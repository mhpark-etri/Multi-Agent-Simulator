#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Watch captured ROS camera frames and run light_fire_pkg without reloading weights.

Launched by dlgROSI2I.py with a dedicated 'lightfire' Python interpreter.
Only files created after startup are processed. Send 'DRAIN\\n' on stdin to finish queued frames and exit.
This worker deliberately has no ROS, Qt, or cv_bridge dependency.
"""

import argparse
import os
from pathlib import Path
import select
import sys
import time
import traceback

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
POLL_SECONDS = 0.20


def image_files(directory):
    """Only completed-looking image paths; temporary dot files are ignored."""
    try:
        return sorted(
            (path for path in directory.iterdir()
             if path.is_file() and not path.name.startswith(".")
             and path.suffix.lower() in IMAGE_EXTENSIONS),
            key=lambda path: path.name,
        )
    except FileNotFoundError:
        return []


def drain_requested():
    """Nonblocking DRAIN/STOP command over stdin (Linux)."""
    try:
        if select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            return not line or line.strip().upper() in ("STOP", "DRAIN")
    except (ValueError, OSError):
        # stdin may be closed by the launcher during shutdown.
        return True
    return False


def run_worker(input_dir, output_dir, package_dir, device="cuda"):
    input_dir = Path(input_dir).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    package_dir = Path(package_dir).expanduser().resolve()
    if not (package_dir / "model.py").is_file():
        raise FileNotFoundError("light_fire_pkg/model.py not found: {}".format(package_dir))
    if not input_dir.is_dir():
        raise NotADirectoryError("Capture directory does not exist: {}".format(input_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Take the initial snapshot BEFORE any expensive PyTorch/SAM2 imports.
    # Existing images are not reprocessed. The GUI starts ROS capture only
    # after it receives this readiness marker, so no new frames are missed.
    processed = {p.name for p in image_files(input_dir)}
    stable_stat = {}  # name -> (file size, mtime_ns), ensures complete external writes
    print("I2I_WATCHING", flush=True)
    print("[I2I] Watching {} ({} pre-existing files ignored)".format(
        input_dir, len(processed)), flush=True)

    # Import heavy dependencies only inside the dedicated Conda process.
    sys.path.insert(0, str(package_dir))
    import cv2
    from model import RTLightFire

    print("[I2I] Loading fire model once (device={})...".format(device), flush=True)
    engine = RTLightFire(device=device)
    print("I2I_MODEL_READY", flush=True)

    draining = False
    completed = 0
    failed = 0
    drain_total = 0
    drain_done = 0
    while True:
        # DRAIN starts only after the ROS capture thread and any in-flight ROS
        # callback have finished saving. The pending count is therefore fixed.
        if drain_requested() and not draining:
            draining = True
            pending_at_drain = [p for p in image_files(input_dir) if p.name not in processed]
            drain_total = len(pending_at_drain)
            print("[I2I] DRAINING: finishing all queued fire images...", flush=True)
            print("I2I_DRAIN_TOTAL {}".format(drain_total), flush=True)
        # Sequential processing keeps temporal smoke tracking and fire shape.
        # Each scan observes new files; on-disk inputs are not held in RAM.
        pending = [p for p in image_files(input_dir) if p.name not in processed]
        if not pending:
            if draining:
                break
            time.sleep(POLL_SECONDS)
            continue

        next_file = pending[0]
        try:
            stat = next_file.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
        except FileNotFoundError:
            time.sleep(POLL_SECONDS)
            continue

        if stable_stat.get(next_file.name) != signature:
            stable_stat[next_file.name] = signature
            time.sleep(POLL_SECONDS)
            continue

        try:
            input_img = cv2.imread(str(next_file), cv2.IMREAD_COLOR)
            if input_img is None:
                raise ValueError("Cannot decode capture image")

            generated_img = engine.step(input_img)
            final_path = output_dir / "{}-I2I{}".format(
                next_file.stem, next_file.suffix.lower()
            )
            # Atomic rename: consumers never see a half-written output image.
            partial_path = output_dir / ("." + final_path.stem + ".tmp" + final_path.suffix)
            try:
                if not cv2.imwrite(str(partial_path), generated_img):
                    raise OSError("cv2.imwrite returned False")
                os.replace(str(partial_path), str(final_path))
            finally:
                try:
                    partial_path.unlink(missing_ok=True)
                except OSError:
                    pass
            completed += 1
            print("[I2I] DONE {} -> {}".format(next_file.name, final_path.name), flush=True)
        except Exception as exc:
            # A single malformed image must not stop the entire stream.
            failed += 1
            print("[I2I] ERROR {}: {}".format(next_file.name, exc), file=sys.stderr, flush=True)
        finally:
            processed.add(next_file.name)
            stable_stat.pop(next_file.name, None)
            if draining:
                drain_done += 1
                print("I2I_DRAIN_PROGRESS {} {}".format(drain_done, drain_total), flush=True)

    print("[I2I] STOPPED: converted={}, failed={}".format(completed, failed), flush=True)
    # Report failed conversions to the GUI rather than silently claiming success.
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description="Live light_fire_pkg capture directory worker")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    arguments = parser.parse_args()
    try:
        return run_worker(arguments.input_dir, arguments.output_dir,
                          arguments.package_dir, arguments.device)
    except Exception as exc:
        print("[I2I] FATAL: {}".format(exc), file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
