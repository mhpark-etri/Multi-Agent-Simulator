# plans/ — 기본 협업 태스크의 작업 분할 계획 (JnP 0.8.2)

| goal (GUI) | 계획 파일 | 바인딩되는 상수 ← payload | 계획의 구조 (canonical) |
|---|---|---|---|
| Relay | `relay.py` | `ROBOTS`, `TARGETS` ← `name=x,y,th;…` | 순차: GoTo(r1) → GoTo(r2) → … |
| Mult-Goal | `multigoal.py` | `GOALS`, `ITEMS`, `GOAL_POS` ← `goals=G:x,y:count\|…` | 병렬: 물품마다 Trip(G.itemK) |
| Avoidance | `avoidance.py` | `FIRST`, `REST`, `TARGETS`, `PREV` ← `bt=…;routes=…` (ETA 순) | 병렬: 로봇마다 [WaitPass(prev) →] GoTo |
| MapExplore | `map_explore.py` | `HOST`, `EXPLORERS` ← `robots=…` (병합 호스트 1대) | 병렬: 로봇마다 Explore 가지 + MergeMaps\|SendMap 가지 |
| ObjectSearch | `object_search.py` | `ROBOTS` ← `robots=…` | 병렬: 로봇마다 Patrol 가지 + Detect 가지 |

## 경로

1. **계획** — LLM-TDM 형식(`# Task Description / # GENERAL TASK DECOMPOSITION / # CODE`)의 **example 템플릿**: 다섯 파일 모두 사람이 직접 쓴
   분할이며 LLM-TDM 모듈의 출력이 아니다(머리의 `# Plan Source: example`; 기록·Monitor 에 `plan_source` 로 표시). 실행 중 LLM 을 부르지 않는다.
   실제 LLM-TDM 출력 파일을 쓰고 지원 DSL·어댑터 계약을 만족하는 경우 `# Plan Source: llm-tdm` 으로 출처를 선언한다 — 이 주석은
   **작성자 선언**이며 생성 사실을 검증하지 않는다(열거 example|llm-tdm 밖의 값과 누락은 unknown 으로 기록). 헤더만 바꾼다고 임의 계획이
   실행되거나 생성이 증명되는 것은 아니다.
   `# CODE` 는 실행되지 않고 `scripts/plan_to_tasktree.py` 가 ast 로 기호 평가한다: 함수 호출 = 복합 task, 모듈 수준 `threading.Thread`
   start/join = 병렬 가지, 최상위 `for` = 순차, 스킬 호출(`GoTo(...)` 등) = 원자 task. 쓸 수 있는 스킬과 인수는 `config/skills_catalog_basic.json`.
   - **상수는 바인딩 뒤 읽기 전용**이다. 모듈 상수는 문자열 리스트·사전(값은 문자열 또는 문자열 리스트)이고, `NAME[key]` 첨자는
     **스킬 인수·함수 호출/`Thread` 인수·`for` 반복 대상** 자리에서만 해석된다(키는 리터럴 또는 바인딩된 이름; 없는 키는 거부).
     지역 대입(`pos = TARGETS[robot]`)이나 조건식(`if D[k]:`) 안의 첨자는 지원하지 않는다.
   - **거부되는 구문**(변환 전에 PlanIssue → PlanBuildError, 조용히 건너뛰지 않음): 첨자/속성/다중 대입(`TARGETS[r] = …`), 증감 대입(`+=`),
     `del`, 상수에 대한 메서드 호출(`TARGETS.update(...)`, `ROBOTS.append(...)`, `.pop()` …), 카탈로그에 없는 스킬·키워드 인자,
     카탈로그보다 많은 위치 인자(`GoTo(robot, target, 'radar')`), 리터럴로 해석되지 않는 스킬 인자, `while`, 정적으로 판정할 수 없는 `if`.
     스레드 DSL(`t.start()`, `t.join()`, `threads.append(t)`)과 `import`·`pass`·docstring 은 그대로 허용된다.
   - 능력 태그(`use_radar=True` → `radar`)는 배정 대상 스킬(GoTo·Trip·Explore·Patrol)에만 붙일 수 있다. 가상/상시 서비스 단계
     (WaitPass·Detect·SendMap·MergeMaps)에 붙이면 거부된다(배정 대상이 아니라 센서 사용을 강제할 수 없다).
2. **바인딩** — 그룹이 모듈 상수(`ROBOTS = []` 등)를 payload 값으로 바꿔 넣는다(`scripts/jnp_plan.py` `bind`): 값은 JSON 리터럴로 넣고
   치환은 callable replacement 로 해 백슬래시·따옴표가 그대로 보존된다. 제어문자(줄바꿈 등)가 든 값은 거부한다.
   ETA 순서(Avoidance)와 병합 호스트(MapExplore)는 실행 환경 정보(로봇 속도·멤버 capability)라 계획 밖에서 정한다 —
   각각 `jnp_plan.build_avoidance`(그룹이 넘긴 parser·속도 함수)와 `jnp_group.py` 의 `_compute_rank`.
3. **canonical TaskTree** — 변환기 출력(JSON). 그룹 콘솔 `[PLAN] canonical TaskTree` 와 rosparam `/jnp/plan/<group>` 의 `canonical`.
4. **실행 트리** — `jnp_plan.py` 의 태스크별 **어댑터**가 canonical 을 `jnp_task` 객체 트리로 바꾼다. 아래 규칙만 적용한다.

## 실행 변환 규칙 (어댑터가 하는 일 전부)

- **R1 카탈로그가 원자 node 실행 속성의 원천** — goal 문자열(`exec_goal` 템플릿을 args 로 포맷: `nav:{target}`, `trip:{target}@{goal}`,
  `virtual:wait`, `explore`, `search`, `service:yolov8`, `publish:map`, `service:map_merge`), 요구 능력(`requirement`), 원자 종류(`node`:
  sequential/parallel), `optional`, `preassigned`(에이전트에 배정하지 않는 상시 가상 서비스 — 표시용 agent `/etri/<robot>`).
- **R2 추가 능력 태그 → 요구 능력** — canonical `required_skills` 의 스킬 외 항목(예: `use_radar=True` → `radar`)은 배정 대상 원자
  node 의 requirement 에 더한다(할당기가 그 능력을 광고한 에이전트만 고른다). 가상/상시 서비스 단계에 붙은 태그는 거부한다. 조용히 버리지 않는다.
- **R3 로봇별 묶음(MapExplore·ObjectSearch)** — 같은 `robot` 인수를 가진 병렬 가지들을 로봇 단위 병렬 복합(`make_maps.<r>`, `search.<r>`)으로
  묶는다. 병렬의 병렬이므로 순서 제약은 그대로다.
- **R4 navigate 래퍼(MapExplore)** — Explore 원자는 순차 복합 `navigate.<r>` 안에 둔다. 자식이 하나라 순서 제약은 없고, 실행 중 병목 양보
  task(`yield.<상대>`)를 그 앞에 끼우는 삽입 지점이다(그룹의 `_seqbr`).
- **R5 선행 사슬(Relay)** — 순차 자식 사이에 `addPredecessor` 를 건다. 순차 복합이 이미 뜻하는 제약과 같다(0.8.1 과 동일).
- **R6 빈 goal 가지(Mult-Goal)** — goal 가지(`G[count]`)는 payload 순서대로 모두 만든다. 물품 0개면 빈 가지(0.8.1 과 같음; GUI 는 1~9 만 낸다).
- **R7 가지 1개인 병렬 루트** — 변환기가 루트를 sequential 로 접으므로 어댑터가 병렬 루트로 되돌린다(의미 동일).
- **이름 규칙** — `relay<N>.<robot>`, `<G>.item<K>` / `<G>[<count>]`, `cross.<robot>` / `wait_pass.<prev>` / `move.<robot>`,
  `make_maps.<r>` / `navigate.<r>` / `explore.<r>` / `merge_maps.<r>` / `send_map.<r>`, `search.<r>` / `patrol.<r>` / `detect.<r>`.
  그룹의 실행 시 후처리(병목 관찰자·양보 삽입·지도 병합 호스트·JnP Monitor)가 이 이름으로 노드를 찾는다.

## 반환 전 검사 (어긋나면 PlanBuildError → 그룹은 0.8.1 고정 빌더로 대체, `_plan_strict:=true` 면 예외 전파)

- **계약** — canonical 원자 ↔ 실행 원자 1:1, 순서 제약(선행 쌍) 집합 동일(순차 복합의 앞/뒤 원자 모든 쌍 + 명시적 선행의 직접 간선;
  전이 폐쇄는 계산하지 않으므로 어댑터가 만드는 트리 범위의 검사다). 계획의 구조를 바꾸면(예: Relay 를 병렬로, ObjectSearch 를 순차로)
  어댑터의 고정 묶음과 어긋나 거부된다 — 구조를 바꾸려면 어댑터 규칙도 함께 바꿔야 한다. 원자의 실행 속성은 이 검사가 아니라
  카탈로그(R1)와 `test/test_plan_trees.py` 의 동일성 검사가 확인한다.
- **완전성** — 태스크별 필수 스킬 수·중복·로봇·호스트: Relay 는 다리마다 GoTo 1개(payload 와 같은 순서), Mult-Goal 은 물품마다 Trip 1개,
  Avoidance 는 로봇마다 GoTo 1개 + (첫 로봇 제외) 앞 로봇을 기다리는 WaitPass 1개(ETA 순), MapExplore 는 로봇마다 Explore 1개 + 호스트는
  MergeMaps 1개·나머지는 SendMap 1개, ObjectSearch 는 로봇마다 Patrol 1개 + Detect 1개. 참여 로봇 밖의 단계, 어휘 밖 스킬·키워드 인자는 거부.
- **지원 범위** — Relay 로봇 이름 유일, MapExplore 호스트는 참여 로봇 중 하나, 바인딩 값에 제어문자 없음, 카탈로그 값(`node`, `requirement`) 유효.

## 확인

- `source <workspace>/devel/setup.bash && python3 test/test_plan_trees.py` — ROS 마스터 불필요. A/B/C 동일성(0.8.1 고정 빌더와 서명 동일)·
  불변식(부모·선행/후행 상호 참조·별칭·complete)·계약, D 반례(바인딩 왕복/거부, 불완전·구조 변경·지원 범위 밖 계획의 거부, radar 태그 반영,
  상수 변경문·상수 메서드 호출·초과 위치 인자·해석 불가 인자의 거부),
  E 그룹 연결부(대체 정책·strict·기록 여부).
- `python3 scripts/jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"` — 계획·canonical·트리 덤프(변환 예제. MapExplore 는
  `host=<robot>` 로 호스트를 지정; 실제 그룹은 컴퓨팅 등급으로 고른다).
- rosparam `/jnp/plan/<group>`: `source`(plan|legacy), `plan_file`, `bindings`, `canonical`, `warnings`, `tree`, `subtasks`(행별 스킬·요구 능력·실행 node), 대체 시 `reason`.
  같은 내용이 latched 토픽 `/jnp/plan`(std_msgs/String, JSON 한 줄, `schema: jnp-plan-record/1`)로도 나간다 — JnP Monitor 의
  '미션 → 작업 분할 → 스킬 매칭' 패널이 받는다. 타입 주의: rosparam 의 `bindings`·`canonical`·`subtasks` 는 JSON **문자열**, 토픽에서는
  객체/배열이다. 두 기록 모두 `run_id`(그룹 프로세스 = 회차)를 싣고 그룹의 `/jnp/status` 도 같은 `run_id` 를 실으므로 Monitor 는 같은
  회차끼리만 계획과 상태를 결합한다. legacy(고정 빌더) 기록은 `plan_source` 가 빈 문자열이다. 기록은 **초기 트리** 기준이며
  (`preassigned` = 초기 상시 서비스, `after` = 명시적 선행만) 그룹 프로세스가 끝나면 latched 메시지도 사라진다(영구 보관 아님).
