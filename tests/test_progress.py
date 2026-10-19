import io
import time
import unittest

from progress import ProgressReporter


class TTYStringIO(io.StringIO):
    def isatty(self):
        return True


class ProgressReporterTests(unittest.TestCase):
    def test_prints_elapsed_eta_output_rate_and_per_model_name(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output)
        reporter.register_model("openai/gpt-6-luna", "low", 10)
        time.sleep(0.01)
        reporter(
            {
                "event": "case_finished",
                "model_id": "openai/gpt-6-luna",
                "reasoning_effort": "low",
                "case_id": "d4-1009",
                "outcome": "correct",
                "completion_tokens": 50,
                "total_cases": 10,
            }
        )
        text = output.getvalue()
        self.assertIn("openai/gpt-6-luna | low", text)
        self.assertIn("1/10", text)
        self.assertIn("elapsed", text)
        self.assertIn("ETA", text)
        self.assertIn("out", text)
        self.assertIn("tok/s", text)
        self.assertIn("C1", text)

    def test_failure_usage_is_included_in_output_token_rate(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output)
        reporter.register_model("provider/model", "low", 2)
        reporter(
            {
                "event": "attempt_failed",
                "model_id": "provider/model",
                "reasoning_effort": "low",
                "case_id": "d4-1009",
                "attempt_number": 1,
                "max_attempts": 3,
                "completion_tokens": 12,
                "reason": "HTTP 503",
            }
        )
        self.assertIn("attempt 1/3 failed", output.getvalue())
        self.assertIn("tok/s", output.getvalue())

    def test_tty_dashboard_redraws_in_place_instead_of_scrolling(self):
        output = TTYStringIO()
        reporter = ProgressReporter(stream=output)
        reporter.set_batch_total(1)
        reporter.register_model("openai/gpt-6-luna", "low", 2)
        reporter(
            {
                "event": "case_finished",
                "model_id": "openai/gpt-6-luna",
                "reasoning_effort": "low",
                "case_id": "d4-1009",
                "outcome": "correct",
                "completion_tokens": 12,
            }
        )
        text = output.getvalue()
        self.assertIn("[", text)
        self.assertIn("█", text)
        self.assertIn("\x1b[2A", text)
        self.assertIn("openai/gpt-6-luna | low", text)

    def test_redirected_progress_is_throttled(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output)
        reporter.set_batch_total(1)
        reporter.register_model("openai/model", "low", 100)
        for index in range(100):
            reporter(
                {
                    "event": "case_finished",
                    "model_id": "openai/model",
                    "reasoning_effort": "low",
                    "case_id": f"case-{index}",
                    "outcome": "correct",
                    "completion_tokens": 1,
                }
            )
        reporter.model_finished("openai/model", "low", success=True)
        self.assertLessEqual(len(output.getvalue().splitlines()), 50)

    def test_heartbeat_reports_a_slow_nonstreaming_request(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output, heartbeat_interval=0.1, force_tty=True)
        reporter.register_model("provider/slow-model", "medium", 2)
        reporter(
            {
                "event": "attempt_started",
                "model_id": "provider/slow-model",
                "reasoning_effort": "medium",
                "case_id": "d10-1000000007",
                "attempt_number": 1,
                "max_attempts": 3,
            }
        )
        time.sleep(0.25)
        reporter.close()
        self.assertIn("waiting for model response", output.getvalue())
        self.assertIn("ETA", output.getvalue())


if __name__ == "__main__":
    unittest.main()
