# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G1 2026-10-31] 통신 기록표 — 누가 누구에게 어떤 항목을 몇 바이트 보냈는지 한 줄씩 적는다(ROS 없이 import 된다).

규칙: 받는 쪽이 적는다(수신자가 둘이면 두 줄, 즉 두 번 센다). 메시지 본문 바이트만 센다(TCP 등 전송 계층 제외).
kind = 'data'(제공 항목 수신) | 'control'(설명 조회·구독 시작 같은 제어 메시지) | 'meta'(계측기 생존 표시, 바이트 0). 파일은 JSON 한 줄씩(.jsonl).
[2026-11-01, R5 F2] 생존 표시 줄(start/alive/end)을 더했다. 집계(aggregate)는 수신자마다 이 줄로 기록표가 회차 내내 살아 있었는지
확인하고, 식별자·시각이 빠진 줄·음수 바이트·빠진 수신자는 조용히 통과시키지 않고 무효(invalid)로 표시한다."""
import json
import math
import os
import time


class CommLog(object):
    def __init__(self, agent_name, path=None, run_id=None, clock=None, write_start=True):
        """run_id: 회차 식별자(채점은 같은 회차 줄만 합친다). clock: 시뮬 시각 함수(예: rospy.get_time) — 줄마다 t_sim 으로 적는다.
        [JnP-1.0 RL 2026-11-01, R4 F7] 벽시계 t 만으로는 회차 구간을 나눌 수 없었다. write_start: 열자마자 'start' 줄을 적는다."""
        self.agent = str(agent_name).strip('/')
        self.path = path
        self.rows = []
        self.run_id = str(run_id) if run_id else (os.environ.get('JNP_RUN_ID') or '')
        self.clock = clock
        self.closed = False
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
        if write_start:
            self.meta('start')

    def _row(self, kind, item, sender, receiver, nbytes, t=None, extra=None):
        row = {'t': time.time() if t is None else float(t), 'kind': kind, 'item': item,
               'sender': str(sender).strip('/'), 'receiver': str(receiver).strip('/'), 'bytes': int(nbytes)}
        if extra:
            row.update({str(k): v for k, v in dict(extra).items() if k not in row})   # [R8 F3] 결과물 digest 같은 덧붙임 칸
        if self.run_id:
            row['run_id'] = self.run_id
        if self.clock is not None:
            try:
                row['t_sim'] = float(self.clock())
            except Exception:
                pass
        self.rows.append(row)
        if self.path:
            with open(self.path, 'a') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
        return row

    def record(self, kind, item, sender, receiver, nbytes, t=None, extra=None):
        return self._row(kind, item, sender, receiver, nbytes, t, extra)

    def meta(self, what, t=None):
        """생존 표시 줄: 'start'(기록표 열림) / 'alive'(주기 표시) / 'end'(정상 종료). 바이트 합계에 들어가지 않는다."""
        if self.closed:
            return None
        return self._row('meta', what, self.agent, self.agent, 0, t)

    def close(self):
        if not self.closed:
            self.meta('end')
            self.closed = True

    def summary(self):
        return summarize(self.rows)


def _is_meta(r):
    return r.get('kind') == 'meta'


def summarize(rows):
    out = {'bytes_total': 0, 'by_kind': {}, 'by_item': {}, 'by_pair': {}, 'rows': 0, 'meta_rows': 0}
    for r in rows:
        if _is_meta(r):
            out['meta_rows'] += 1
            continue
        b = int(r['bytes']); out['bytes_total'] += b; out['rows'] += 1
        out['by_kind'][r['kind']] = out['by_kind'].get(r['kind'], 0) + b
        out['by_item'][r['item']] = out['by_item'].get(r['item'], 0) + b
        k = '%s->%s' % (r['sender'], r['receiver'])
        out['by_pair'][k] = out['by_pair'].get(k, 0) + b
    return out


def read_log(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _short(name):
    return str(name).strip('/').split('/')[-1]


def _bad_row(r, run_id, need_time=True):
    """결함 줄 사유(없으면 None): 식별자 누락(run_id 로 거를 때), sim 시각 누락(시간 구간으로 거를 때), 비유한/음수 바이트, 필수 칸 누락."""
    if run_id and not r.get('run_id'):
        return 'missing run_id'
    ts = r.get('t_sim')
    if ts is None:
        if need_time:
            return 'missing t_sim'
    else:
        try:
            if not math.isfinite(float(ts)):
                return 't_sim not finite'
        except Exception:
            return 't_sim malformed'
    b = r.get('bytes')
    if isinstance(b, bool) or not isinstance(b, (int, float)) or not math.isfinite(float(b)) or b < 0:
        return 'bad bytes %r' % (b,)
    for k in ('kind', 'item', 'sender', 'receiver'):
        if not r.get(k):
            return 'missing %s' % k
    return None


def aggregate(paths, t0=None, t1=None, run_id=None, receivers=None, t_end=None, alive_period_s=10.0, start_grace_s=30.0):
    """여러 에이전트의 기록표 파일을 합쳐 요약한다(각 수신자가 자기 몫을 적으므로 그냥 더하면 된다).
    t0·t1(시뮬 초)이 있으면 t_sim 이 그 구간 안인 줄만, run_id 가 있으면 그 회차 줄만 센다(F7). 구간 밖·다른 회차 줄 수도 적는다.
    [R5 F2] 완전성 확인 — receivers(기대 수신자 이름 목록)·t_end(회차의 실제 종료 sim 초, 없으면 t1)가 있으면:
      수신자마다 start 줄이 t0 + start_grace_s 안에 있어야 하고(런타임은 태스크를 받은 뒤 만들어지므로 몇 초 늦게 열린다 — 그 늦음은 start_gap_s 로 기록),
      t_end 가까이(생존 표시 주기의 2.5배 안)까지 alive/end 또는 데이터 줄이 있어야 한다.
      식별자·시각이 빠진 줄, 비유한/음수 바이트, 빠진 수신자 → invalid=True 와 reasons. 기록 0건은 생존 표시가 갖춰졌을 때만 유효(B=0)."""
    rows, dropped, malformed = [], 0, []
    per = {}
    need_time = any(v is not None for v in (t0, t1, t_end))        # 시간 구간으로 거를 때만 t_sim 이 필수
    for p in paths:
        for r in read_log(p):
            if run_id and r.get('run_id') and r['run_id'] != run_id:
                if not _is_meta(r):
                    dropped += 1
                continue
            why = _bad_row(r, run_id, need_time)
            if why:
                malformed.append({'file': os.path.basename(p), 'why': why, 'row': r})
                continue
            ts = float(r['t_sim']) if r.get('t_sim') is not None else None
            st = per.setdefault(_short(r['receiver']), {'start': None, 'end': None, 'alive': None, 'last_row': None, 'rows': 0, 'file': os.path.basename(p)})
            if _is_meta(r):
                k = r.get('item')
                if ts is None:
                    continue
                if k == 'start':
                    st['start'] = ts if st['start'] is None else min(st['start'], ts)
                elif k in ('end', 'alive'):
                    st[k] = ts if st[k] is None else max(st[k], ts)
                continue
            if ts is not None:
                st['last_row'] = ts if st['last_row'] is None else max(st['last_row'], ts)
            if ts is not None and ((t0 is not None and ts < t0) or (t1 is not None and ts > t1)):
                dropped += 1
                continue
            rows.append(r); st['rows'] += 1
    out = summarize(rows)
    out['rows_dropped'] = dropped
    out['rows_malformed'] = len(malformed)
    out['malformed_examples'] = malformed[:3]
    out['window'] = [t0, t1]
    out['run_id'] = run_id
    out['t_end'] = t_end
    reasons = []
    if malformed:
        reasons.append('%d malformed rows (first: %s)' % (len(malformed), malformed[0]['why']))
    expect = [_short(x) for x in receivers] if receivers else sorted(per)
    end_ref = t_end if t_end is not None else t1
    out['receivers'] = {}
    for rec in expect:
        st = per.get(rec)
        if st is None:
            reasons.append('receiver %s: no ledger rows' % rec)
            out['receivers'][rec] = None
            continue
        out['receivers'][rec] = dict(st)
        if st['start'] is None:
            reasons.append('receiver %s: no start row' % rec)
        elif t0 is not None:
            gap = st['start'] - float(t0)
            out['receivers'][rec]['start_gap_s'] = round(gap, 3)
            if gap > float(start_grace_s):
                reasons.append('receiver %s: ledger opened %.1f s after t0 (grace %.0f s)' % (rec, gap, float(start_grace_s)))
        if end_ref is not None:
            seen = [v for v in (st['end'], st['alive'], st['last_row']) if v is not None]
            last = max(seen) if seen else None
            if last is None or last < float(end_ref) - 2.5 * float(alive_period_s):
                reasons.append('receiver %s: no alive/end evidence near %.1f (last %s)' % (rec, float(end_ref), 'none' if last is None else '%.1f' % last))
    if reasons:
        out['invalid'] = True
        out['reasons'] = reasons
    return out
