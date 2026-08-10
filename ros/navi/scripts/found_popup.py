#!/usr/bin/env python3
"""물건찾기 최종 결과 팝업 (2026-08-10 지시): 발견 물체의 YOLO 주석 스냅샷을
타일로 묶어 한 창에 표시. 디스플레이는 표류하므로 후보를 xrandr 로 실측해
첫 접속 가능한 것을 사용 ([[display-13-for-gui]] 절차)."""
import glob
import json
import os
import subprocess

import cv2
import numpy as np


def live_display():
    # ★사용자가 실제 보는 화면 = 현 세션 뷰어(GUI/RViz/gzclient)의 DISPLAY —
    # 디스플레이 표류 대응: /proc 에서 그 env 를 읽어 1순위 후보로 (2026-08-10)
    cands = []
    try:
        out = subprocess.run(['pgrep', '-f',
                              'python3 main.py|^rviz|gzclient'],
                             capture_output=True, text=True, timeout=4)
        import glob as _g
        pids = out.stdout.split()
        for pat in ('python3 main.py', 'gzclient', 'rviz'):
            r2 = subprocess.run(['pgrep', '-f', pat], capture_output=True,
                                text=True, timeout=4)
            pids += r2.stdout.split()
        for p in pids:
            try:
                env = open('/proc/%s/environ' % p, 'rb').read().split(b'\0')
                for e in env:
                    if e.startswith(b'DISPLAY='):
                        d = e.decode()[8:]
                        if d and d not in cands:
                            cands.append(d)
                    if e.startswith(b'XAUTHORITY='):
                        os.environ.setdefault('XAUTHORITY',
                                              e.decode()[11:])
            except Exception:
                continue
    except Exception:
        pass
    if os.environ.get('DISPLAY'):
        cands.append(os.environ['DISPLAY'])
    cands += [':14', ':13', ':10', ':0']
    for d in cands:
        try:
            r = subprocess.run(['xrandr'], env=dict(
                os.environ, DISPLAY=d,
                XAUTHORITY=os.environ.get('XAUTHORITY',
                                          '/root/.Xauthority')),
                capture_output=True, timeout=4)
            if r.returncode == 0:
                return d
        except Exception:
            pass
    return None


def main():
    import sys
    # 인자 모드(발견 즉시 팝업): found_popup.py <이미지> [라벨]
    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        d = live_display()
        if d is None:
            print('found_popup: 디스플레이 없음')
            return
        os.environ['DISPLAY'] = d
        os.environ.setdefault('XAUTHORITY', '/root/.Xauthority')
        img = cv2.imread(sys.argv[1])
        if img is None:
            return
        label = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(sys.argv[1])
        win = 'YOLO: ' + label
        # 하단에 Close 버튼 스트립 합성 (2026-08-10 지시: 영구 보존 + 닫기 버튼)
        h, w = img.shape[:2]
        bar = np.full((56, w, 3), (45, 45, 45), dtype=np.uint8)
        bx0, bx1, by0, by1 = w // 2 - 90, w // 2 + 90, 8, 48
        cv2.rectangle(bar, (bx0, by0), (bx1, by1), (70, 70, 200), -1)
        cv2.putText(bar, 'Close', (bx0 + 55, by0 + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
                    cv2.LINE_AA)
        canvas = np.vstack([img, bar])
        state = {'close': False}

        def _on_mouse(ev, mx, my, flags, param):
            if (ev == cv2.EVENT_LBUTTONUP and my >= h + by0
                    and my <= h + by1 and bx0 <= mx <= bx1):
                state['close'] = True
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, 800, 656)
        cv2.moveWindow(win, 400, 200)
        cv2.imshow(win, canvas)
        cv2.setMouseCallback(win, _on_mouse)
        try:
            cv2.setWindowProperty(win, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass
        cv2.waitKey(200)
        try:    # cv2 4.2 는 TOPMOST 미지원 — X 유틸로 창 전면 인양
            subprocess.run(['wmctrl', '-a', win], timeout=3,
                           env=os.environ)
        except Exception:
            pass
        print(f'found_popup(즉시): {label} (display {d}) — Close 로 닫기')
        # 영구 보존: Close 버튼/ESC/창 파괴로만 닫힘.
        # ★WND_PROP_VISIBLE 은 일부 WM(MobaXterm 계열)에서 항상 0 을 반환해
        # 창이 '번쩍'하고 즉시 닫히던 원인 — AUTOSIZE(-1=파괴)로 판정 (2026-08-10)
        while not state['close']:
            k = cv2.waitKey(200)
            if k in (27, ord('q')):
                break
            try:
                if cv2.getWindowProperty(win, cv2.WND_PROP_AUTOSIZE) < 0:
                    break                     # 창 X 버튼으로 파괴됨
            except Exception:
                break
        cv2.destroyAllWindows()
        return
    snaps = []
    # /found_objects latched JSON 우선 (img 경로 포함), 폴백은 저장 폴더 글롭
    try:
        import rospy
        from std_msgs.msg import String
        rospy.init_node('found_popup', anonymous=True)
        msg = rospy.wait_for_message('/found_objects', String, timeout=5.0)
        for f in json.loads(msg.data):
            if f.get('img') and os.path.exists(f['img']):
                snaps.append((f['img'],
                              f"{f['cls']}  ({f['robot']} 발견, conf {f['conf']})"))
    except Exception:
        pass
    if not snaps:
        for p in sorted(glob.glob(
                '/root/tesla/ros/navi/found_objects/*.jpg')):
            snaps.append((p, os.path.basename(p)))
    if not snaps:
        print('found_popup: 표시할 스냅샷 없음')
        return
    d = live_display()
    if d is None:
        print('found_popup: 접속 가능한 디스플레이 없음')
        return
    os.environ['DISPLAY'] = d
    os.environ.setdefault('XAUTHORITY', '/root/.Xauthority')
    tiles = []
    for path, label in snaps[:6]:
        img = cv2.imread(path)
        if img is None:
            continue
        img = cv2.resize(img, (480, 360))
        cv2.rectangle(img, (0, 330), (480, 360), (30, 30, 30), -1)
        cv2.putText(img, label, (8, 351), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(img)
    if not tiles:
        return
    rows = [np.hstack(tiles[i:i + 2]) if len(tiles[i:i + 2]) == 2
            else np.hstack([tiles[i], np.zeros_like(tiles[i])])
            for i in range(0, len(tiles), 2)]
    canvas = np.vstack(rows)
    win = 'Found Objects (발견 물체)'
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.moveWindow(win, 300, 150)
    cv2.imshow(win, canvas)
    try:
        cv2.setWindowProperty(win, cv2.WND_PROP_TOPMOST, 1)
    except Exception:
        pass
    print(f'found_popup: {len(tiles)}장 표시 (display {d}) — 창을 닫으면 종료')
    while cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) >= 1:
        if cv2.waitKey(200) != -1:
            break
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
