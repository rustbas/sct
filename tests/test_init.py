import sys
import os

sys.path.append('../')

import sct

class TestInit:
    def test_init(self):
        '''
        Test empty class
        '''
        test = sct.SCT('./tests')
        assert test.todos == []

    def test_string(self):
        '''
        Test to_string function
        '''
        test = sct.Todo(
                        status='status',
                        file='file',
                        row_number='row_number',
                        task='task',
                        priority='priority',
                )
        assert test.as_string == "file:row_number:task"
