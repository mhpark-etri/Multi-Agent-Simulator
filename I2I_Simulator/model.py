"""model.py — RTLightFire: 실시간 smoke→fire 합성 모델 (이미지 in → 이미지 out, 인과적).

구성 (4단계, 모두 스트리밍/인과 처리 — 미래 프레임 불필요):
  [1] 연기 탐지   : Grounding-DINO(첫 프레임 시드 1회) → SAM2.1-tiny 이미지 예측기
                    (이전 프레임 마스크의 bbox를 프롬프트로 자기추적)
  [2] 기저부 마스크: 열(column)별 연기 최하단 등고선 y_b(x) → 등고선 밀착 시트 밴드
                    + soft primer(흐릿한 발광, 위치/크기 힌트)
  [3] 화염 생성   : SD1.5+Hyper-SD LoRA(fuse됨) masked SDEdit — 4 LCM 스텝,
                    마스크 밖 latent는 매 스텝 원본으로 재고정, 이전 프레임 latent 앵커
  [4] 블렌드     : luma-key 발광 합성 + smoke veil + fire-lit smoke + glow (크롭 ROI에서만)

가중치: ./weights/ (sd15_hyper_fused, gdino_tiny, sam2.1_hiera_tiny.pt) — 전부 로컬, 네트워크 불필요.
"""
import os, sys
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")          # 완전 오프라인: 어떤 네트워크 접근도 금지
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import numpy as np, cv2, torch
from PIL import Image

PKG = Path(__file__).resolve().parent
W = PKG / "weights"
# sam2 코드는 패키지에 내장(third_party/sam2). 외부 레포를 쓰려면 SAM2_REPO 환경변수로 재지정
_BUNDLED_SAM2 = PKG / "third_party" / "sam2"
SAM2_REPO = os.environ.get("SAM2_REPO", str(_BUNDLED_SAM2) if _BUNDLED_SAM2.exists() else "/data2/gahyeon/sam2")
sys.path.insert(0, SAM2_REPO)
from sam2.build_sam import build_sam2                       # noqa: E402
from sam2.sam2_image_predictor import SAM2ImagePredictor    # noqa: E402
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor  # noqa: E402
from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler           # noqa: E402

SMOKE_PROMPT = "smoke . dark smoke . smoke plume . cloud of smoke ."


def _fire_palette():
    """0..255 강도 → BGR 불색(검정→진홍→주황→노랑→백색) 룩업테이블. primer 채색용."""
    lut = np.zeros((256, 3), np.uint8)
    for i in range(256):
        t = i / 255.0
        if t < 0.25: c = (0, 0, int(t / 0.25 * 180))
        elif t < 0.5: c = (0, int((t - 0.25) / 0.25 * 120), 200)
        elif t < 0.8: c = (int((t - 0.5) / 0.3 * 80), int(120 + (t - 0.5) / 0.3 * 135), 255)
        else: c = (int(80 + (t - 0.8) / 0.2 * 175), 255, 255)
        lut[i] = c
    return lut


class RTLightFire:
    """스트리밍 smoke→fire. 카메라 스트림당 인스턴스 1개를 만들고 step()을 프레임마다 호출.

    사용자 검증 기본값: seat_frac 0.55(화염 최대 높이), below 0.05(기저 미세 패딩 — 0.12+는
    불-연기 분리), primer_alpha 0.8(화염 부피), strength 0.65(프레임 안정성),
    veil 0.45(화염 상부를 연기가 덮음), key_gain 1.3(화염 가장자리 노출),
    t_anchor 0.35(이전 프레임 latent 혼합 — 프레임 품질 편차 완화, 비용 0).
    기저부 타겟팅: SAM2 soft-logit 등고선 + 바닥 기억(base_y, 신뢰도 15프레임 후 완전 접지).
    오검출 방어: 시드 점수 0.30 게이트 + 연기다움(무채색) 검사 + centroid/면적 관성 게이트.
    """

    def __init__(self, device="cuda", prompt="a photo of a big fire flame",
                 strength=0.65, steps=4, seat_frac=0.55, below=0.05, primer_alpha=0.8,
                 veil=0.45, key_gain=1.3, t_anchor=0.35, reseed_every=90):
        self.dev = device
        self.dt = torch.float16 if device == "cuda" else torch.float32
        self.strength, self.steps = strength, steps
        self.seat_frac, self.below, self.primer_alpha = seat_frac, below, primer_alpha
        self.veil, self.key_gain, self.t_anchor = veil, key_gain, t_anchor
        self.reseed_every = reseed_every                      # N프레임마다 DINO로 재시드(드리프트 방지)
        # --- [1] 탐지기 로드: DINO(시드용) + SAM2-tiny 이미지 예측기 ---
        self.dproc = AutoProcessor.from_pretrained(str(W / "gdino_tiny"))
        self.dino = AutoModelForZeroShotObjectDetection.from_pretrained(str(W / "gdino_tiny")).to(device).eval()
        self.sam = SAM2ImagePredictor(build_sam2("configs/sam2.1/sam2.1_hiera_t.yaml",
                                                 str(W / "sam2.1_hiera_tiny.pt"), device=device))
        # --- [3] 생성기 로드: LoRA가 이미 fuse된 SD1.5 (단일 폴더) ---
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            str(W / "sd15_hyper_fused"), torch_dtype=self.dt,
            safety_checker=None, requires_safety_checker=False).to(device)
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
        pipe.set_progress_bar_config(disable=True)
        self.vae, self.unet, self.sched = pipe.vae, pipe.unet, pipe.scheduler
        self.emb = pipe.encode_prompt(prompt, device, 1, False)[0]   # 프롬프트 임베딩 1회 캐시
        self.lut = _fire_palette()
        # --- 인과적 상태(스트림 간 유지) ---
        self.t = 0                # 프레임 카운터
        self.prev_box = None      # 직전 마스크의 bbox → 다음 프레임 SAM2 프롬프트
        self.bbox_ema = None      # 크롭 박스 안정화(EMA)
        self.turb = None          # primer 난류(위로 advect → 자연스러운 일렁임)
        self.prev_lat = None      # 직전 프레임 출력 latent → 시간적 앵커
        self.key_ema = None       # luma-key 알파의 시간 EMA(깜빡임 완화)
        self.cent_ema = None      # 승인된 연기 centroid의 관성(EMA) — 오검출 게이트 기준
        self.area_ema = None      # 승인된 연기 면적의 관성
        self.prev_mask = None     # 직전 승인 마스크(기각 프레임에서 재사용)
        self.rejects = 0          # 연속 기각 횟수(5회면 DINO 재시드)
        self.base_y = None        # 연기 바닥의 최저점 기억(풀프레임 y) — 불 발원점은 떠오르지 않음
        self.base_conf = 0        # 바닥 기억 신뢰도: 연기가 기억 바닥에 닿은 프레임 누적 수
        self.soft_mask = None     # SAM2 soft(logit>-2.5) 마스크 — 얇은 하단 연기까지, 기저 추정 전용

    # ---------------- [1] 연기 마스크 (인과 추적) ----------------
    def _mask(self, bgr):
        """DINO 시드(첫 프레임/재시드 주기) → SAM2 이미지 예측 → 최대 연결성분만 유지.
        이전 마스크의 15% 패딩 bbox를 다음 프레임 프롬프트로 사용(자기추적)."""
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        H, Wd = bgr.shape[:2]
        need_seed = self.prev_box is None or self.t % self.reseed_every == 0 or self.rejects >= 5
        if self.prev_box is None and self.t % 5 != 1:
            return None                                    # 연기 미발견 상태: 5프레임마다만 재탐색(비용 절약)
        if need_seed:
            pil = Image.fromarray(rgb)
            inp = self.dproc(images=pil, text=SMOKE_PROMPT, return_tensors="pt").to(self.dev)
            with torch.no_grad(): o = self.dino(**inp)
            r = self.dproc.post_process_grounded_object_detection(
                o, inp.input_ids, threshold=0.25, text_threshold=0.20, target_sizes=[pil.size[::-1]])[0]
            if len(r["boxes"]) == 0: return self.prev_mask
            bxs = np.array([b.tolist() for b in r["boxes"]], np.float32)
            scs = r["scores"].cpu().numpy()
            if self.cent_ema is not None and len(bxs) > 1:
                # 관성: 기억된 centroid에 가장 가까운 박스 선택(최고 점수 아님)
                cents = np.stack([(bxs[:, 0] + bxs[:, 2]) / 2, (bxs[:, 1] + bxs[:, 3]) / 2], 1)
                cand_boxes = [bxs[int(np.argmin(np.linalg.norm(cents - self.cent_ema, axis=1)))]]
            else:
                bi = int(np.argmax(scs))                           # 기억 없음: 최고 점수 박스
                if scs[bi] < 0.30: return self.prev_mask           # 저신뢰 → 연기 없음
                cand_boxes = [bxs[bi]]
            self.rejects = 0
        else:
            cand_boxes = [self.prev_box]
        with torch.no_grad():
            self.sam.set_image(rgb)
        m = None
        for cb in cand_boxes:                              # 후보 박스 순차 시도(첫 통과 채택)
            with torch.no_grad():
                mk, _, _ = self.sam.predict(box=cb[None], multimask_output=False, return_logits=True)
            for logits in [mk[0]]:
                mh = (logits > 0).astype(np.uint8) * 255
                n, lab, stats, _ = cv2.connectedComponentsWithStats(mh, connectivity=8)
                if n <= 1: continue
                big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
                if stats[big, cv2.CC_STAT_AREA] < 400: continue        # 너무 작음
                mh = np.where(lab == big, 255, 0).astype(np.uint8)
                ys, xs = np.where(mh > 0)
                pix = bgr[ys, xs].astype(np.int16)                     # 연기다움: 무채색 회색만
                chroma = float((pix.max(1) - pix.min(1)).mean())
                vmean = float(pix.mean())
                if chroma > 32 or not (35 < vmean < 215): continue     # 다음 후보로
                m = mh
                self.soft_mask = (logits > -2.5).astype(np.uint8) * 255
                break
            if m is not None: break
        if m is None:
            self.rejects += 1
            return self.prev_mask                          # 모든 후보 실패 → 기억 오염 방지
        ys, xs = np.where(m > 0)
        cent = np.array([xs.mean(), ys.mean()], np.float32); area = float(len(xs))
        # --- centroid 관성 게이트: 기억 대비 위치 급변/면적 급변이면 기각하고 직전 마스크 재사용 ---
        if self.cent_ema is not None:
            jump = float(np.linalg.norm(cent - self.cent_ema))
            r_plume = max(30.0, np.sqrt(self.area_ema / np.pi))          # 기억된 플룸 반경
            if jump > 0.9 * r_plume or area > 2.5 * self.area_ema or area < 0.3 * self.area_ema:
                self.rejects += 1
                return self.prev_mask                                     # 이상 검출 → 관성 유지
        self.rejects = 0
        self.cent_ema = cent if self.cent_ema is None else 0.7 * self.cent_ema + 0.3 * cent
        self.area_ema = area if self.area_ema is None else 0.7 * self.area_ema + 0.3 * area
        self.prev_mask = m
        px, py = 0.15 * (xs.max() - xs.min() + 1), 0.15 * (ys.max() - ys.min() + 1)
        self.prev_box = np.array([max(0, xs.min() - px), max(0, ys.min() - py),
                                  min(Wd, xs.max() + px), min(H, ys.max() + py)], np.float32)
        return m

    # ---------------- 메인: 프레임 1장 처리 ----------------
    @torch.no_grad()
    def step(self, bgr):
        """BGR uint8 이미지 → 화염 합성된 BGR uint8 (동일 해상도). 연기 없으면 원본 반환."""
        self.t += 1
        H, Wd = bgr.shape[:2]
        m = self._mask(bgr)
        if m is None: return bgr
        # --- 크롭 박스: 마스크 bbox의 정사각형 확장(0.7×장변), EMA로 흔들림 억제 ---
        ys, xs = np.where(m > 0)
        box = np.array([xs.min(), xs.max(), ys.min(), ys.max()], np.float32)
        self.bbox_ema = box if self.bbox_ema is None else 0.7 * self.bbox_ema + 0.3 * box
        x0, x1, y0, y1 = self.bbox_ema.astype(int)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        hw = int(max(x1 - x0, y1 - y0) * 0.7)
        cy0, cy1 = max(0, cy - hw), min(H, cy + hw)
        cx0, cx1 = max(0, cx - hw), min(Wd, cx + hw)
        crop = cv2.resize(bgr[cy0:cy1, cx0:cx1], (512, 512))
        mc = cv2.resize(m[cy0:cy1, cx0:cx1], (512, 512))
        occ = mc > 80
        if occ.sum() < 30: return bgr
        # soft 마스크(얇은 하단 연기 포함) — 기저 등고선 계산에만 사용
        msoft = cv2.resize(self.soft_mask[cy0:cy1, cx0:cx1], (512, 512)) if self.soft_mask is not None else mc
        osoft = np.maximum(msoft, mc) > 80
        # --- [2] 기저 등고선 → 시트 마스크(latent 64) + soft primer ---
        ysm, _ = np.where(occ); bh = max(8, ysm.max() - ysm.min())     # 플룸 높이(hard 기준)
        valid = occ.any(axis=0)                                        # 연기가 있는 열(hard 기준)
        yb_hard = (511 - np.argmax(occ[::-1, :], axis=0)).astype(np.float32)
        yb_hard[~valid] = np.median(yb_hard[valid])
        yb = (511 - np.argmax(osoft[::-1, :], axis=0)).astype(np.float32)  # SOFT: 얇은 하단까지
        vs = osoft.any(axis=0)
        yb[~vs] = np.median(yb[vs])
        yb = np.minimum(yb, yb_hard + 0.15 * bh)          # CAP: soft 확장은 hard 아래 0.15bh까지만
        yb = np.where(valid, yb, yb_hard)                  # hard 연기 없는 열은 확장 금지(수평 번짐 방지)
        yb = cv2.GaussianBlur(yb.reshape(1, -1), (0, 0), sigmaX=10).ravel()  # 등고선 평활
        # --- 바닥 기억: 연기 퍼프가 떠올라도 화염 발원점은 기억된 최저점(바닥)에 고정 ---
        sc_y = (cy1 - cy0) / 512.0
        y1_full = cy0 + float(yb.max()) * sc_y                         # 현재 연기 바닥(풀프레임 y)
        if self.base_y is None:
            self.base_y = y1_full
        elif y1_full > self.base_y:                                    # 더 낮은 바닥 발견 → 빠르게 채택
            self.base_y = 0.5 * self.base_y + 0.5 * y1_full
        else:                                                          # 연기가 떠오름 → 기억은 이주 천천히만 상승
            self.base_y = max(y1_full, self.base_y - 0.01 * bh * sc_y)
        tgt = (self.base_y - cy0) / sc_y                               # 기억된 바닥(크롭 좌표)
        raw_gap = max(0.0, tgt - yb.max())
        if raw_gap < 0.08 * bh:
            self.base_conf = min(self.base_conf + 1, 30)               # 연기가 바닥에 닿음 → 신뢰 누적
        cap = 0.15 * bh if self.base_conf < 15 else 2.0 * bh           # 검증된 바닥이면 상한 해제(완전 접지)
        shift = min(raw_gap, cap)
        if shift > 2:
            yb = np.clip(yb + shift, 0, 511)
        yy = np.arange(512, dtype=np.float32)[:, None]
        rel = yb[None, :] - yy                                         # 등고선 위 높이(px)
        seat_h, below = self.seat_frac * bh, self.below * bh
        band = ((rel >= -below) & (rel <= seat_h)).astype(np.uint8) * 255   # 기저 밀착 밴드
        # 하부(등고선 근처)는 연기 유무와 무관하게 허용(끌어내린 구간), 상부는 연기와 교집합
        md_low = (band * (rel <= 0.15 * bh)).astype(np.uint8)
        md_up = cv2.bitwise_and(cv2.dilate(mc, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))), band)
        md = np.maximum(md_low, md_up)
        md = np.where(valid[None, :], md, 0).astype(np.uint8)
        m64 = np.clip(cv2.GaussianBlur(cv2.resize(md, (64, 64)).astype(np.float32) / 255, (0, 0), 1.2), 0, 1)
        self.dbg = dict(box=(cy0, cy1, cx0, cx1), mc=mc, msoft=msoft, yb=yb.copy(), md=md, bh=bh)  # 시각화용
        # primer: 등고선에서 위로 선형 감쇠하는 발광 × 난류. σ10 블러 → 실루엣이 결과에 안 남음
        prof = np.clip(1.0 - rel / max(seat_h, 1), 0, 1) * (rel >= -below) * (rel <= seat_h)
        n = cv2.GaussianBlur(np.random.default_rng(self.t).random((512, 512)).astype(np.float32), (0, 0), 12)
        self.turb = n if self.turb is None else np.roll(self.turb, -10, 0) * 0.7 + 0.3 * n
        root_boost = 1.0 + 0.5 * ((rel >= -below) & (rel <= 0.12 * bh))      # 뿌리 구간 primer 강화
        inten = np.clip(prof * root_boost * (0.5 + 0.5 * self.turb) * np.maximum(mc.astype(np.float32) / 255, 0.25), 0, 1)
        inten = cv2.GaussianBlur(inten * valid[None, :], (0, 0), 10)
        fire_pr = self.lut[(np.clip(inten * 1.2, 0, 1) * 255).astype(np.uint8)].astype(np.float32)
        alp = cv2.GaussianBlur(inten, (0, 0), 8)[..., None] * self.primer_alpha
        primed = np.clip(crop * (1 - alp) + fire_pr * alp, 0, 255).astype(np.uint8)
        # --- [3] masked SDEdit: primed에서 시작, 마스크 밖은 매 스텝 '깨끗한 원본'으로 재고정 ---
        def enc(img):
            x = torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).permute(2, 0, 1)[None].to(self.dev, self.dt) / 127.5 - 1
            return self.vae.encode(x).latent_dist.sample(torch.Generator(self.dev).manual_seed(42)) * self.vae.config.scaling_factor
        lat_init, lat0 = enc(primed), enc(crop)                        # init=primed / 앵커=clean
        mt = torch.from_numpy(m64).to(self.dev, self.dt)[None, None]
        if self.prev_lat is not None and self.t_anchor > 0:            # 시간적 앵커(마스크 내부만)
            lat_init = lat_init + mt * self.t_anchor * (self.prev_lat - lat_init)
        self.sched.set_timesteps(self.steps, device=self.dev)
        ts = self.sched.timesteps[min(int(self.steps * (1 - self.strength)), self.steps - 1):]
        g = torch.Generator(self.dev).manual_seed(42)
        noise = torch.randn(lat0.shape, generator=g, device=self.dev, dtype=lat0.dtype)
        lat = self.sched.add_noise(lat_init, noise, ts[:1])
        for i, tt in enumerate(ts):
            eps = self.unet(lat, tt, encoder_hidden_states=self.emb).sample
            lat = self.sched.step(eps, tt, lat).prev_sample
            if hasattr(self.sched, "_step_index"): self.sched._step_index = None
            lat = mt * lat + (1 - mt) * (self.sched.add_noise(lat0, noise, ts[i + 1:i + 2]) if i + 1 < len(ts) else lat0)
        self.prev_lat = lat.detach()
        gen = self.vae.decode(lat / self.vae.config.scaling_factor).sample
        gen = cv2.cvtColor(((gen.clamp(-1, 1) + 1) * 127.5).byte()[0].permute(1, 2, 0).cpu().numpy(),
                           cv2.COLOR_RGB2BGR).astype(np.float32)
        # --- [4] 블렌드: luma-key 발광 합성 (사용자 선호 확정 룩, 2026-08-24 롤백) ---
        warmth = np.clip(gen[..., 2] - gen[..., 0], 0, 255)
        lum = cv2.cvtColor(gen.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        key = np.clip((lum - 80 / self.key_gain) / (120 / self.key_gain), 0, 1) \
            * np.clip(warmth / (50 / self.key_gain), 0, 1)
        key = cv2.GaussianBlur(np.clip(key, 0, 1) ** 0.9, (0, 0), 2)
        self.key_ema = key if self.key_ema is None else 0.7 * key + 0.3 * self.key_ema
        al = np.clip(self.key_ema * 1.25, 0, 1)
        if self.veil > 0:                                              # 화염 상부를 원본 연기가 덮음
            relh = rel / bh
            v = np.clip((relh - 0.28) / 0.35, 0, 1) * occ * self.veil
            al = al * (1 - cv2.GaussianBlur(v.astype(np.float32), (0, 0), 7))
        al = al[..., None]
        base = crop.astype(np.float32)
        # 크롭 경계 feather (조명 효과 이음선 방지)
        edge = np.ones((512, 512), np.float32); r = 36
        ramp = np.linspace(0, 1, r, dtype=np.float32)
        edge[:r, :] *= ramp[:, None]; edge[-r:, :] *= ramp[::-1][:, None]
        edge[:, :r] *= ramp[None, :]; edge[:, -r:] *= ramp[::-1][None, :]
        zone = cv2.GaussianBlur((self.key_ema > 0.08).astype(np.float32), (0, 0), 9)
        base *= (1 - 0.13 * cv2.GaussianBlur(zone, (0, 0), 31) * edge)[..., None]   # 국소 암화
        gl_big = cv2.GaussianBlur(self.key_ema, (0, 0), 31)
        hfall = np.clip((yy - (yb[None, :].mean() - 0.9 * bh)) / (0.9 * bh), 0, 1)
        lit = gl_big * occ.astype(np.float32) * hfall * 1.4 * edge     # fire-lit smoke
        base[..., 2] = np.clip(base[..., 2] + lit * 95, 0, 255)
        base[..., 1] = np.clip(base[..., 1] + lit * 40, 0, 255)
        base[..., 0] = np.clip(base[..., 0] * (1 - 0.15 * lit), 0, 255)
        gl = cv2.GaussianBlur(self.key_ema, (0, 0), 15)                # 주변 glow
        base[..., 2] = np.clip(base[..., 2] + gl * 55 * edge, 0, 255)
        base[..., 1] = np.clip(base[..., 1] + gl * 25 * edge, 0, 255)
        comp = np.clip(base * (1 - al) + gen * al, 0, 255).astype(np.uint8)
        out = bgr.copy()
        out[cy0:cy1, cx0:cx1] = cv2.resize(comp, (cx1 - cx0, cy1 - cy0))
        return out
