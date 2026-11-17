# plans/ — 기본 협업 태스크의 작업 분할 계획 (JnP 0.9.0: 로봇 미지정, 역할 기반)

| goal (미션 종류) | 계획 파일 | 바인딩되는 상수 ← payload | 역할(role) | 계획의 구조 (canonical v2) |
|---|---|---|---|---|
| Relay | `relay.py` | `LEGS`, `TARGETS` ← `name=x,y,th;…` (이름 = 선호 로봇 힌트, 좌표 = 다리 목표) | `leg1..legN` | 순차: GoTo(leg1) → GoTo(leg2) → … |
| Mult-Goal | `multigoal.py` | `GOALS`, `ITEMS`, `GOAL_POS` ← `goals=G:x,y:count\|…` | 없음(풀) | 병렬: 물품마다 Trip(G.itemK) — 자격 있는 유휴 로봇 아무나 |
| Avoidance | `avoidance.py` | `FIRST`, `REST`, `TARGETS`, `PREV` ← `bt=…;routes=…` (ETA 순) | 경로 이름(`routes=` 의 키) | 병렬: 역할마다 [WaitPass(앞 역할) →] GoTo |
| MapExplore | `map_explore.py` | `HOST`, `EXPLORERS` ← `robots=…` 의 **수** (이름은 선호 집합) | `host`, `explorer1..k-1` | 병렬: 역할마다 Explore 가지 + MergeMaps\|SendMap 가지; `ROLE_PREFER = {"host": ["compute_x86"]}` |
| ObjectSearch | `object_search.py` | `SEARCHERS` ← `robots=…` 의 수 | `searcher1..k` | 병렬: 역할마다 Patrol 가지 + Detect 가지 |
| ObjectSearch (변형 `explore`, 2026-11-07) | `object_search_explore.py` | `SEARCHERS` ← `robots=…` 의 수 | `searcher1..k` | 병렬: 역할마다 Explore 가지 + Detect 가지. 사전 지도가 없을 때(그룹 `~search_known_map:=false`) 고른다. 실행 트리는 `search.<r>` 안에 `patrol.<r>` 대신 `explore.<r>` |

## 경로 (0.9.0)

1. **계획** — LLM-TDM 형식(`# Task Description / # GENERAL TASK DECOMPOSITION / # CODE`)의 **example 템플릿**: 다섯 파일 모두 사람이 직접 쓴
   분할이며 LLM-TDM 모듈의 출력이 아니다(머리의 `# Plan Source: example`). **계획은 로봇을 지정하지 않는다** — 스킬 호출의 첫 자리
   `<robot>`(카탈로그 `role_param`)에 들어가는 이름이 **역할(role)** 이고(`leg1`, `host` …), 로봇은 그룹이 나중에 역할마다 고른다.
   `# CODE` 는 실행되지 않고 `scripts/plan_to_tasktree.py` 가 ast 로 기호 평가한다: 함수 호출 = 복합 task, 모듈 수준 `threading.Thread`
   start/join = 병렬 가지, 최상위 `for` = 순차, 스킬 호출(`GoTo(...)` 등) = 원자 task. 쓸 수 있는 스킬과 인수는 `config/skills_catalog_basic.json`(v0.3).
   - 역할 선언 상수(선택): `ROLE_REQUIRES = {"역할": ["능력 태그", …]}`(하드 요구), `ROLE_PREFER = {"역할": [...]}`(소프트 선호). 선언된 역할은
     계획의 단계에 나타나야 한다(아니면 거부).
   - **상수는 바인딩 뒤 읽기 전용**이다. 모듈 상수는 문자열 리스트·사전이고, `NAME[key]` 첨자는 스킬 인수·함수 호출/`Thread` 인수·`for` 반복
     대상 자리에서만 해석된다. 거부되는 구문(첨자/속성 대입, 증감 대입, `del`, 상수 메서드 호출, 어휘 밖 스킬·키워드 인자, 초과 위치 인자,
     해석 불가 인자, `while`, 정적으로 판정할 수 없는 `if`)은 0.8.2 와 같다.
   - 능력 태그(`use_radar=True` → `radar`)는 배정 대상 스킬에만 붙는다. canonical v2 에서는 `required_skills == [skill]` 이고 태그는 `requirements` 에 둔다.
2. **바인딩** — 그룹이 모듈 상수를 **역할 이름과 지점**으로 바꿔 넣는다(`scripts/jnp_plan.py` `plan_roles` → `bind`): Relay 는 payload 순서의
   `leg1..N` 과 좌표, Avoidance 는 경로 이름(ETA 순 FIRST/REST/PREV), MapExplore/ObjectSearch 는 요청 로봇 수만큼의 역할 이름. payload 의
   로봇 이름은 **선호 로봇 힌트**(계획 안에는 들어가지 않는다).
3. **canonical v2 TaskTree** — 변환기 출력(JSON, `contract: jnp-canonical-tasktree/2`): 단위 `{id, type, skill, args(역할 제외), role, required_skills:[skill],
   requirements, goal, optional?}`, 루트 `{text, source, contract, roles{역할:{requires,prefer}}, role_order}`. 그룹 콘솔 `[PLAN] canonical TaskTree` 와
   rosparam `/jnp/plan/<group>` 의 `canonical`.
4. **역할표·편성** — `jnp_plan.role_table` 이 역할마다 요구(스킬 합집합 + 요구 능력 + 선언 요구)를 모으고, 그룹(`jnp_group._recruit_and_plan`)이
   명부(모든 에이전트의 설명: 능력 + 광고 스킬 + busy)에서 `jnp_scheduler.assign_roles` 로 역할마다 로봇을 고른다(힌트 → 뒤 역할 힌트 보존 →
   명단 → prefer → 위치 아는 후보 → 시작점 ETA → 이름 자연 정렬; 결정적, 역할 선언 순 탐욕). 자격 로봇이 없는 역할은 `~unassigned_policy`(fail|skip|wait)로 처리한다.
   선택된 로봇은 action 서버에 접속해야 멤버가 되며, 재수집·재시도 중에도 같은 로봇의 접속 객체는 하나로 유지된다(광고 값만 갱신). 마지막 시도의
   접속 실패도 배정 불가로 돌린다. **후보 범위 기본값은 payload 명단(list-only)** — 명단 밖 로봇으로의 자동 대체는 `~candidates:=prefer-list|all` 로
   명시적으로 켠다.
5. **실행 트리** — `jnp_plan.build(…, roles_bound={역할: 로봇})` 의 태스크별 **어댑터**가 canonical 을 `jnp_task` 객체 트리로 바꾼다. 노드 이름은
   역할에 묶인 **로봇 이름**(`relay1.<robot>`, `make_maps.<robot>` …)이라 그룹의 후처리(병목 관찰자·양보 삽입·지도 병합 호스트·JnP Monitor)는
   0.8.2 와 같은 이름으로 노드를 찾는다. 원자 task 에는 `_role`, `_skill`, `_robot` 이 붙고, `RoleAllocator` 가 역할 task 를 묶인 로봇으로만 보낸다.

## 실행 변환 규칙 (어댑터가 하는 일 전부)

- **R1 카탈로그가 원자 node 실행 속성의 원천** — goal 문자열(`exec_goal` 템플릿을 args+robot 으로 포맷: `nav:{target}`, `trip:{target}@{destination}`,
  `virtual:wait`, `explore`, `search`, `service:yolov8`, `publish:map`, `service:map_merge`), 요구 능력(`requirement`), 원자 종류(`node`), `optional`,
  `preassigned`(에이전트에 배정하지 않는 상시 가상 서비스 — 표시용 agent `/etri/<역할의 로봇>`).
- **R2 능력 태그 → 요구 능력** — canonical `requirements`(예: `radar`)를 배정 대상 원자 node 의 requirement 에 더한다. 가상/상시 서비스 단계에 붙은 태그는 거부.
- **R3 역할별 묶음(MapExplore·ObjectSearch)** — 같은 `role` 의 병렬 가지들을 그 역할에 묶인 로봇 단위 병렬 복합(`make_maps.<r>`, `search.<r>`)으로 묶는다.
- **R4 navigate 래퍼(MapExplore)** — Explore 원자는 순차 복합 `navigate.<r>` 안에 둔다(병목 양보 task 의 삽입 지점).
- **R5 선행 사슬(Relay)** — 순차 자식 사이에 `addPredecessor` 를 건다.
- **R6 빈 goal 가지(Mult-Goal)** — goal 가지(`G[count]`)는 payload 순서대로 모두 만든다.
- **R7 가지 1개인 병렬 루트** — 변환기가 루트를 sequential 로 접으므로 어댑터가 병렬 루트로 되돌린다.
- **R8 역할 → 로봇(0.9.0)** — 모든 역할에 로봇이 묶여 있어야 트리를 만든다(아니면 PlanBuildError). 한 로봇이 두 역할에 묶이면 거부.
  `WaitPass.prev` 같은 역할 참조 인자는 그 역할의 로봇 이름으로 바꿔 노드 이름(`wait_pass.<robot>`)을 만든다.
- **이름 규칙** — `relay<N>.<robot>`, `<G>.item<K>` / `<G>[<count>]`, `cross.<robot>` / `wait_pass.<prev robot>` / `move.<robot>`,
  `make_maps.<r>` / `navigate.<r>` / `explore.<r>` / `merge_maps.<r>` / `send_map.<r>`, `search.<r>` / `patrol.<r>` / `detect.<r>`.

## 반환 전 검사와 실패의 세 갈래

실패는 단계에 따라 다르게 처리한다 — (1) **변환 단계 오류**(계획 파일 없음·변환 실패·canonical 검증 실패 = PlanBuildError 가 `plan_roles` 에서
나는 경우): 호환 모드로 0.8.1 고정 빌더에 대체하고 `recruit_mode` 를 goal 로 전환한다(`_plan_strict:=true` 면 예외 전파). (2) **편성 단계 오류**(설정 값 오류,
명부·접속·할당·바인딩·실행 트리 생성의 오류, 배정 불가): 대체하지 않고 그룹을 끝낸다(`/jnp/status` failed + 사유). (3) **명시적 legacy 선택**(`~plan_mode:=false`):
처음부터 고정 빌더. 아래 검사는 변환 단계(어휘·canonical 검증)와 실행 트리 생성 단계(계약·완전성·바인딩 — 빌더 안에서 수행)에 나뉘며, 실패 처리는
발생 단계에 따른다: skills 편성 경로에서 실행 트리 생성 실패는 (2) 편성 단계 오류로 종료한다. goal 모드의 그룹 래퍼(`_plan_or_legacy`)는 PlanBuildError 에
기존 fallback/strict 정책을 적용한다. 직접 CLI 실행(`python3 scripts/jnp_plan.py …`)은 PlanBuildError 를 출력하고 종료 코드 1 로 끝내며 legacy 대체를 하지 않는다.

- **계약** — canonical 원자 ↔ 실행 원자 1:1, 순서 제약(선행 쌍) 집합 동일. 계획의 구조를 바꾸면 어댑터의 고정 묶음과 어긋나 거부된다.
- **완전성** — 태스크별 필수 스킬 수·역할: Relay 는 다리(역할)마다 GoTo 1개(payload 순서), Mult-Goal 은 물품마다 Trip 1개, Avoidance 는 역할마다
  GoTo 1개 + (첫 역할 제외) 앞 역할을 기다리는 WaitPass 1개(ETA 순), MapExplore 는 역할마다 Explore 1개 + host 는 MergeMaps·나머지는 SendMap 1개,
  ObjectSearch 는 역할마다 Patrol 1개 + Detect 1개. 역할표 밖의 단계, 어휘 밖 스킬·키워드 인자는 거부.
- **지원 범위** — Relay 힌트 이름 유일, 바인딩 값에 제어문자 없음, 카탈로그 값 유효, 역할 선언은 단계에 나타난 역할만.
- **배정 불가**는 대체(legacy)가 아니라 실패다 — 그룹이 `[SCHED] 배정 불가` 와 `/jnp/status` failed(note 에 역할·사유)를 남기고 끝난다. 사유는
  "역할 선언 순 탐욕 배정에서 자격 로봇을 확보하지 못함"이다(전체 배정이 불가능하다는 증명이 아니다; 각 역할의 후보·거부 사유는 기록의 `recruit`).
  편성 이후의 실패(RecruitError: 잘못된 파라미터 값(`~candidates`·`~unassigned_policy`·`~recruit_timeout`), skip 뒤 빈 계획, 바인딩 뒤 트리 생성 실패,
  명부·접속 중 예외)도 대체하지 않고 그룹을 끝낸다 — 편성 단계의 어떤 예외도 호환 모드로 새지 않는다(R2-F3). 호환 모드(legacy 대체)는 **계획 변환이
  실패했을 때만** 쓰이며, 그때 그룹은 `recruit_mode` 를 goal 로 바꿔 0.8.2 방식(goal 매칭 등록·정족수 대기)으로 전환한다.
- **모집 중 제거·재등록 통보**(`kill:`·`new:`, R2-F1·R3-F1·R4-F1): 그룹은 노드마다 **등록 세대**를 둔다 — kill 처리와 명부(agent_list)에 없는 노드의
  신규 등록(new) 처리마다 +1(이미 명부에 있는 노드의 중복 new 는 세대를 올리지 않는다; 에이전트는 기동 때 new 를 3번 보낸다). 설명은 **요청 전의 세대**에
  묶어 받는다: 요청 도중 kill→new 가 처리돼 세대가 바뀌면 이전 응답을 버리고 한 번만 다시 요청하며, 두 번 연속 바뀌면 그 회차에서 뺀다(기록 `recruit.unstable`).
  세대가 바뀐 로봇의 설명·접속 객체·바인딩은 다시 쓰지 않는다 — '제거 표식 해제(new)' 와 '이전 접속 유효' 는 다르며, 재등록된 로봇은 새 설명을 받아 새로
  접속해야 후보가 된다. 접속·재등록 실패에 대한 **즉시 재시도는 최초 시도를 포함한 4번째 시도에서 끝나고**, 남은 미배정은 선택한 정책으로 처리한다 — fail 은
  그 시점에 종료하고, wait 는 남은 재수집 예산 안에서 추가 대기·수집할 수 있으므로 전체 attempts 가 4 를 넘을 수 있다. 편성 확정은 제거 콜백과 **같은 잠금** 안에서 한다:
  잠금 전에 끝난 kill/new 는 확정 검사에서 종료 사유가 되고, 잠금 뒤에 온 kill 은 기존 제거 경로(멤버 목록 제자리 갱신)로 반영되어 할당기·dispatch 가
  그 로봇에 보내지 않는다. 편성 뒤의 제거도 같은 경로다.
- **skip 정책**(`~unassigned_policy:=skip`): 건너뛸 수 있는 역할은 (a) 배정 대상 단계가 모두 선택 태스크(optional)이고 (b) 공유 서비스(카탈로그
  `shared_service`, MergeMaps)가 없고 (c) 다른 역할이 참조(WaitPass.prev)하지 않는 역할뿐이다. 건너뛴 역할은 계획에서 빼고 다시 변환한다
  (`jnp_plan.prep_without_roles`) — 가짜 로봇 이름을 쓰지 않으며 피더·서비스·Monitor 는 실제 로봇만 본다. 기록에 `skipped` 로 남고 '수행하지 않음'이지
  실행 성공이 아니다. 모든 역할을 건너뛰면 실행할 계획이 없어 실패한다.
- **wait 의 시간 계약**(R2-F2, ROUND3 §4 문구): `~recruit_timeout` 은 **미배정 역할이 남았을 때 추가 대기·재수집을 더 시작할지 판단하는 벽시계 예산**
  이다(첫 모집 루프 진입 기준). 미배정 상태에서 예산 소진을 확인하면 일반 대기 뒤 재수집을 더 시작하지 않는다; 대기는 min(2 s, 남은 예산)이다.
  **이미 시작한 수집·접속은 예산을 넘겨 완료될 수 있고 그 결과는 배정에 사용할 수 있다.** 첫 시도와 접속·재등록 실패에 대한 즉시 재시도(최초 시도를 포함한
  4번의 즉시 시도)는 이 시작 제한의 예외다.
  예산 소진 뒤에도 미배정이면 fail 과 같다. 전체 종료 시간 상한은 보장하지 않는다: 설명 수집은 서비스 대기 3 s/노드이고 서비스 응답 자체의 대기에는
  상한이 없다(응답이 멈춘 서비스는 미지원 범위), 접속은 5 s/후보다. 기록: `recruit.recollect_budget_s` = 예산(첫 수집은 예산 소진으로 취소하지 않지만 그
  경과는 이후 재수집 판단에 들어간다), `elapsed_s` = 수집·할당·접속 루프가 끝난 시점의 경과(뒤의 계획 재생성·확정·발행은 제외), `budget_exhausted` =
  미배정이 남아 예산 때문에 더 재수집하지 않고 끝난 경우에만 True(성공 경로에서는 경과가 예산을 넘어도 없을 수 있다 — `elapsed_s >= 예산` 과 동치가 아니다).
  값은 0 이상의 유한한 초(0 = 재수집 없음); 숫자가 아니거나 음수·NaN·무한대면 설정 오류로 그룹이 끝난다.
- **빈 명단**: `list-only` 인데 payload 에 로봇 이름이 없으면(예: Mult-Goal 의 `robots=` 비어 있음) 전체 명부로 확대하지 않고 입력 오류로 실패한다.

## 확인

- `source <workspace>/devel/setup.bash && python3 test/test_plan_trees.py` — 동일성(0.8.1 고정 빌더와 서명 동일; 기본 바인딩 = 힌트 순서)·불변식·계약·반례·그룹 연결부·기록.
- `python3 test/test_roles.py` — canonical v2(역할 추출·검증 반례), 역할표, 할당(결정성·3상태 스킬·대체·ETA·prefer·풀·정책), 실행 트리·RoleAllocator, 광고 왕복, 기록 v2.
- `python3 scripts/jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"` — 계획·canonical v2·역할표·기본 바인딩·트리 덤프.
- rosparam `/jnp/plan/<group>` / latched 토픽 `/jnp/plan`(`schema: jnp-plan-record/2`): `contract`, `roles`(역할표), `assignments`(역할 → 로봇과 사유: hinted/substituted/eta/prefer_hit),
  `recruit`(명부·거부 사유·정책), 배정 불가면 `unassigned`. `/jnp/status.members[]` 에 `skills`(null = 미광고)·`role`·`busy`. Monitor 는 역할 열과 스킬 층 매칭을 보여 준다.

## 그룹 파라미터 (0.9.0)

| 파라미터 | 기본 | 뜻 |
|---|---|---|
| `~recruit_mode` | `skills` | `skills` = 계획 먼저, 역할표로 명부에서 선택(B) / `goal` = 0.8.2 방식(goal 라벨 매칭 등록) |
| `~candidates` | `list-only` | payload 명단 안에서만(기본) / `prefer-list` = 명단 우선, 부족하면 명부 전체로 대체 / `all` = 명단 무시 (Mult-Goal 은 항상 list-only) |
| `~skills_strict` | `false` | `true` 면 스킬 미광고 로봇은 부적격(호환 모드 해제) |
| `~unassigned_policy` | `fail` | `fail` / `skip`(선택 태스크뿐인 역할 건너뜀) / `wait`(`~recruit_timeout` 동안 재수집) |
| `~recruit_timeout` | `20.0` | wait 정책의 **재수집 예산**(벽시계 초, 0 이상 유한). 전체 종료 상한이 아니다 — 위 '시간 계약' 참조 |

`~recruit_mode:=goal`(0.8.2 방식)에서도 할당기(Simple/Affinity/MultiGoal)는 같은 적격 검사(바쁨·광고 스킬·능력, `~skills_strict`)를 적격 후보 집합에
적용한다 — 선호·거리 규칙은 그 집합 위에서만 동작한다. 즉 goal 모드는 "스킬 검사를 끄는 모드"가 아니라 "멤버를 goal 라벨로 모으는 모드"다.

## 운영 조건과 한계 (0.9.0)

- **예약 없음.** 설명의 `<busy>` 는 광고 시점에 액션을 실행 중인지만 뜻한다. 다른 미션에 역할이 배정됐지만 아직 차례를 기다리는 로봇은 busy 가 아니다.
  그룹은 로봇을 원격으로 점유하지 않으므로, **동시에 돌리는 미션들의 payload 명단은 서로 겹치지 않아야 한다.** `list-only` 는 명단 밖 로봇을 끌어오지
  않게 할 뿐 겹치는 명단의 중복 배정은 막지 못한다. 공유 명부에서 자동 대체(`prefer-list`/`all`)를 켜는 것은 격리된 단일 미션 실험에서만 안전하다.
- 파일로 주는 설명(XML 파일)은 그대로 돌려주므로 `<skills>`/`<busy>` 가 파일에 적힌 값뿐이다(파일에 `<skills>` 가 없으면 미광고 = 호환 모드).
- 역할 할당은 선언 순 탐욕이다. 앞 역할이 뒤 역할의 유일한 후보를 가져가는 경우가 있으며(힌트는 보존한다), 재배치 탐색은 하지 않는다.
- payload 없이 그룹을 띄우는 기본 예제 경로(`jnp_group.py` 의 `TaskTree` 샘플 트리)는 0.9 편성(역할 모집)을 거치지 않는다 — skills 모드에서는 멤버가
  채워지지 않으므로 예제 용도로만 두고, 쓰려면 `~recruit_mode:=goal` 로 띄운다.
- 그룹 간 이적(`mgjoin:`, 다목적 이동)의 영입 자격은 0.8.2 와 같은 **goal 라벨 매칭**(+ 명단·접속)이며 초기 편성의 스킬 중심 자격과 다르다. 스킬 중심으로
  바꿀지는 미결(정책 결정 대기). 이적의 ROS 실측은 0.9 에서 하지 않았다.

에이전트: `~jnp_skills`(미지정 = 실행기 등록표 전부 광고, `none` = 없음 선언, `GoTo,Trip` = 부분집합, `unadvertised` = 요소 없음(구버전 호환 시험)).
