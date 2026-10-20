import threading
import time
import unittest

from request_gate import AccountRequestGate


class AccountRequestGateTests(unittest.TestCase):
    def test_concurrent_workers_share_spacing(self):
        gate = AccountRequestGate(0.03, default_429_cooldown_seconds=0.05)
        start = threading.Barrier(3)
        dispatch_times = []
        lock = threading.Lock()

        def worker():
            start.wait(timeout=1)
            self.assertTrue(gate.acquire())
            with lock:
                dispatch_times.append(time.monotonic())

        workers = [threading.Thread(target=worker) for _ in range(3)]
        for worker_thread in workers:
            worker_thread.start()
        for worker_thread in workers:
            worker_thread.join(timeout=2)
            self.assertFalse(worker_thread.is_alive())

        self.assertEqual(len(dispatch_times), 3)
        ordered = sorted(dispatch_times)
        self.assertGreaterEqual(ordered[1] - ordered[0], 0.025)
        self.assertGreaterEqual(ordered[2] - ordered[1], 0.025)

    def test_admission_callback_is_inside_the_spacing_reservation(self):
        gate = AccountRequestGate(0.04, default_429_cooldown_seconds=0.05)
        callback_finished = []
        dispatches = []

        def slow_callback():
            time.sleep(0.03)
            callback_finished.append(time.monotonic())
            return True

        first = threading.Thread(
            target=lambda: gate.acquire(on_admitted=slow_callback)
        )
        first.start()
        first.join(timeout=1)
        self.assertFalse(first.is_alive())

        second = threading.Thread(
            target=lambda: gate.acquire(on_admitted=lambda: dispatches.append(time.monotonic()) or True)
        )
        second.start()
        second.join(timeout=1)
        self.assertFalse(second.is_alive())
        self.assertEqual(len(dispatches), 1)
        self.assertGreaterEqual(dispatches[0] - callback_finished[0], 0.035)

    def test_shared_cooldown_honors_and_rechecks_extended_deadline(self):
        gate = AccountRequestGate(0.005, default_429_cooldown_seconds=0.04)
        self.assertTrue(gate.acquire())
        self.assertEqual(gate.cool_down(0.08), 0.08)
        start = time.monotonic()
        admitted = []

        waiter = threading.Thread(
            target=lambda: admitted.append((gate.acquire(), time.monotonic()))
        )
        waiter.start()
        time.sleep(0.03)
        self.assertEqual(gate.cool_down(0.15), 0.15)
        waiter.join(timeout=1)
        self.assertFalse(waiter.is_alive())
        self.assertTrue(admitted[0][0])
        self.assertGreaterEqual(admitted[0][1] - start, 0.17)

    def test_missing_retry_after_uses_conservative_shared_cooldown(self):
        gate = AccountRequestGate(0.01, default_429_cooldown_seconds=0.04)
        self.assertEqual(gate.cool_down(None), 0.04)
        start = time.monotonic()
        self.assertTrue(gate.acquire())
        self.assertGreaterEqual(time.monotonic() - start, 0.035)

    def test_cancelled_gate_waiter_is_removed_without_dispatch(self):
        gate = AccountRequestGate(0.15, default_429_cooldown_seconds=0.04)
        self.assertTrue(gate.acquire())
        cancelled = threading.Event()
        result = []
        waiter = threading.Thread(target=lambda: result.append(gate.acquire(cancelled)))
        waiter.start()
        time.sleep(0.02)
        started = time.monotonic()
        cancelled.set()
        waiter.join(timeout=0.2)
        self.assertFalse(waiter.is_alive())
        self.assertEqual(result, [False])
        self.assertLess(time.monotonic() - started, 0.2)


if __name__ == "__main__":
    unittest.main()
