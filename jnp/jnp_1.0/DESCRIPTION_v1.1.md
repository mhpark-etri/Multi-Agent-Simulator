# JnP 설명(description) 형식 v1.1 — 정보 제공 항목 `<provides>` (2026-10-31)

JnP 1.0 프로그램 번호는 그대로이고, 설명 XML 형식만 v1.0 → v1.1 로 올린다.

- v1.0: `<data><item>…</item><agent>…</agent><goal>…</goal><capability>…</capability><skills source="…">…</skills><busy>0|1</busy></data>`
- v1.1: 위에 `<provides version="1.1"><item name="pose" type="geometry_msgs/PoseStamped" channel="/<에이전트>/jnp/provides/pose" rate="2.0"/>…</provides>` 를 더하고, 이때만 `<data version="1.1">` 속성을 붙인다.

규칙
- 제공 항목이 없으면(파라미터 `~jnp_provides` 비어 있음) 설명은 v1.0 과 바이트까지 같다. 옛 파서는 모르는 요소를 무시하고, 새 파서는 `<provides>` 가 없으면 None(구판 설명), 빈 요소면 [](없음 선언)으로 읽는다 — `<skills>` 와 같은 규칙.
- 항목 목록(jnp_rl_registry.PROVIDES_ITEMS): pose(내 위치), local_map(내 지도), goal(내 이동 목표), done_area(다 훑은 구역), detections(탐지 결과), assignment(리더의 배정 제안). 채널 이름은 `/<에이전트 노드 이름>/jnp/provides/<항목>`.
- 설명에 적히지 않은 채널로 주고받는 것은 금지. 다른 에이전트는 설명 서비스(`/<에이전트>/description_service`)로 설명을 읽고, 광고된 채널만 구독한다(jnp_rl_link.describe_and_subscribe).
- 통신 기록표(jnp_rl_meter.CommLog): **받는 쪽이** 한 줄씩 적는다 — 종류(data/control)·항목·보낸 이·받은 이·바이트. 설명 조회 응답과 구독 시작도 control 로 적는다. 메시지 본문 바이트만 센다.

G1 에서 구현된 것: 목록·설명 v1.1 생성/파싱, 구독·수신 기록, pose 발행기(`~jnp_provides:=pose`, `~jnp_provides_rate`). 다른 항목의 발행기와 정책 호출은 G2 이후.
