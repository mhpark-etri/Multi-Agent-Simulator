# -*- coding: utf-8 -*-
"""[JnP-1.0 RL 2026-11-01, R5 F6] 격자 지도 메시지 공통 검사 — 채점 모니터(결과물·합집합 입력)와 로봇 런타임(자기 지도·받은 지도)이
같은 함수로 거른다. ROS 없이 import 된다.

규약(리더보드 지도 결과물, 2026-11-01 결정 (c) 포함):
  - 좌표계 이름(frame_id)은 'map' 또는 트랙이 정한 별칭 목록 안의 이름. 빈 이름은 거부한다.
  - 원점 자세는 정규화된 quaternion 이고 2D 항등(roll·pitch·yaw 모두 0 근방). NaN·무한대는 거부.
  - 해상도·원점은 유한하고 해상도는 허용 범위 안. 크기 w,h ≥ 1, w×h ≤ max_cells, 데이터 길이 = w×h.
  - 셀 값은 -1(모름) 또는 0..100.
의미 검증(이 함수)과 수신 비용 계측은 별개다 — 거부된 지도의 수신 바이트도 비용으로 센다(R5 F2)."""
import math

try:
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None

DEFAULT_FRAMES = ('map',)
DEFAULT_RES_RANGE = (0.01, 0.2)
DEFAULT_MAX_CELLS = 4000000          # 2000×2000 칸 = 0.05 m 칸으로 100 m × 100 m
QUAT_TOL = 1e-3
ORIGIN_MAX_M = 1e4


def yaw_of_quat(x, y, z, w):
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def quat_from_yaw(yaw):
    return (0.0, 0.0, math.sin(0.5 * float(yaw)), math.cos(0.5 * float(yaw)))


def _finite(*vals):
    for v in vals:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return False
        if not math.isfinite(float(v)):
            return False
    return True


def check_quat(q, tol=QUAT_TOL):
    """2D 항등 자세인가: 유한·정규화·roll/pitch/yaw ≈ 0. 반환 (ok, 이유)."""
    try:
        x, y, z, w = (float(v) for v in q)
    except Exception:
        return False, 'quaternion malformed'
    if not _finite(x, y, z, w):
        return False, 'quaternion not finite'
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if abs(n - 1.0) > tol:
        return False, 'quaternion norm %.4f != 1' % n
    if abs(x) > tol or abs(y) > tol:
        return False, 'roll/pitch not zero (x=%.4f y=%.4f)' % (x, y)
    yaw = yaw_of_quat(x / n, y / n, z / n, w / n)
    if abs(yaw) > tol:
        return False, 'non-zero yaw %.4f not supported' % yaw
    return True, ''


def check_grid(info, data, frame_id='map', quat=(0.0, 0.0, 0.0, 1.0), accept_frames=DEFAULT_FRAMES,
               res_range=DEFAULT_RES_RANGE, max_cells=DEFAULT_MAX_CELLS, check_cells=True):
    """info=(res, ox, oy, w, h), data=셀 값 목록/배열. 반환 (ok, 이유). 거부 사유는 한 가지만(처음 걸린 것) 돌려준다."""
    try:
        res, ox, oy, w, h = info
        res, ox, oy = float(res), float(ox), float(oy)
        w, h = int(w), int(h)
    except Exception:
        return False, 'info malformed'
    frames = tuple(accept_frames) if accept_frames else DEFAULT_FRAMES
    if frame_id is None or str(frame_id) not in frames:
        return False, 'frame %r not accepted (%s)' % (frame_id, ','.join(frames))
    if not _finite(res, ox, oy):
        return False, 'geometry not finite'
    if not (float(res_range[0]) <= res <= float(res_range[1])):
        return False, 'resolution %.4f out of range' % res
    if abs(ox) > ORIGIN_MAX_M or abs(oy) > ORIGIN_MAX_M:
        return False, 'origin out of range'
    if w < 1 or h < 1:
        return False, 'empty grid'
    if w * h > int(max_cells):
        return False, 'grid %dx%d exceeds %d cells' % (w, h, int(max_cells))
    n = len(data)
    if n != w * h:
        return False, 'data length %d != %d' % (n, w * h)
    ok, why = check_quat(quat)
    if not ok:
        return False, why
    if check_cells:
        if _np is not None:
            d = _np.asarray(data)
            if d.dtype.kind not in 'iu':
                try:
                    d = d.astype(_np.int64)
                except Exception:
                    return False, 'cell values not integer'
            bad = (d < -1) | (d > 100)
            if bool(bad.any()):
                return False, 'cell value out of domain (%d cells)' % int(bad.sum())
        else:  # pragma: no cover
            for v in data:
                if v < -1 or v > 100:
                    return False, 'cell value %r out of domain' % (v,)
    return True, ''


def message_digest(msg, n=16):
    """[R8 F3, Gazebo 12차에서 발견] 결과물 내용 digest: header.seq 를 0 으로 둔 직렬화 바이트의 sha256 앞 n 자리.
    ROS 는 latched 메시지를 늦게 붙은 구독자에게 다시 보낼 때 seq 를 새로 매기므로, seq 를 포함한 digest 는 보낸 쪽과 받은 쪽이 달라진다.
    보낸 쪽(런타임)과 받은 쪽(채점 모니터)이 같은 함수를 쓴다. 메시지 객체는 바꾸지 않는다(seq 를 잠시 0 으로 두고 되돌린다)."""
    import hashlib
    import io
    seq = None
    hdr = getattr(msg, 'header', None)
    if hdr is not None and hasattr(hdr, 'seq'):
        seq = hdr.seq
        hdr.seq = 0
    try:
        buf = io.BytesIO()
        msg.serialize(buf)
        return hashlib.sha256(buf.getvalue()).hexdigest()[:n]
    finally:
        if seq is not None:
            hdr.seq = seq
