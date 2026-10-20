import io
import os
import re
import time
import unittest
from unittest.mock import patch

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
        self.assertIn("Model ID: openai/gpt-6-luna | Effort: low", text)
        self.assertIn("1/10", text)
        self.assertIn("Elapsed", text)
        self.assertIn("ETA", text)
        self.assertIn("Output", text)
        self.assertIn("tok/s", text)
        self.assertIn("Correct 1", text)

    def test_omitted_effort_events_reuse_registered_identity_and_display_omitted(self):
        for explicit_null in (False, True):
            with self.subTest(explicit_null=explicit_null):
                output = io.StringIO()
                reporter = ProgressReporter(stream=output)
                reporter.set_batch_total(1)
                reporter.register_model("provider/model", None, 2)
                event = {
                    "event": "run_progress_init",
                    "model_id": "provider/model",
                    "total_cases": 2,
                    "completed_cases": 1,
                    "correct": 1,
                }
                if explicit_null:
                    event["reasoning_effort"] = None
                reporter(event)
                reporter({
                    **event,
                    "event": "case_finished",
                    "case_id": "remaining-case",
                    "outcome": "correct",
                    "completion_tokens": 12,
                })
                reporter.model_finished("provider/model", None, success=True)
                self.assertEqual(set(reporter._models), {("provider/model", None)})
                state = reporter._models[("provider/model", None)]
                self.assertEqual(state.completed, 2)
                self.assertEqual(state.correct, 2)
                self.assertEqual(state.output_tokens, 12)
                self.assertIn("Effort: default", output.getvalue())
                self.assertIn("1/1 done", output.getvalue())
                reporter.close()

    def test_mixed_efforts_keep_omission_distinct_from_literal_none(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output)
        reporter.set_batch_total(3)
        for effort in (None, "none", "high"):
            reporter.register_model("provider/model", effort, 1)
            reporter({
                "event": "case_finished",
                "model_id": "provider/model",
                "reasoning_effort": effort,
                "case_id": "same-case",
                "outcome": "correct",
                "completion_tokens": 1,
            })
            reporter.model_finished("provider/model", effort, success=True)
        self.assertEqual(len(reporter._models), 3)
        self.assertTrue(all(state.completed == 1 for state in reporter._models.values()))
        self.assertIn("Effort: default", output.getvalue())
        self.assertIn("Effort: none", output.getvalue())
        self.assertIn("Effort: high", output.getvalue())
        self.assertIn("3/3 done", output.getvalue())
        reporter.close()

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
        self.assertIn("\x1b[3A", text)
        self.assertIn("Model ID: openai/gpt-6-luna | Effort: low", text)

    def test_many_parallel_models_stay_within_a_24_row_tty_viewport(self):
        output = TTYStringIO()
        reporter = ProgressReporter(stream=output, force_tty=True)
        with patch("progress.shutil.get_terminal_size", return_value=os.terminal_size((80, 24))):
            reporter.set_active_model_limit(4)
            reporter.set_batch_total(13)
            self.assertEqual(reporter._rendered_lines, 9)
            for index in range(4):
                reporter.register_model(f"provider/model-{index}", "low", 140)
            self.assertEqual(reporter._rendered_lines, 9)

            for index in range(4):
                reporter.model_finished(f"provider/model-{index}", "low", success=True)
            for index in range(4, 13):
                reporter.register_model(f"provider/model-{index}", "low", 140)
                reporter.model_finished(f"provider/model-{index}", "low", success=True)

        self.assertLessEqual(reporter._rendered_lines, 22)
        self.assertEqual(len(reporter._finished_models), 13)
        self.assertIn("\x1b[9A", output.getvalue())
        final_frame = output.getvalue().rsplit("\x1b[9A", 1)[1]
        self.assertIn("13/13 done", final_frame)
        self.assertNotIn("Model ID:", final_frame)
        reporter.close()

    def test_80_column_rows_keep_eta_and_token_rate_visible(self):
        reporter = ProgressReporter(stream=io.StringIO(), force_tty=True)
        reporter.register_model("openai/gpt-6-luna", "high", 140)
        state = reporter._models[("openai/gpt-6-luna", "high")]
        state.completed = 14
        state.output_tokens = 5_000
        first_line, second_line = reporter._model_lines(("openai/gpt-6-luna", "high"), state, 79)
        self.assertLessEqual(len(first_line), 79)
        self.assertLessEqual(len(second_line), 79)
        self.assertIn("Model ID:", first_line)
        self.assertIn("Effort:", first_line)
        self.assertIn("ETA", second_line)
        self.assertIn("tok/s", second_line)
        reporter.close()

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

    def test_finished_model_elapsed_and_rate_freeze_while_batch_continues(self):
        reporter = ProgressReporter(stream=io.StringIO())
        reporter.set_batch_total(2)
        reporter.register_model("provider/fast", "low", 1)
        reporter.register_model("provider/slow", "medium", 2)
        reporter(
            {
                "event": "case_finished",
                "model_id": "provider/fast",
                "reasoning_effort": "low",
                "case_id": "fast-case",
                "outcome": "correct",
                "completion_tokens": 100,
            }
        )
        reporter.model_finished("provider/fast", "low", success=True)
        key = ("provider/fast", "low")
        first = reporter._model_lines(key, reporter._models[key], 79)
        time.sleep(0.05)
        second = reporter._model_lines(key, reporter._models[key], 79)
        self.assertEqual(first, second)
        reporter.close()

    def test_80_column_cancellation_header_and_every_tty_row_stay_within_width(self):
        output = TTYStringIO()
        reporter = ProgressReporter(stream=output, force_tty=True)
        with patch("progress.shutil.get_terminal_size", return_value=os.terminal_size((80, 24))):
            reporter.set_batch_total(1)
            reporter.register_model("openai/gpt-6-luna", "custom-effort", 140)
            reporter.set_batch_status("cancel requested; no new dispatch")
        rows = []
        for raw in output.getvalue().splitlines():
            clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", raw).replace("\r", "")
            if clean:
                rows.append(clean)
        self.assertTrue(rows)
        self.assertTrue(all(len(row) <= 79 for row in rows), rows)
        self.assertIn("cancel requested", " ".join(rows))
        self.assertIn("ETA", " ".join(rows))
        self.assertIn("tok/s", " ".join(rows))
        reporter.close()

    def test_heartbeat_reports_waiting_for_shared_request_gate(self):
        output = io.StringIO()
        reporter = ProgressReporter(stream=output, heartbeat_interval=0.1, force_tty=True)
        reporter.register_model("provider/slow-model", "low", 2)
        reporter(
            {
                "event": "rate_limit_wait",
                "model_id": "provider/slow-model",
                "reasoning_effort": "low",
                "case_id": "d10-1000000007",
                "attempt_number": 1,
                "max_attempts": 6,
            }
        )
        time.sleep(0.25)
        reporter.close()
        self.assertIn("waiting for shared request gate", output.getvalue())

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
