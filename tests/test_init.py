import sys
import os

sys.path.append('../')

import sct

class TestInit:
    def test_init(self):
        test = sct.SCT('./tests')
        assert test.todos == []
