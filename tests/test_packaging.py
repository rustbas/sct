import unittest

from importlib.resources import files


class PackagingTest(unittest.TestCase):
    def test_theme_tcss_in_package(self) -> None:
        path = files("sct.tui") / "theme.tcss"
        self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
