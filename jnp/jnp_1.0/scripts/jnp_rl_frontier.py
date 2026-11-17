# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G2] 자기 지도에서 프론티어 후보 찾기 — ROS 없이 numpy 만 쓴다.
프론티어 = 자유 칸(0≤값<50) 중 모르는 칸(-1)과 4방향으로 붙은 칸. 8방향으로 뭉쳐 덩어리를 만들고 덩어리 중심을 후보로 한다.
중심이 자유 칸이 아니면 덩어리 안에서 중심에 가장 가까운 칸으로 옮긴다. 훑은 지점(visited)·받은 완료 구역 근처(1 m)는 뺀다."""
import math
from collections import deque

import numpy as np

from jnp_rl_api import Candidate


def frontier_cells(grid):
    res, ox, oy, w, h = grid[0]
    d = np.asarray(grid[1], dtype=np.int16).reshape(h, w)
    free = (d >= 0) & (d < 50)
    unk = d == -1
    nb = np.zeros_like(unk)
    nb[1:, :] |= unk[:-1, :]; nb[:-1, :] |= unk[1:, :]; nb[:, 1:] |= unk[:, :-1]; nb[:, :-1] |= unk[:, 1:]
    return free & nb, free, (res, ox, oy, w, h)


def cluster(mask, min_size=5):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    rs, cs = np.nonzero(mask)
    for r0, c0 in zip(rs.tolist(), cs.tolist()):
        if seen[r0, c0]:
            continue
        seen[r0, c0] = True
        q = deque([(r0, c0)]); cells = []
        while q:
            r, c = q.popleft(); cells.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and mask[rr, cc] and not seen[rr, cc]:
                        seen[rr, cc] = True; q.append((rr, cc))
        if len(cells) >= min_size:
            out.append(cells)
    return out


def candidates_from_grid(grid, my_pos, visited=(), exclude_pts=(), exclude_r=1.0, min_size=5):
    """grid = ((res, ox, oy, w, h), data) → Candidate 목록(내 위치에서 가까운 순)."""
    mask, free, (res, ox, oy, w, h) = frontier_cells(grid)
    out = []
    excl = list(visited) + list(exclude_pts)
    for cells in cluster(mask, min_size):
        arr = np.asarray(cells)
        cr, cc = arr[:, 0].mean(), arr[:, 1].mean()
        sx, sy = ox + (cc + 0.5) * res, oy + (cr + 0.5) * res
        if any(math.hypot(sx - ex, sy - ey) < exclude_r for ex, ey in excl):
            continue
        ri, ci = int(round(cr)), int(round(cc))
        if not (0 <= ri < h and 0 <= ci < w and free[ri, ci]):
            d2 = np.floor(((arr[:, 0] - cr) ** 2 + (arr[:, 1] - cc) ** 2) * float(1 << 20))      # [2026-11-01] 같은 거리면 row-major 작은 칸
            k = int(np.lexsort((arr[:, 0] * w + arr[:, 1], d2))[0])
            ri, ci = cells[k]
        x, y = ox + (ci + 0.5) * res, oy + (ri + 0.5) * res
        out.append(Candidate(x=x, y=y, src_x=sx, src_y=sy, dist=math.hypot(x - my_pos[0], y - my_pos[1]), size=len(cells)))
    out.sort(key=lambda c: c.dist)
    return out
