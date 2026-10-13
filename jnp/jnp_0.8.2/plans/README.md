# plans/ — 기본 협업 태스크의 작업 분할 계획 (JnP 0.8.2)

| goal (GUI) | 계획 파일 | 바인딩되는 상수 ← payload | 계획의 구조 (canonical) |
|---|---|---|---|
| Relay | `relay.py` | `ROBOTS`, `TARGETS` ← `name=x,y,th;…` | 순차: GoTo(r1) → GoTo(r2) → … |
| Mult-Goal | `multigoal.py` | `GOALS`, `ITEMS`, `GOAL_POS` ← `goals=G:x,y:count\|…` | 병렬: 물품마다 Trip(G.itemK) |
| Avoidance | `avoidance.py` | `FIRST`, `REST`, `TARGETS`, `PREV` ← `bt=…;routes=…` (ETA 순) | 병렬: 로봇마다 [WaitPass(prev) →] GoTo |
| MapExplore | `map_explore.py` | `HOST`, `EXPLORERS` ← `robots=…` (병합 호스트 1대) | 병렬: 로봇마다 Explore 가지 + MergeMaps\|SendMap 가지 |
| ObjectSearch | `object_search.py` | `ROBOTS` ← `robots=…` | 병렬: 로봇마다 Patrol 가지 + Detect 가지 |

## 경로

1. **계획** — LLM-TDM 형식(`# Task Description / # GENERAL TASK DECOMPOSITION / # CODE`)의 미리 작성된 템플릿. 실행 중 LLM 을 부르지는 않는다.
   `# CODE` 는 실행되지 않고 `scripts/plan_to_tasktree.py` 가 ast 로 기호 평가한다: 함수 호출 = 복합 task, 모듈 수준 `threading.Thread`
   start/join = 병렬 가지, 최상위 `for` = 순차, 스킬 호출(`GoTo(...)` 등) = 원자 task. 모듈 상수는 리스트·사전(`TARGETS[robot]`)을 쓸 수 있다.
   쓸 수 있는 스킬과 인수는 `config/skills_catalog_basic.json`.
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
- **R2 추가 능력 태그 → 요구 능력** — canonical `required_skills` 의 스킬 외 항목(예: `use_radar=True` → `radar`)은 원자 node 의
  requirement 에 더한다(할당기가 그 능력을 광고한 에이전트만 고른다). 조용히 버리지 않는다.
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

- **계약** — canonical 원자 ↔ 실행 원자 1:1, 순서 제약(선행 쌍) 집합 동일. 계획의 구조를 바꾸면(예: Relay 를 병렬로, ObjectSearch 를 순차로)
  어댑터의 고정 묶음과 어긋나 거부된다 — 구조를 바꾸려면 어댑터 규칙도 함께 바꿔야 한다.
- **완전성** — 태스크별 필수 스킬 수·중복·로봇·호스트: Relay 는 다리마다 GoTo 1개(payload 와 같은 순서), Mult-Goal 은 물품마다 Trip 1개,
  Avoidance 는 로봇마다 GoTo 1개 + (첫 로봇 제외) 앞 로봇을 기다리는 WaitPass 1개(ETA 순), MapExplore 는 로봇마다 Explore 1개 + 호스트는
  MergeMaps 1개·나머지는 SendMap 1개, ObjectSearch 는 로봇마다 Patrol 1개 + Detect 1개. 참여 로봇 밖의 단계, 어휘 밖 스킬·키워드 인자는 거부.
- **지원 범위** — Relay 로봇 이름 유일, MapExplore 호스트는 참여 로봇 중 하나, 바인딩 값에 제어문자 없음.

## 확인

- `source <workspace>/devel/setup.bash && python3 test/test_plan_trees.py` — ROS 마스터 불필요. A/B/C 동일성(0.8.1 고정 빌더와 서명 동일)·
  불변식(부모·선행/후행 상호 참조·별칭·complete)·계약, D 반례(바인딩 왕복/거부, 불완전·구조 변경·지원 범위 밖 계획의 거부, radar 태그 반영),
  E 그룹 연결부(대체 정책·strict·기록 여부).
- `python3 scripts/jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"` — 계획·canonical·트리 덤프(변환 예제. MapExplore 는
  `host=<robot>` 로 호스트를 지정; 실제 그룹은 컴퓨팅 등급으로 고른다).
- rosparam `/jnp/plan/<group>`: `source`(plan|legacy), `plan_file`, `bindings`, `canonical`, `warnings`, `tree`, 대체 시 `reason`.
