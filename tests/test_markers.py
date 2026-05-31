import unittest

from sct.core.markers import (
    done_marker,
    open_marker,
    parse_line,
    priority_from_marker,
    replace_marker_on_line,
)


class MarkersTest(unittest.TestCase):
    def test_priority(self) -> None:
        self.assertEqual(priority_from_marker("TODO"), 1)
        self.assertEqual(priority_from_marker("TODOO"), 2)
        self.assertEqual(priority_from_marker("DONEEE"), 3)

    def test_markers_roundtrip(self) -> None:
        self.assertEqual(open_marker(2), "TODOO")
        self.assertEqual(done_marker(2), "DONEE")

    def test_parse_and_replace(self) -> None:
        m = "TOD" + "O" * 2
        line = f"    # {m}: Implement suffix filter\n"
        parsed = parse_line(line)
        self.assertIsNotNone(parsed)
        prefix, marker, task, _ = parsed
        self.assertEqual(marker, "TODOO")
        new = replace_marker_on_line(line, done_marker(2))
        self.assertIn("DON" + "EE:", new)
        self.assertIn("Implement suffix filter", new)


if __name__ == "__main__":
    unittest.main()
