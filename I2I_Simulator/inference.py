"""inference.py — image-to-image 실행: 연기 이미지 → 화염 합성 이미지.

  단일:  python inference.py <입력_이미지_경로> [<출력_이미지_경로>]
  폴더:  python inference.py <입력_폴더> <출력_폴더>          # 모델 1회 로드 후 연속 처리
         python inference.py in_dir/ out_dir/ --independent   # 서로 무관한 이미지들일 때

  예: python inference.py /path/to/smoke.png /path/to/fire_out.png
      python inference.py /data2/captures/ /data2/results/    # 정렬 순서 = 스트림 순서로 처리

폴더 모드 주의: 기본은 '연속 프레임 스트림'으로 간주해 추적·시간앵커 상태를 이어갑니다.
서로 무관한 스틸 이미지들이면 --independent 를 붙이세요(이미지마다 상태 초기화 — 관성
게이트 오작동 방지). 모델 로드는 어느 모드든 1회입니다.
"""
import argparse, time
from pathlib import Path
import cv2
from model import RTLightFire

EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def reset_state(eng):
    """무관한 이미지 간 상태 초기화 (model.py의 인과 상태 블록과 동일 항목)"""
    eng.t = 0; eng.prev_box = None; eng.bbox_ema = None; eng.turb = None
    eng.prev_lat = None; eng.key_ema = None; eng.cent_ema = None; eng.area_ema = None
    eng.prev_mask = None; eng.rejects = 0; eng.base_y = None; eng.base_conf = 0
    eng.soft_mask = None
    eng.prev_gray = None; eng.ego_A = None; eng.ego_fail = 0   # 10-29 카메라 이동 보정 상태


def main():
    ap = argparse.ArgumentParser(description="light_fire image-to-image")
    ap.add_argument("input", metavar="INPUT_PATH",
                    help="입력 이미지 경로 또는 폴더 (예: /path/to/smoke.png, /data2/captures/)")
    ap.add_argument("output", nargs="?", default="out.png", metavar="OUTPUT_PATH",
                    help="출력 이미지 경로 또는 폴더 (기본 ./out.png)")
    ap.add_argument("--independent", action="store_true",
                    help="폴더 모드에서 이미지마다 상태 초기화 (무관한 스틸 이미지용)")
    ap.add_argument("--prompt", default="a photo of a big fire flame")
    ap.add_argument("--strength", type=float, default=0.65)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()

    inp = Path(a.input)
    eng = RTLightFire(device=a.device, prompt=a.prompt, strength=a.strength, steps=a.steps)

    if inp.is_dir():                                       # ---- 폴더 모드: 1회 로드, 연속 처리 ----
        files = sorted(p for p in inp.iterdir() if p.suffix.lower() in EXTS)
        if not files:
            ap.error(f"이미지 없음: {inp}")
        outdir = Path(a.output if a.output != "out.png" else "out")
        outdir.mkdir(parents=True, exist_ok=True)
        t0 = time.perf_counter()
        for p in files:
            img = cv2.imread(str(p))
            if img is None:
                print(f"skip (읽기 실패): {p.name}"); continue
            if a.independent:
                reset_state(eng)
            t1 = time.perf_counter()
            cv2.imwrite(str(outdir / p.name), eng.step(img))
            print(f"{p.name} -> {outdir/p.name}  ({1000*(time.perf_counter()-t1):.0f} ms)", flush=True)
        n = len(files)
        print(f"done: {n}장, 총 {time.perf_counter()-t0:.1f}s (장당 평균 {(time.perf_counter()-t0)/n:.2f}s)")
    else:                                                  # ---- 단일 이미지 ----
        img = cv2.imread(str(inp))
        if img is None:
            ap.error(f"이미지를 읽을 수 없음: {inp}")
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        t1 = time.perf_counter()
        cv2.imwrite(a.output, eng.step(img))
        print(f"{inp} -> {a.output}  ({1000*(time.perf_counter()-t1):.0f} ms)")


if __name__ == "__main__":
    main()
