# third_party — 수정본 ROS 패키지

이 디렉토리의 패키지들은 **원저작자의 코드를 수정한 포크**입니다. 각 패키지의
원본 라이선스가 그대로 적용되며(이 저장소의 Apache-2.0 이 아님), 원본 LICENSE
파일을 함께 담았습니다. 수정 내역은 아래에 요약합니다.

## rrt_exploration (MIT) — 원저작자 Hassan Umari
원본: https://github.com/hasauino/rrt_exploration · 라이선스: `rrt_exploration/LICENSE.md`

**MAS 개정판이 사용하는 파일만 담았습니다.** 이 포크의 원 개발 트리에는 다른
연구 과제(재난 대처, 오더 피킹 등)에서 쓰는 스크립트가 함께 있었으나, 이번
릴리스 범위가 아니므로 제외했습니다. 담은 구성:
`scripts/{boundary,filter,frontier_relay,functions}.py`, `src/*.cpp`(RRT 검출기),
`include/`, `msg/PointArray.msg`, `CMakeLists.txt`, `package.xml`, `LICENSE.md`.

이 저장소에서의 수정:
- `scripts/filter.py`
  - `~use_global_merged_map` 추가 — 프런티어 정보이득을 **병합 지도** 기준으로 판정.
    (기본값 False 인 원본 동작에서는 `map_topic` 을 로봇별로 풀어 로컬 지도로 판정하므로,
     한 로봇만 탐사한 영역의 프런티어가 영영 삭제되지 않았다.)
  - `~min_info_gain_keep` — 삭제 임계값 파라미터화(원본 하드코딩 0.2)
  - `~snap_to_free` — 후보를 관측된 free 셀로 스냅, 벽 밖 후보 폐기
  - `~reject_corner_frontiers` 및 코너/도달불가 후보 거부 로직
  - `~costmap_clearing_mode` — 로봇별 costmap 검증 방식 선택
- `scripts/functions.py` — 프런티어 판정 헬퍼 추가(코너 프런티어 판정,
  로봇별 costmap 검증, 지도 셀 의미 함수). 배정기(assigner) 전용 클래스는
  MAS 가 쓰지 않아 제외(배정은 JnP 스케줄러가 담당).

## map_merge (BSD-3-Clause) — 원저작자 Zhi Yan, Jiri Horner
원본: https://github.com/hrnr/m-explore (noetic 브랜치) · 라이선스: `map_merge/LICENSE`

**이 패키지는 수정하지 않았습니다.** 상류 소스를 그대로 담았습니다(실측: 다른
사본과 바이트 동일, 우리가 더한 것은 LICENSE 파일뿐).

담는 이유는 **버전** 때문입니다:
- apt 배포판: `ros-noetic-multirobot-map-merge 2.1.4-1focal` — 다중 로봇 병합
  지도가 어긋나는 문제가 있었습니다.
- 여기 담은 소스: **2.1.5** — 정렬 문제가 해결된 판.
apt 패키지를 설치해 쓰면 지도 병합이 틀어지므로, 소스로 빌드해 오버레이합니다.
