#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

# ====== 전역 설정(기본값) ======
MODEL_PREFIX = "particle_"
POS_X, POS_Y, POS_Z = 0, 0, -10      # 스폰 좌표
MAX_WORKERS = os.cpu_count() or 4    # 시스템 CPU 코어 수 기반 스레드 개수
RETRIES = 2                          # 실패 재시도 횟수
# ========================================

def parse_args():
    parser = argparse.ArgumentParser(description="Gazebo 파티클 스폰 스크립트")
    parser.add_argument(
        "-n", "--num-models",
        type=int, required=True,
        help="생성할 파티클(모델) 개수"
    )
    parser.add_argument(
        "-f", "--sdf-file",
        type=str, required=True,
        help="사용할 SDF 파일 경로"
    )
    return parser.parse_args()

def check_prerequisites(sdf_file: str) -> None:
    """rosrun, sdf 파일 경로 확인."""
    if shutil.which("rosrun") is None:
        print("[에러] 'rosrun'을 찾을 수 없습니다. ROS 환경이 올바르게 설정되었는지 확인하세요 (PATH/ROS setup.bash).", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(sdf_file):
        print(f"[에러] SDF 파일을 찾을 수 없습니다: {sdf_file}", file=sys.stderr)
        sys.exit(1)

def build_cmd(i: int, sdf_file: str) -> List[str]:
    """spawn_model 명령어 구성."""
    model_name = f"{MODEL_PREFIX}{i}"
    return [
        "rosrun", "gazebo_ros", "spawn_model",
        "-file", sdf_file,
        "-sdf",
        "-model", model_name,
        "-x", str(POS_X), "-y", str(POS_Y), "-z", str(POS_Z),
    ]

def run_once(cmd: List[str]) -> subprocess.CompletedProcess:
    """한 번 실행."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def spawn_with_retries(i: int, sdf_file: str) -> str:
    """스폰 실행 + 재시도 로직."""
    cmd = build_cmd(i, sdf_file)
    attempt = 0
    while True:
        proc = run_once(cmd)
        if proc.returncode == 0:
            return f"[OK] {MODEL_PREFIX}{i}"
        attempt += 1
        if attempt > RETRIES:
            # 실패 로그를 간략히 리턴(표준에러 앞부분만)
            err_snip = (proc.stderr or "").strip().splitlines()
            err_snip = err_snip[:3] if err_snip else ["(no stderr)"]
            return f"[FAIL] {MODEL_PREFIX}{i} (code {proc.returncode}) -> " + " | ".join(err_snip)
        # 지수 백오프
        time.sleep(min(2 ** attempt, 5))

def main():
    args = parse_args()
    num_models = args.num_models
    sdf_file = args.sdf_file

    check_prerequisites(sdf_file)
    print(f"총 {num_models}개의 모델을 병렬로 스폰합니다. (스레드: {MAX_WORKERS})")
    start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(spawn_with_retries, i, sdf_file) for i in range(1, num_models + 1)]
        done_cnt = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done_cnt += 1
            # 간단 진행상황 표시
            if done_cnt % 10 == 0 or done_cnt == num_models:
                elapsed = time.time() - start
                print(f"[진행] {done_cnt}/{num_models} 완료 (경과 {elapsed:.1f}s)")

    # 요약
    ok = sum(1 for r in results if r.startswith("[OK]"))
    fail = num_models - ok
    print("\n===== 결과 요약 =====")
    print(f"성공: {ok} / 실패: {fail}")
    if fail:
        print("실패 항목:")
        for r in results:
            if r.startswith("[FAIL]"):
                print("  " + r)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.", file=sys.stderr)
        sys.exit(130)

