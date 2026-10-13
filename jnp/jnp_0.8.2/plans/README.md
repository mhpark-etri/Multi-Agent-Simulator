# plans/ — 기본 협업 태스크의 작업 분할 계획 (JnP 0.8.2)

| goal (GUI) | 계획 파일 | 바인딩되는 상수 ← payload | 만들어지는 트리 |
|---|---|---|---|
| Relay | `relay.py` | `LEGS` ← `name=x,y,th;…` | 순차: relay1.<r> → relay2.<r> → … (GoTo) |
| Mult-Goal | `multigoal.py` | `ITEMS` ← `goals=G:x,y:count\|…` | 병렬: G[count] → G.itemk (Trip) |
| Avoidance | `avoidance.py` | `FIRST`, `REST` ← `bt=…;routes=…` (ETA 순) | 병렬: cross.<r> = [wait_pass.<prev>(virtual) →] move.<r> (GoTo) |
| MapExplore | `map_explore.py` | `HOST`, `EXPLORERS` ← `robots=…` (병합 호스트 1대) | 병렬: make_maps.<r> = { navigate.<r>[explore.<r>], merge_maps\|send_map.<r> } |
| ObjectSearch | `object_search.py` | `ROBOTS` ← `robots=…` | 병렬: search.<r> = { patrol.<r>, detect.<r> } |

- 형식은 LLM-TDM 계획(`# Task Description / # GENERAL TASK DECOMPOSITION / # CODE`). `# CODE` 는 실행되지 않고
  `scripts/plan_to_tasktree.py` 가 ast 로 기호 평가한다: 함수 호출 = 복합 task, `threading.Thread` start/join = 병렬 가지,
  최상위 `for` = 순차, 스킬 호출(`GoTo(...)` 등) = 원자 task. 쓸 수 있는 스킬과 인수는 `config/skills_catalog_basic.json`.
- 모듈 상수(`LEGS = []` 등)는 실행 시 그룹이 payload 값으로 바꿔 넣는다(`scripts/jnp_plan.py` `bind`). 계획 = 분할 구조, payload = 구체 값.
- 노드 이름·goal 문자열(`nav:x,y`, `trip:x,y@G`, `virtual:wait`, `explore`, `search`, …)은 `jnp_plan.py` 가 0.8.1 고정 빌더와
  같게 붙인다 — 그룹의 실행 시 후처리(병목 관찰자·양보 삽입·지도 병합 호스트)가 그 이름으로 노드를 찾기 때문.
- 확인: `source <catkin_ws>/devel/setup.bash && python3 test/test_plan_trees.py` (고정 빌더와 동일성, ROS 마스터 불필요),
  `python3 scripts/jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"` (계획·canonical·트리 덤프).
- 그룹 파라미터 `_plan_mode:=false` 면 이 경로를 끄고 0.8.1 고정 빌더를 쓴다(변환 실패 시에도 자동 대체).
