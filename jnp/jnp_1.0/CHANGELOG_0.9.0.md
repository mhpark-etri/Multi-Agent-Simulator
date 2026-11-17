# JnP 0.9.0 (2026-10-18) — 스킬 기반 할당: 로봇 미지정 계획 · 역할 · 계획 우선 편성

0.8.2 → 0.9.0 변경(패키지 `jnp/jnp_0.9.0/`, 0.8.2 는 그대로 둠).

## 바뀐 것
- **설명(description)에 스킬 광고(advertisement)** — `jnp_agent.py`: 실행기 등록표 `SKILL_HANDLERS`(GoTo→nav:, Trip→trip:, Explore→explore, Patrol→search)에서
  `<skills source="registry|param">` 을 자동 유도. `~jnp_skills`(부분집합 / `none` / `unadvertised`). 실행 중이면 `<busy>1</busy>`.
- **계획은 로봇을 지정하지 않는다** — `plans/*.py` 의 상수가 역할 이름(LEGS·경로 이름·HOST/EXPLORERS·SEARCHERS)으로 바뀜. 스킬 서명의 `<robot>` 자리 = 역할(role).
  Trip 의 매개변수 `goal` → `destination`.
- **canonical v2** (`plan_to_tasktree.py`, `contract: jnp-canonical-tasktree/2`): 단위 task 에 `role`, `required_skills == [skill]`(1:1), 능력 태그는 `requirements`,
  `optional`; 루트에 `roles{요구·선호}`·`role_order`. `ROLE_REQUIRES`/`ROLE_PREFER` 선언 상수. 역할 참조 인자(WaitPass.prev) 검증.
- **계획 우선 편성(B)** — `jnp_group.py` `_recruit_and_plan`: 계획 변환 → 역할표(`jnp_plan.role_table`) → 명부 수집(goal 필터 없음, `collect_candidates`) →
  역할마다 적격 검사·결정적 선택(`jnp_scheduler.assign_roles`: 힌트 → 뒤 역할 힌트 보존 → 명단 → prefer → 시작점 ETA → 이름 자연 정렬) → 선택된 로봇만
  접속·멤버 등록 → 역할→로봇 바인딩으로 실행 트리(`jnp_plan.build(roles_bound=…)`). 풀 task(Trip)는 자격 있는 유휴 로봇 아무나.
  파라미터 `~recruit_mode`(skills|goal), `~candidates`(list-only[기본]|prefer-list|all), `~skills_strict`, `~unassigned_policy`(fail|skip|wait), `~recruit_timeout`(벽시계).
- **적격 검사** `jnp_scheduler.can_execute`: busy 아님 ∧ (광고가 있으면) 스킬 ⊇ 요구 스킬 ∧ 능력 ⊇ 요구 능력. 스킬 3상태(None 미광고 = 호환, [] 없음 선언 = 불가).
  `RoleAllocator`(역할 task 는 묶인 로봇으로만, 풀은 기존 할당기 규칙) + `dispatch` 최종 방어.
- **배정 불가** — 대체가 아니라 실패: `[SCHED] 배정 불가: 역할 … (후보별 사유)`, `/jnp/status` failed(note), `/jnp/plan` 에 `unassigned`, 그룹 종료(coalition 이면 해체).
- **기록 v2** (`schema: jnp-plan-record/2`): `contract`, `roles`, `assignments[{role, robot, reason}]`, `recruit{mode, candidates, rejected, …}`, 행에 `role`·`robot`·`requirements`.
  `/jnp/status.members[]` 에 `skills`·`role`·`busy`.
- **Monitor** (`code/Multi-Agent-Simulator/dlgJnpMonitor.py`): 역할 열, 스킬 층 매칭(✓/✗/미광고(호환)), 편성 요약(힌트·대체·부적격 사유), 배정 불가 표시, 멤버 목록에 skills·역할.
- **카탈로그 v0.3** (`config/skills_catalog_basic.json`): `role_param`, `role_refs`, `description`, `aliases`, `has_executor_wrapper`, `capabilities`.

## 바뀌지 않은 것
- GUI payload 형식(이름은 선호 로봇 힌트로 해석), 실행 트리의 노드 이름(역할에 묶인 로봇 이름), 스케줄러 루프, 에이전트 `execute()` 분기,
  다목적 이동의 분산 goal 선택(그룹 안에서는 list-only + 스킬 검사), 동적 충돌회피(솔로), 0.8.1 고정 빌더 대체(계획 경로 실패 시).
- `~recruit_mode:=goal` 이면 0.8.2 의 편성(goal 매칭 등록 + 힌트 순서 바인딩)으로 돈다.

## 검사
- `test/test_plan_trees.py`(기존 25건 + v2 반영), `test/test_roles.py`(신설), `code/Multi-Agent-Simulator/test_dlgJnpMonitor_html.py`(스킬 층·역할 열 추가).
- 최소 동작 확인(가짜 move_base, Gazebo 없음): 릴레이 3구간·에이전트 4대 중 1대 GoTo 미광고 → 명단 밖 로봇으로 대체·SUCCESS; 3대뿐이면 배정 불가 → failed·종료.
  (내부 기록 폴더 verification_20261018_v090 의 smoke.out / smoke_unassigned.out)

## 검토 반영 (2026-10-18, V-F1~V-F7)
- V-F1 재수집·재시도 중 접속 객체 유지(광고 값만 갱신), 마지막 회차 접속 실패도 배정 불가, wait 기한은 벽시계(`time.sleep`), 접속 없는 멤버 불변식.
- V-F2 skip 은 역할을 계획에서 빼고 재변환(`prep_without_roles`, 가짜 로봇 없음); 건너뛸 수 있는 역할 = 선택 태스크뿐 + 공유 서비스 없음 + 참조 안 됨;
  편성 이후 실패는 `RecruitError` 로 종료(legacy 우회 없음); 호환 모드 전환 시 recruit_mode=goal 로 일관.
- V-F3 RoleAllocator·Affinity bind·dispatch 가 현재 멤버가 아닌 로봇에 보내지 않음(바인딩 무효, 재할당 없음).
- V-F4 빈 명단 list-only 는 입력 오류로 실패(전체 명부 확대 없음).
- V-F5 validator: args 자료형·숨은 역할 인자·role_order/roles 형식·optional 계약; `_check_bound` 에 중복 로봇·역할표 밖 키 검사(모든 goal).
- V-F6 Simple/Affinity/MultiGoal 할당기가 적격 후보 집합(바쁨·스킬·능력) 위에서 동작, `~skills_strict` 를 모든 경로에서 초기화.
- V-F7 기본 후보 범위 = payload 명단(list-only); 자동 대체는 명시적 선택; busy = 광고 시점 실행 여부(예약 아님); 동시 미션 명단 비중첩 운영 조건 명시.
- 권고 반영: V-F8 배정 불가 문구(탐욕 배정 한정)·설계 문서 키 갱신, V-F9 Monitor strict 회차 표시·검사 수 정정, V-F10 mgjoin 성공 로그 한정·호환 모드 전환 명시,
  V-F11 위치 모르는 후보 후순위(pos_known).

## 검토 반영 2차 (2026-10-19, R2-F1~R2-F3)
- R2-F1 모집 중 `kill:` 통보의 최종성: 그룹이 `_killed` 집합을 기록하고(`new:` 로 해제) 편성이 후보·접속 캐시·바인딩에서 제거, 재할당. 확정 직전 재확인(되살리지 않음).
- R2-F2 시간 계약 확정: `~recruit_timeout` = 미배정 시 추가 대기·재수집을 더 시작할지 판단하는 예산(벽시계). 첫 수집·접속 재시도는 예산 밖, 대기는 min(2 s, 남은 예산),
  예산 소진 뒤 새 재수집을 시작하지 않음(이미 시작한 수집·접속은 예산을 넘겨 끝나도 그 결과를 배정에 씀), 전체 종료 상한 아님(서비스 응답 대기 상한 없음 = 미지원 범위 명시).
  기록에 `recollect_budget_s`·`elapsed_s`(루프 종료 시점)·`budget_exhausted`(미배정으로 끝난 경우에만).
- R2-F3 설정 오류의 종료: 파라미터 검증(`_recruit_params`: 숫자·0 이상·유한)과 편성 단계의 모든 예외를 RecruitError 로 정규화 — 호환 모드(legacy)는 계획 변환 실패에만.
- 문서: 실패의 세 갈래(변환 단계 대체 / 편성 단계 종료 / 명시적 legacy), payload 없는 예제 경로·mgjoin 정책 미결을 README 한계에 기록, 기록 v2 에 `roles_all` 직렬화.

## 검토 반영 3차 (2026-10-19, R3-F1·§4·§5)
- R3-F1 노드별 등록 세대(`_reg_gen`, kill·new 마다 +1)와 제거 콜백 ↔ 편성 확정의 공유 잠금(`_member_lock`): 세대가 바뀐 접속 객체·바인딩은 재사용하지 않고(재등록 로봇은
  새 설명·새 접속), 확정은 잠금 안에서 제거·재등록을 검사하며 잠금 뒤의 kill 은 기존 제거 경로로 반영된다. 편성 중 재등록이 접속 회차 한도까지 반복되면 배정 불가.
- §4 시간 계약 문구를 "예산 소진 뒤 새 재수집을 시작하지 않음(시작한 수집·접속은 완료 가능)" 으로 좁히고 기록 세 필드의 정의를 명시. §5 검사 단계 안내 문구 보완.

## 검토 반영 4차 (2026-10-19, R4-F1·R4-N1·R4-N2)
- R4-F1 설명 응답을 **요청 전 세대**에 묶음(`collect_candidates`): 요청 도중 kill→new 로 세대가 바뀌면 이전 응답 폐기·한 번 재요청, 두 번 연속이면 그 회차 제외(`recruit.unstable`). 이전 설명에
  근거한 편성·발송 없음. 무제한 내부 재수집은 도입하지 않음(기존 fail/wait 정책·예산에 귀속).
- R4-N1 문구: 즉시 재시도는 최초 시도 포함 4번째 시도에서 끝나고 남은 미배정은 정책으로(fail 종료 / wait 는 예산 안 추가 수집 → attempts 가 4 를 넘을 수 있음); 세대 증가 조건을
  "kill 처리 및 명부에 없는 노드의 new 처리" 로 정확히 기술. R4-N2 문구: CLI 는 PlanBuildError 출력·종료 코드 1, legacy 대체 없음.

## 알려진 한계·다음 단계
- 역할 할당은 선언 순 탐욕(greedy)이며 재배치 탐색이 없다. 배정 불가는 "탐욕 배정에서 확보 못함"이지 전체 배정 불가능의 증명이 아니다(각 역할의 후보·사유는 recruit).
- 예약 없음: busy 는 실행 중 표시뿐. 동시 미션의 명단이 겹치면 중복 배정을 막지 못한다(plans/README 운영 조건). 이탈 감지·재할당·재분할은 다음 단계.
- LLM-TD 연결(계획 파일 자리에 모듈 출력)은 다음 단계; GUI 의 지점 입력(명단 대신)은 미반영.
