# RTLightFire — 실시간 smoke→fire 합성 패키지

GazeboSim에서 실시간으로 들어오는 **이미지 1장**을 받아 연기 기저부에 사실적인 대형 화염을
합성해 **이미지 1장**으로 돌려주는 스트리밍 모델. 인과적(causal) 처리만 사용 — 미래 프레임 불필요.

```
light_fire_pkg/
├── model.py          # RTLightFire 클래스 (탐지→기저부 마스크→생성→블렌드)
├── inference.py      # image-to-image 실행 (입력 이미지 → 출력 이미지)
├── requirements.txt
├── README.md         # (이 파일) 환경 설정 + 사용법
├── CODE_GUIDE.md     # 코드 블록별 상세 설명
├── third_party/sam2/ # SAM2 코드 내장 (5 MB) — 별도 클론/설치 불필요
└── weights/          # 모든 가중치 로컬 포함 (~2.8 GB, 네트워크 불필요)
    ├── sd15_hyper_fused/       # SD1.5 + Hyper-SD15 LoRA가 fuse된 diffusers 폴더 (2.0 GB)
    ├── gdino_tiny/             # Grounding-DINO-tiny (0.66 GB, 첫 프레임 시드용)
    └── sam2.1_hiera_tiny.pt    # SAM2.1-tiny (149 MB, 프레임별 연기 추적)
```

## 1. 환경 설정

```bash
# (a) 새 환경 — SAM2 코드는 이미 third_party/에 내장되어 있어 pip 설치만 하면 끝
conda create -n lightfire python=3.10 -y && conda activate lightfire
pip install -r requirements.txt

# (b) 이 서버의 기존 env 재사용 (설치 불필요)
#     /home/gahyeon/miniconda3/envs/gdino/bin/python 사용, SAM2_REPO=/data2/gahyeon/sam2 (기본값)
```

## 2. 사용법

```bash
PY=/home/gahyeon/miniconda3/envs/gdino/bin/python   # 또는 lightfire env의 python
cd /data2/gahyeon/light_fire_pkg

# 단일 이미지
$PY inference.py /path/to/smoke_frame.png /path/to/fire_out.png            # GPU
$PY inference.py /path/to/smoke_frame.png /path/to/fire_out.png --device cpu

# 폴더 모드: 모델 1회 로드 후 연속 처리 (연속 프레임이면 추적 상태 자동 유지)
$PY inference.py /path/to/frames_dir/ /path/to/out_dir/
$PY inference.py /path/to/stills_dir/ /path/to/out_dir/ --independent      # 무관한 이미지들

# 연속 프레임(GazeboSim 연동)은 파이썬에서 직접
from model import RTLightFire
eng = RTLightFire(device="cuda")      # 스트림당 1개, 로드 ~15초; 상태(추적·앵커) 자동 유지
out_bgr = eng.step(frame_bgr)         # 프레임당 ~0.42초 (A100) / CPU ~8-10초
```

## 3. 성능 (실측, A100-40GB, 1080p 입력)

| 항목 | 값 |
|---|---|
| 프레임당 지연 | **0.42 s** (p95 0.49 s) → 2.4 FPS. `--steps 2` ≈ 0.3 s |
| VRAM | ~6 GB (SAM2 2.5 + SD1.5 3.3) |
| 탐지 구성 | **GDINO-tiny 시드 + SAM2.1-tiny 추적** (확정; YOLO/HSV 대안은 실측 비교 후 기각 — 아카이브 /data2/gahyeon/smoke_yolo/) |
| 가중치 총량 | 2.8 GB (전부 `weights/`, 오프라인 동작) |
| CPU-only (`--device cpu`) | 프레임당 **~8–10 s** — 실측. 완전 오프라인(HF_HUB_OFFLINE 강제), GPU·네트워크 모두 불필요 |

## 4. 핵심 파라미터 (전부 사용자 검증값이 기본)

| 파라미터 | 기본 | 의미 |
|---|---|---|
| `prompt` | "a photo of a big fire flame" | 단순 프롬프트만. 장소·물체 명사는 환각 유발 금지 |
| `strength` | 0.65 | ↑크고 자유로움/프레임 출렁임, ↓primer 실루엣 노출 |
| `seat_frac` | 0.55 | 화염 최대 높이(플룸 높이 비율) |
| `below` | 0.05 | 기저 미세 패딩(확정). 0.12+로 키우면 불이 연기에서 분리돼 보임 |
| `primer_alpha` | 0.8 | 생성 화염 부피 |
| `veil` | 0.45 | 화염 상부를 원본 연기가 덮는 정도(연기 속으로 솟는 불) |
| `key_gain` | 1.3 | 화염 가장자리 노출량(luma-key 완화) |
| `t_anchor` | 0.35 | 이전 프레임 latent 혼합 — I2I 프레임 품질 편차 완화(비용 0) |

## 5. 관련 자료
- 코드 상세: `CODE_GUIDE.md`
- 오프라인 배치판(클립 단위, 3-stage): `/data2/gahyeon/light_fire/`
- CPU 초경량 절차적 실시간판(20 FPS, diffusion 없음): `/data2/gazebosim_data/rt_smoke2fire.py`
