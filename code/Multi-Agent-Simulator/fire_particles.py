#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gazebo Classic / ROS1: fire sources configured by the Qt Fire Editor.

Run standalone with defaults (one fire source)::

    python3 fire_particles.py

When started from MainWindow, FIRE_PARTICLES_CONFIG_JSON contains the editor's
list of fire sources and the original Start-button timestamp.  There are no
command-line arguments.  ``particle_template_grey.sdf`` must be beside THIS
file, regardless of the shell's current working directory.

Ctrl+C, SIGTERM, or natural expiration stops the animation and deletes only
models belonging to this invocation; Gazebo and other models are untouched.
"""

import json
import math
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event, Lock


# Public configuration (ROS-independent; testable without Gazebo)
SDF_FILENAME = "particle_template_grey.sdf"
SDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), SDF_FILENAME)
FIRE_CONFIG_ENV = "FIRE_PARTICLES_CONFIG_JSON"
MAX_FIRE_SOURCES = 10
MIN_MODELS_PER_SOURCE = 15
MAX_MODELS_PER_SOURCE = 30
MAX_TOTAL_MODELS = 300
DEFAULT_SPREAD_SCALE = 0.3

# Spawn models underground, then reposition them with the Gazebo ROS API.
SPAWN_X, SPAWN_Y, SPAWN_Z = 0.0, 0.0, -10.0
MAX_WORKERS = min(os.cpu_count() or 4, 12)
SPAWN_RETRIES = 2
SPAWN_COMMAND_TIMEOUT = 45  # seconds per CLI invocation

# Particle positions are set ONCE at birth with linear velocity.  Gazebo's
# physics then moves each particle continuously until it is recycled.  This
# avoids sending one ROS model-state message per particle per rendered frame.
EMITTER_TICK_HZ = 40
PARTICLE_LIFESPAN = 0.90  # seconds of continuous physics motion
EMISSION_RATE_WEAK = 2.0    # emissions / second, intensity 0
EMISSION_RATE_STRONG = 28.0  # emissions / second, intensity 100
PERFORMANCE_LOG_SECONDS = 5.0
RAMP_SECONDS_SLOW = 30.0    # gradualness=0: slow rise to full fire
RAMP_SECONDS_FAST = 0.5    # gradualness=100: quick rise to full fire
FADE_SECONDS = 8.0         # fade during last min(8 s, 20% of duration)
FADE_PORTION = 0.20

_active_runtime = None


def _log(message, error=False):
    print(message, file=sys.stderr if error else sys.stdout, flush=True)


def model_count_for_intensity(intensity):
    """Pool size for one source; 0 -> 15, 100 -> 30."""
    return MIN_MODELS_PER_SOURCE + int(round(
        (MAX_MODELS_PER_SOURCE - MIN_MODELS_PER_SOURCE) * intensity / 100.0
    ))


def smoothstep(progress):
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def fire_envelope(elapsed_since_ignition, duration, gradualness):
    """0..1 fire volume: gradual ramp-up + smooth fade near the end.

    Gradualness only controls the rise speed: high (100) is quicker.  The
    fade occupies at most the last 8 seconds or last 20% of the duration.
    """
    if duration <= 0 or elapsed_since_ignition <= 0 or elapsed_since_ignition >= duration:
        return 0.0
    gradualness = max(0.0, min(100.0, float(gradualness))) / 100.0
    ramp_sec = min(duration * 0.45,
                   RAMP_SECONDS_SLOW + (RAMP_SECONDS_FAST - RAMP_SECONDS_SLOW) * gradualness)
    fade_sec = min(FADE_SECONDS, duration * FADE_PORTION)
    rise = smoothstep(elapsed_since_ignition / max(ramp_sec, 0.001))
    fall = smoothstep((duration - elapsed_since_ignition) / max(fade_sec, 0.001))
    return min(rise, fall)


def _numeric(value, label, min_value=None, max_value=None):
    # Qt supplies finite ints/floats; reject bad hand-edited environment JSON.
    if isinstance(value, bool):
        raise ValueError("{} must be numeric".format(label))
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise ValueError("{} must be numeric".format(label))
    if not math.isfinite(number):
        raise ValueError("{} must be finite".format(label))
    if min_value is not None and number < min_value:
        raise ValueError("{} must be >= {}".format(label, min_value))
    if max_value is not None and number > max_value:
        raise ValueError("{} must be <= {}".format(label, max_value))
    return number


def validate_fire_sources(raw_sources):
    """Normalize the widget GetFireData() contract and reject invalid plans."""
    if not isinstance(raw_sources, list) or not 1 <= len(raw_sources) <= MAX_FIRE_SOURCES:
        raise ValueError("Fire source count must be 1..{}".format(MAX_FIRE_SOURCES))
    sources = []
    seen_ids = set()
    for row, item in enumerate(raw_sources):
        if not isinstance(item, dict):
            raise ValueError("Fire source #{} must be an object".format(row))
        fire_id = int(_numeric(item.get('id', row), 'id'))
        if fire_id in seen_ids:
            raise ValueError("Duplicate fire source ID: {}".format(fire_id))
        seen_ids.add(fire_id)
        position = item.get('position', {})
        if not isinstance(position, dict):
            raise ValueError("Source {} position must be an object".format(fire_id))
        coordinates = {
            axis: _numeric(position.get(axis), 'position.' + axis)
            for axis in ('x', 'y', 'z')
        }
        start = _numeric(item.get('ignition_start_sec'), 'ignition_start_sec', 0)
        duration = _numeric(item.get('ignition_end_sec'), 'ignition_end_sec', 0)
        intensity = _numeric(item.get('ignition_intensity'), 'ignition_intensity', 0, 100)
        gradualness = _numeric(item.get('ignition_gradualness'), 'ignition_gradualness', 0, 100)
        sources.append({
            'id': fire_id, 'position': coordinates,
            'ignition_start_sec': start,
            'ignition_end_sec': duration,
            'ignition_intensity': intensity,
            'ignition_gradualness': gradualness,
            'model_count': model_count_for_intensity(intensity),
        })
    model_total = sum(src['model_count'] for src in sources)
    if model_total > MAX_TOTAL_MODELS:
        raise ValueError("Model budget exceeded: {} > {}".format(model_total, MAX_TOTAL_MODELS))
    return sources


def load_configuration():
    """Load Qt's environment JSON or one standalone default source."""
    raw = os.environ.get(FIRE_CONFIG_ENV)
    if raw:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("{} must contain a JSON object".format(FIRE_CONFIG_ENV))
        sources = data.get('fires')
        click_unix_sec = _numeric(data.get('start_unix_sec'), 'start_unix_sec', 0)
    else:
        sources = [{
            'id': 0,
            'position': {'x': 0, 'y': 0, 'z': 0},
            'ignition_start_sec': 0,
            'ignition_end_sec': 60,
            'ignition_intensity': 50,
            'ignition_gradualness': 80,
        }]
        click_unix_sec = time.time()
    return validate_fire_sources(sources), click_unix_sec


def validate_prerequisites():
    if not os.path.isfile(SDF_FILE):
        raise FileNotFoundError(
            "[경고] '{}' 파일이 없습니다.\n{}\n"
            "fire_particles.py와 같은 폴더에 SDF 파일을 배치하세요.".format(
                SDF_FILENAME, SDF_FILE
            )
        )
    if not shutil.which('rosrun'):
        raise RuntimeError("'rosrun'을 찾을 수 없습니다. ROS1 setup.bash를 적용하세요.")


def _sdf_tag(element):
    """Return the tag without an optional XML namespace."""
    return element.tag.rsplit('}', 1)[-1]


def _set_sdf_child(parent, tag, value):
    """Edit an SDF field in-place without losing XML namespaces."""
    child = next((node for node in parent if _sdf_tag(node) == tag), None)
    if child is None:
        namespace = parent.tag.split('}', 1)[0] + '}' if '}' in parent.tag else ''
        child = ET.SubElement(parent, namespace + tag)
    child.text = value


def prepare_motion_sdf(sdf_file):
    """Create a temporary SDF suitable for continuous Gazebo-driven motion.

    The original SDF is never modified.  Particle bodies must be non-static,
    gravity-free, and non-colliding; otherwise they fall, stick or bounce into
    other simulation objects instead of following their ignition trajectories.
    Place the temp file next to the original to preserve relative asset paths.
    """
    tree = ET.parse(sdf_file)
    root = tree.getroot()
    models = [node for node in root.iter() if _sdf_tag(node) == 'model']
    links = [node for node in root.iter() if _sdf_tag(node) == 'link']
    if not models or not links:
        raise ValueError('Fire SDF requires at least one <model> and <link>.')

    for model in models:
        _set_sdf_child(model, 'static', 'false')
        _set_sdf_child(model, 'allow_auto_disable', 'false')

    collision_count = 0
    for link in links:
        _set_sdf_child(link, 'gravity', 'false')
        _set_sdf_child(link, 'kinematic', 'false')
        # Visual fire particles should not collide with robots, furniture, etc.
        for child in list(link):
            if _sdf_tag(child) == 'collision':
                link.remove(child)
                collision_count += 1
        velocity_decay = next((c for c in link if _sdf_tag(c) == 'velocity_decay'), None)
        if velocity_decay is not None:
            _set_sdf_child(velocity_decay, 'linear', '0')
            _set_sdf_child(velocity_decay, 'angular', '0')

    try:
        with tempfile.NamedTemporaryFile(
                mode='wb', prefix='.fire_motion_', suffix='.sdf',
                dir=os.path.dirname(os.path.abspath(sdf_file)), delete=False) as output:
            temp_path = output.name
            tree.write(output, encoding='utf-8', xml_declaration=True)
    except Exception:
        # The NamedTemporaryFile may have already been created when writing fails.
        if 'temp_path' in locals():
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise
    _log('[Fire] Using temporary motion SDF (gravity off; {} collisions disabled).'.format(
        collision_count))
    return temp_path


def wait_for_gazebo_service(rospy, service_name, stop_event, timeout_sec):
    """Service readiness wait that can be cancelled immediately by SIGTERM."""
    deadline = time.monotonic() + timeout_sec
    last_error = None
    while not stop_event.is_set() and not rospy.is_shutdown():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError('Timed out waiting for {}: {}'.format(
                service_name, last_error or 'no response'))
        try:
            rospy.wait_for_service(service_name, timeout=min(1.0, remaining))
            return True
        except Exception as exc:
            last_error = exc
    return False


def spawn_with_retries(model_name, stop_event, spawn_sdf_file):
    """Spawn only models with a unique run prefix (never touch existing ones)."""
    command = [
        'rosrun', 'gazebo_ros', 'spawn_model', '-file', spawn_sdf_file, '-sdf',
        '-model', model_name, '-x', str(SPAWN_X), '-y', str(SPAWN_Y),
        '-z', str(SPAWN_Z),
    ]
    last_error = ''
    for attempt in range(SPAWN_RETRIES + 1):
        if stop_event.is_set():
            return False, 'cancelled'
        try:
            proc = subprocess.run(command, capture_output=True, text=True,
                                  timeout=SPAWN_COMMAND_TIMEOUT)
            if proc.returncode == 0:
                return True, ''
            last_error = 'exit {}: {}'.format(
                proc.returncode, (proc.stderr or proc.stdout or '').strip()[:260])
        except (OSError, subprocess.TimeoutExpired) as exc:
            last_error = str(exc)
        if attempt < SPAWN_RETRIES and stop_event.wait(min(2 ** (attempt + 1), 5)):
            return False, 'cancelled'
    return False, last_error


def spawn_all_models(runtime, sources, spawn_sdf_file):
    """Create all model pools, report partial failures and support cancellation."""
    tasks = []
    serial = 1
    for source in sources:
        source['model_names'] = [
            '{}{:03d}'.format(runtime.model_prefix, number)
            for number in range(serial, serial + source['model_count'])
        ]
        serial += source['model_count']
        tasks.extend(source['model_names'])

    _log('[Spawn] {} fire sources; spawning {} / {} maximum models (workers={}).'.format(
        len(sources), len(tasks), MAX_TOTAL_MODELS, min(MAX_WORKERS, len(tasks))))
    failures = []
    runtime.spawn_finished.clear()
    try:
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tasks))) as executor:
            futures = {executor.submit(spawn_with_retries, name, runtime.stop_event, spawn_sdf_file): name
                       for name in tasks}
            for count, future in enumerate(as_completed(futures), start=1):
                name = futures[future]
                try:
                    ok, error = future.result()
                except Exception as exc:
                    ok, error = False, str(exc)
                if ok:
                    runtime.record_spawned(name)
                    _log('[Spawn] Created model {}.'.format(name))
                else:
                    failures.append((name, error))
                if count % 20 == 0 or count == len(tasks):
                    _log('[Spawn] {}/{} completed'.format(count, len(tasks)))
    finally:
        runtime.spawn_finished.set()

    if runtime.stop_event.is_set():
        return False
    if failures:
        for name, error in failures[:8]:
            _log('[Spawn FAILED] {}: {}'.format(name, error), error=True)
        raise RuntimeError('{} particle models failed to spawn; cleaning up.'.format(len(failures)))
    return True


class FireEmitter:
    """Schedule ignition; Gazebo handles each particle's continuous motion."""

    def __init__(self, sources, runtime, model_state_type, model_publisher):
        self.sources = sources
        self.runtime = runtime
        self.model_state_type = model_state_type
        self.publisher = model_publisher
        self.rng = random.Random()
        self._published = 0
        for source in self.sources:
            source['_available'] = deque(source['model_names'])
            source['_active'] = {}  # model name -> wall-clock recycle deadline
            source['_emission_credit'] = 0.0
            source['_started'] = False
            source['_ended'] = False

    def _publish(self, name, x, y, z, vx=0.0, vy=0.0, vz=0.0):
        """Send one pose/velocity update; no per-frame ROS messages."""
        msg = self.model_state_type()
        msg.model_name = name
        msg.reference_frame = 'world'
        msg.pose.orientation.w = 1.0
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = z
        msg.twist.linear.x = vx
        msg.twist.linear.y = vy
        msg.twist.linear.z = vz
        self.publisher.publish(msg)
        self._published += 1

    def _hide(self, name):
        # Zero the twist explicitly, otherwise this model may keep drifting
        # underground while sitting in its reusable pool.
        self._publish(name, SPAWN_X, SPAWN_Y, SPAWN_Z)

    def _new_particle(self, source, now, envelope):
        available = source['_available']
        if not available:
            return
        name = available.popleft()
        intensity = source['ignition_intensity'] / 100.0
        scale = 0.16 + 0.84 * intensity
        power = 0.20 + 0.80 * envelope
        spread = DEFAULT_SPREAD_SCALE * scale * power
        dx = self.rng.uniform(-spread, spread)
        dy = self.rng.uniform(-spread, spread)
        low_vz = 0.12 + 0.30 * intensity
        high_vz = 0.45 + 2.35 * intensity
        vz = self.rng.uniform(low_vz, high_vz) * power
        xyz = source['position']
        self._publish(
            name,
            xyz['x'] + self.rng.uniform(-0.015, 0.015),
            xyz['y'] + self.rng.uniform(-0.015, 0.015),
            xyz['z'] + self.rng.uniform(0.0, 0.07),
            dx / PARTICLE_LIFESPAN, dy / PARTICLE_LIFESPAN, vz,
        )
        source['_active'][name] = now + PARTICLE_LIFESPAN

    def _recycle_expired(self, source, now):
        # Check lifetime without sending intermediate poses.  Gazebo itself
        # interpolates the motion at its physics / rendering update rate.
        for name, deadline in list(source['_active'].items()):
            if now >= deadline:
                self._hide(name)
                del source['_active'][name]
                source['_available'].append(name)

    def _extinguish(self, source):
        for name in list(source['_active']):
            self._hide(name)
        source['_active'].clear()
        source['_ended'] = True
        _log('[Fire] ID {} extinguished.'.format(source['id']))

    def run(self, start_monotonic):
        """Return automatically after all ignition intervals have elapsed."""
        last_frame = time.monotonic()
        log_at = last_frame
        max_frame_delay = 0.0
        last_published = self._published
        while not self.runtime.stop_event.is_set():
            now = time.monotonic()
            frame_delay = max(0.0, now - last_frame)
            max_frame_delay = max(max_frame_delay, frame_delay)
            dt = min(0.20, frame_delay)
            last_frame = now
            all_ended = True
            for source in self.sources:
                if source['_ended']:
                    continue
                all_ended = False
                since_click = now - start_monotonic
                since_ignition = since_click - source['ignition_start_sec']
                if since_ignition < 0:
                    continue
                if not source['_started']:
                    source['_started'] = True
                    _log('[Fire] ID {} ignition at ({}, {}, {}), intensity={}, gradualness={}.'.format(
                        source['id'], source['position']['x'], source['position']['y'],
                        source['position']['z'], source['ignition_intensity'],
                        source['ignition_gradualness']))
                    if since_ignition > 0.75:
                        _log('[Fire WARNING] ID {} ignition is {:.1f}s late due to model setup.'.format(
                            source['id'], since_ignition), error=True)
                duration = source['ignition_end_sec']
                if duration <= 0 or since_ignition >= duration:
                    self._extinguish(source)
                    continue

                envelope = fire_envelope(since_ignition, duration,
                                         source['ignition_gradualness'])
                intensity = source['ignition_intensity'] / 100.0
                peak_rate = EMISSION_RATE_WEAK + (
                    EMISSION_RATE_STRONG - EMISSION_RATE_WEAK) * intensity
                self._recycle_expired(source, now)
                source['_emission_credit'] = min(2.0, source['_emission_credit'] +
                                                  dt * peak_rate * envelope)
                while source['_emission_credit'] >= 1.0 and source['_available']:
                    self._new_particle(source, now, envelope)
                    source['_emission_credit'] -= 1.0

            if now - log_at >= PERFORMANCE_LOG_SECONDS:
                elapsed = max(now - log_at, 1e-6)
                active = sum(len(src['_active']) for src in self.sources)
                sent = self._published - last_published
                _log('[Fire Perf] active={}, ROS commands={:.0f}/s, worst tick={:.3f}s'.format(
                    active, sent / elapsed, max_frame_delay))
                last_published = self._published
                max_frame_delay = 0.0
                log_at = now

            if all_ended or all(src['_ended'] for src in self.sources):
                _log('[Fire] All sources extinguished; removing particle models.')
                return
            self.runtime.stop_event.wait(1.0 / EMITTER_TICK_HZ)


class FireParticleRuntime:
    """Owns only models with this invocation's unique prefix."""

    def __init__(self, rospy_module):
        self.rospy = rospy_module
        # Initialized here as a fallback; refined after inspecting Gazebo names.
        self.model_prefix = 'fire_{}_'.format(uuid.uuid4().hex[:6])
        self.stop_event = Event()
        self.spawn_finished = Event()
        self.spawn_finished.set()
        self.emitter_finished = Event()
        self.emitter_finished.set()
        self.cleanup_lock = Lock()
        self.models_lock = Lock()
        self.created_models = set()
        self.deleted_models = set()
        self.delete_model = None
        self.get_world_properties = None

    def select_short_model_prefix(self):
        """Choose short names, avoiding prefixes already present in the world."""
        existing_names = None
        if self.get_world_properties is not None:
            try:
                response = self.get_world_properties()
                if response.success:
                    existing_names = set(response.model_names)
            except Exception as exc:
                _log('[Fire WARNING] Could not check existing model names: {}'.format(exc),
                     error=True)
        # With known world names a four-digit session token is sufficient; if
        # inspection fails use six hex characters to minimize collision risk.
        token_length = 4 if existing_names is not None else 6
        for _ in range(1000):
            candidate = 'fire_{}_'.format(uuid.uuid4().hex[:token_length])
            if existing_names is None or not any(
                    name.startswith(candidate) for name in existing_names):
                self.model_prefix = candidate
                _log('[Fire] Short model names: {}001, {}002, ...'.format(
                    candidate, candidate))
                return
        raise RuntimeError('Could not allocate a free fire model name prefix.')

    def record_spawned(self, name):
        with self.models_lock:
            self.created_models.add(name)

    def request_stop(self):
        self.stop_event.set()

    def stop(self):
        """Stop animation and delete this run's models. Safe to repeat."""
        self.request_stop()
        self.spawn_finished.wait()
        self.emitter_finished.wait()
        with self.cleanup_lock:
            with self.models_lock:
                names = set(self.created_models - self.deleted_models)
            # Recover from a CLI spawn that succeeded in Gazebo but returned
            # failure/timeout locally.  Unique names prevent other-model loss.
            if self.get_world_properties is not None:
                try:
                    response = self.get_world_properties()
                    if response.success:
                        names.update(name for name in response.model_names
                                     if name.startswith(self.model_prefix)
                                     and name not in self.deleted_models)
                except Exception as exc:
                    _log('[Cleanup WARNING] Could not inspect world: {}'.format(exc), error=True)
            if not names:
                _log('[Cleanup] No models belonging to this fire process remain.')
                return 0
            if self.delete_model is None:
                _log('[Cleanup WARNING] /gazebo/delete_model is unavailable; {} models remain.'.format(
                    len(names)), error=True)
                return 0
            deleted = 0
            _log('[Cleanup] Deleting {} models with prefix {}...'.format(
                len(names), self.model_prefix))
            for idx, name in enumerate(sorted(names), start=1):
                try:
                    response = self.delete_model(name)
                    if response.success:
                        deleted += 1
                        self.deleted_models.add(name)
                    else:
                        _log('[Cleanup FAILED] {}: {}'.format(
                            name, getattr(response, 'status_message', 'unknown')), error=True)
                except Exception as exc:
                    _log('[Cleanup FAILED] {}: {}'.format(name, exc), error=True)
                if idx % 25 == 0 or idx == len(names):
                    _log('[Cleanup] {}/{} processed'.format(idx, len(names)))
            _log('[Cleanup] Removed {}/{} models.'.format(deleted, len(names)))
            return deleted


def stop_fire_particles():
    """Stop + remove models from the SAME Python process (SIGTERM also works)."""
    if _active_runtime is None:
        _log('[Cleanup] No active fire process.')
        return 0
    return _active_runtime.stop()


def main():
    global _active_runtime
    if len(sys.argv) > 1:
        raise ValueError('No command-line arguments are accepted: python3 fire_particles.py')
    sources, start_unix_sec = load_configuration()
    validate_prerequisites()
    try:
        import rospy
        from gazebo_msgs.msg import ModelState
        from gazebo_msgs.srv import DeleteModel, GetWorldProperties
    except ImportError as exc:
        raise RuntimeError('ROS1 rospy/gazebo_msgs modules are required.') from exc

    rospy.init_node('multi_fire_particle_emitter', anonymous=True, disable_signals=True)
    runtime = FireParticleRuntime(rospy)
    _active_runtime = runtime
    rospy.on_shutdown(runtime.request_stop)
    old_handlers = {}

    def on_stop_signal(signum, _frame):
        _log('[Fire] Signal {}: stopping fire and removing its models...'.format(signum))
        runtime.request_stop()

    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            old_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, on_stop_signal)

        _log('[Fire] Waiting for Gazebo ROS services...')
        if not wait_for_gazebo_service(
                rospy, '/gazebo/spawn_sdf_model', runtime.stop_event, 60):
            return
        if not wait_for_gazebo_service(
                rospy, '/gazebo/delete_model', runtime.stop_event, 60):
            return
        runtime.delete_model = rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)
        # Discover unexpected successful spawns when the CLI exits abnormally.
        try:
            if wait_for_gazebo_service(
                    rospy, '/gazebo/get_world_properties', runtime.stop_event, 3):
                runtime.get_world_properties = rospy.ServiceProxy(
                    '/gazebo/get_world_properties', GetWorldProperties)
        except Exception:
            pass
        if runtime.stop_event.is_set() or rospy.is_shutdown():
            return

        # No high-frequency model teleports: publish at birth/recycle only.
        # Keep the queue small to avoid several seconds of stale model states.
        publisher = rospy.Publisher('/gazebo/set_model_state', ModelState, queue_size=100)
        wait_until = time.monotonic() + 8.0
        while (publisher.get_num_connections() == 0 and
               time.monotonic() < wait_until and not runtime.stop_event.is_set()):
            runtime.stop_event.wait(0.10)
        if publisher.get_num_connections() == 0 and not runtime.stop_event.is_set():
            raise RuntimeError('Gazebo does not subscribe to /gazebo/set_model_state.')

        runtime.select_short_model_prefix()
        # The original SDF is kept intact.  A temporary, collision-free SDF
        # ensures Gazebo can move particles smoothly using twist velocities.
        motion_sdf = prepare_motion_sdf(SDF_FILE)
        try:
            if not spawn_all_models(runtime, sources, motion_sdf):
                return
        finally:
            try:
                os.remove(motion_sdf)
            except OSError as exc:
                _log('[Fire WARNING] Could not remove temporary SDF: {}'.format(exc),
                     error=True)
        if runtime.stop_event.is_set() or rospy.is_shutdown():
            return

        _log('[Fire] All models ready. Physics-driven particle motion enabled.')
        _log('[Fire] Per-source start/end times are measured from GUI Start.')
        # Translate GUI wall clock to monotonic timer once.  If loading the SDF
        # took longer than a start delay, log a late ignition rather than
        # pretending the requested delay was met.
        start_monotonic = time.monotonic() - (time.time() - start_unix_sec)
        emitter = FireEmitter(sources, runtime, ModelState, publisher)
        runtime.emitter_finished.clear()
        try:
            emitter.run(start_monotonic)
        finally:
            runtime.emitter_finished.set()
    finally:
        try:
            stop_fire_particles()  # while Gazebo is still running
        finally:
            if not rospy.is_shutdown():
                rospy.signal_shutdown('fire particle session finished')
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
            _active_runtime = None


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        _log('[Fire] Interrupted.', error=True)
        sys.exit(130)
    except Exception as exc:
        _log('[Fire ERROR] {}'.format(exc), error=True)
        sys.exit(1)
