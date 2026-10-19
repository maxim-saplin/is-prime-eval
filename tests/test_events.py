import json
import tempfile
import unittest
from pathlib import Path

from events import LedgerCorruptionError, append_event, load_events


class EventLedgerTests(unittest.TestCase):
    def test_append_and_read_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "run.jsonl"
            append_event(path, {"event_type": "run_created", "value": 1})
            append_event(path, {"event_type": "attempt_started", "attempt_id": "a1"})
            events, discarded = load_events(path)
            self.assertEqual(discarded, 0)
            self.assertEqual([event["event_type"] for event in events], ["run_created", "attempt_started"])
            self.assertTrue(all(event["event_id"] for event in events))
            self.assertTrue(all(event["timestamp"].endswith("Z") for event in events))

    def test_torn_trailing_line_is_preserved_and_repaired(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "run.jsonl"
            append_event(path, {"event_type": "run_created"})
            torn = b'{"event_type":"attempt_started","attempt_id":"partial'
            with path.open("ab") as stream:
                stream.write(torn)
            with self.assertRaises(LedgerCorruptionError):
                load_events(path)
            events, discarded = load_events(path, repair_torn_tail=True)
            self.assertEqual(len(events), 1)
            self.assertEqual(discarded, len(torn))
            self.assertEqual(Path(f"{path}.torn").read_bytes(), torn)
            self.assertTrue(path.read_bytes().endswith(b"\n"))

    def test_invalid_newline_terminated_event_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "run.jsonl"
            path.write_bytes(b'{"event_type":"ok"}\nnot-json\n')
            with self.assertRaisesRegex(LedgerCorruptionError, "line 2"):
                load_events(path, repair_torn_tail=True)

    def test_partial_first_record_is_removed_as_torn_tail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "run.jsonl"
            path.write_bytes(b'{"event_type":"attempt_started"')
            events, discarded = load_events(path, repair_torn_tail=True)
            self.assertEqual(events, [])
            self.assertGreater(discarded, 0)
            self.assertEqual(path.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
