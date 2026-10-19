import io
import time
import unittest

from progress import ProgressReporter


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
        self.assertIn("model_id=openai/gpt-6-luna | reasoning_effort=low", text)
        self.assertIn("1/10", text)
        self.assertIn("elapsed", text)
        self.assertIn("ETA", text)
        self.assertIn("output", text)
        self.assertIn("tok/s", text)
        self.assertIn("correct 1", text)

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

    def test_heartbeat_reports_a_slow_nonstreaming_request(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output, heartbeat_interval=0.1)
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
        self.assertIn("waiting for response to d10-1000000007", output.getvalue())
        self.assertIn("ETA", output.getvalue())


if __name__ == "__main__":
    unittest.main()
