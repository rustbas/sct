import sys

sys.path.append('../')

import sct

def test_init():
    test = sct.SCT('.')
    assert test.todos == []
