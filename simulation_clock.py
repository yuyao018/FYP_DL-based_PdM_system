"""Thread-safe, interruptible pacing for one engine (1x = eight hours/cycle)."""
import threading
import time

BASE_CYCLE_SECONDS = 8 * 60 * 60
SPEEDS = {1: "1× · 8 hours/cycle", 8: "8× · 1 hour/cycle",
          480: "480× · 1 minute/cycle", 5760: "5,760× · 5 seconds/cycle"}
DEFAULT_SPEED = 5760


class SimulationClock:
    def __init__(self):
        self._condition = threading.Condition()
        self.speed = DEFAULT_SPEED
        self.paused = False
        self.auto_slow = True
        self.condition = "warming up"
        self.cycle = 0
        self._degraded = False
        self.note = "Accelerated simulation"

    def snapshot(self):
        with self._condition:
            return dict(speed=self.speed, paused=self.paused, auto_slow=self.auto_slow,
                        condition=self.condition, cycle=self.cycle, note=self.note)

    def configure(self, *, speed=None, paused=None, auto_slow=None):
        with self._condition:
            if speed is not None:
                if speed not in SPEEDS:
                    raise ValueError("Unsupported simulation speed")
                self.speed = speed
                self.note = "Manual speed selected"
            if paused is not None:
                self.paused = bool(paused)
            if auto_slow is not None:
                enabling = auto_slow and not self.auto_slow
                self.auto_slow = bool(auto_slow)
                if enabling and self._degraded:
                    self.speed = 1
                    self.note = "Automatically slowed to 1× at warning/critical"
            self._condition.notify_all()

    def observe(self, condition, cycle):
        with self._condition:
            degraded = condition in ("warning", "critical")
            if degraded and not self._degraded and self.auto_slow:
                self.speed = 1
                self.note = "Automatically slowed to 1× at warning/critical"
            self._degraded = degraded
            self.condition, self.cycle = condition, cycle
            self._condition.notify_all()

    def wait_cycle(self, stop_event):
        """Accumulate one cycle of active time; speed edits preserve progress.

        Poll stop at most every 250ms, including during an eight-hour wait.
        Pause freezes progress. A cycle already processing finishes before pause.
        """
        with self._condition:
            remaining = float(BASE_CYCLE_SECONDS)
            while not stop_event.is_set():
                if self.paused:
                    self._condition.wait(0.25)
                    continue
                if remaining <= 0:
                    return True
                speed = self.speed
                started = time.monotonic()
                self._condition.wait(min(remaining / speed, 0.25))
                remaining -= (time.monotonic() - started) * speed
            return False
