# JnP 1.0 강화학습 지원 — 지금까지 된 것(2026-10-31)

JnP 가 강화학습 정책을 품는 방식: 정책은 "각 로봇의 동작(어디로 갈지 + 무엇을 알려 줄지 + 무엇을 받을지)" 을 정하는 파이썬 클래스 하나이고, 가입·편성·작업 트리·스킬 실행·상태 보고·정보 교환·통신량 세기는 JnP 가 한다.

| 모듈 | 역할 |
|---|---|
| scripts/jnp_rl_api.py | 정책 계약 v0.2: Observation(자기 위치·자기 지도·프론티어 후보·훑은 곳·역할·받은 정보·제공/구독 상태), Action(후보 번호·제공 켜고 끄기·구독 집합), Policy |
| scripts/jnp_rl_loader.py | 정책 파일 읽기(`파일.py:클래스`), api_version 확인 |
| scripts/jnp_rl_registry.py | 제공 항목 목록(pose·local_map·goal·done_area·detections·assignment), 설명 v1.1 `<provides>` 만들기·읽기 |
| scripts/jnp_rl_link.py | 제공 채널 발행, 설명 조회 → 광고 확인 → 구독, 받은 바이트 기록, pose 발행기 |
| scripts/jnp_rl_meter.py | 통신 기록표(받는 쪽이 한 줄씩: 종류·항목·보낸 이·받은 이·바이트) |
| scripts/jnp_rl_frontier.py | 자기 지도에서 프론티어 후보 찾기(RRT 스택 불필요) |
| scripts/jnp_rl_runtime.py | 로봇 쪽 결정 자리: 3초마다 정책 호출, 도착·정체 판정, 제공·구독 적용. 수색 모드(경유점·탐지·보고) 포함 |

켜는 법(에이전트): `~jnp_policy:=/path/my_policy.py:MyPolicy`, 선택 `~jnp_comm_log:=/tmp/jnp_comm_<로봇>.jsonl`, `~jnp_provides:=pose`(정책 없이 제공만 켤 때). 비워 두면 모두 이전과 같다.
리더 프록시(중앙에서 결정): 그룹 노드 `~jnp_policy`. 프록시는 모든 로봇 정보를 받으므로 통신량이 늘어 자율도가 낮아진다.

G3(2026-10-31): 그룹 노드 `~jnp_distributed:=true` 로 분산 모드(RRT 스택·중앙 피더·상시 병합 끔, 로봇들의 explore 완료로 미션 종료), 제공 항목 custom(제작자 정의 JSON)·done(끝 보고)·merged_map(결과물 지도) 추가, Action.done/custom_payload/merged_map. 예제·기준은 지금의 map merge 버전(파라미터 없음) 그대로. 참가자 안내: leaderboard/docs/PARTICIPANT_GUIDE_ko.md.

아직 없는 것: 받은 정보만 보게 막는 장치(병합 지도 토픽·동료 TF 직접 읽기 차단), 리더 프록시의 수신 통신량 기록, 자동 채점 실행(launch·격리), 채점 시각(t0) 수정, 정답 기반 탐지기의 map=world 좌표 가정 검증(TB3 스폰 오프셋).

- [2026-11-01] 정책이 `Action.provide` 로 켠 항목은 런타임이 에이전트에 알려 설명 `<provides>` 에도 광고된다(팀원이 "광고하지 않음"으로 구독 못 하는 일 방지). 팀원 이름은 내 이름공간(예: `etri/`)을 붙여 노드 이름으로 바꿔 설명 조회·구독한다.
- [2026-11-01, R4] 받은 정보의 뜻을 그리드 학습 환경과 맞췄다: 구독을 끊으면 보관본(`received`)도 지운다; 목표에 도착·포기하면 goal 채널에 frame_id 'none' 의 '목표 없음' 알림을 내고 받는 쪽은 보관본을 지운다; `Observation.received_t`('에이전트/항목' → 마지막 수신 sim 시각)를 추가(규약 0.2 에 더한 필드); yaw≠0 인 지도는 받지 않는다. 통신 기록표는 줄마다 `run_id`(`~jnp_run_id`)와 `t_sim` 을 적고 `aggregate(paths, t0, t1, run_id)` 로 회차 구간만 합친다. 그룹은 분산 모드에서 `/jnp/explore_roles`(latched JSON {host, explorers})를 내고 에이전트가 `state['role']` 로 정책에 넘긴다. 정책 런타임이 목표를 버리면 에이전트가 move_base 목표를 바로 취소한다.
- [2026-11-01, R5] 회차 시계: 채점 환경이 `/lb/episode`(run_id·t0=태스크 발행 sim 초·T)를 놓으면 런타임이 그 t0 로 `Observation.t` 를 맞추고 `t_limit` 을 준다(없으면 첫 관측 기준, 표시).
  지도 공통 검사 `jnp_rl_gridcheck.check_grid`(좌표계 이름 'map'+별칭 `~jnp_frame_aliases`, 2D 항등 자세, 유한 기하, 셀 값, 크기 상한)를 자기 지도·받은 지도에 적용하고,
  자기 지도는 받은 좌표계 이름 그대로 다시 낸다(재표기 없음). 수신 보관(`received`·`received_meta`(stamp·frame)·`received_t`)은 잠금 아래 payload 먼저·시각 마지막으로 갱신하고 관측은 한 번에 복사한다.
  `done` 알림에 마지막으로 낸 local_map 의 stamp(`map_stamp`)를 싣는다. 기록표(`jnp_rl_meter`)는 start/alive(10 s)/end 생존 줄을 적고 `aggregate(..., receivers, t_end)` 가 완전성을 확인한다.
  host 가 merged_map 을 내면 `/jnp/explore_result`(latched JSON)로 그룹에 알리고, 분산 모드 그룹은 이 알림이 있을 때만 병합·송신 가상 task 를 완료로 표시한다(없으면 no_submission).
