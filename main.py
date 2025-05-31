#!/usr/bin/env python3

from dataclasses import dataclass
import os
import re

from sct import SCT

def ignore_file_condition(path):
    if path[0] == '.': # Hidden dirs
        return False
    if path[0:2] == '__': # __pycache__, etc
        return False
    return True

def get_file_list(pwd, suffixes=None):
    elements = os.listdir(pwd)

    # Ignore some dirs dirs
    elements = list(filter(ignore_file_condition, elements))

    # Add root prefix
    elements = list(map(lambda x: os.path.join(pwd, x), elements))

    files = list(filter(lambda x: os.path.isfile(x), elements))
    dirs = list(filter(lambda x: os.path.isdir(x), elements))

    for directory in dirs:
        files += get_file_list(directory)
        pass

    if not suffixes is None:
        # TODO: Implement suffix filter
        pass

    return sorted(files)

ID = 0
def get_all_todos(files):
    global ID
    # DONEE: Implement done status
    match_pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):.*$'
    findall_pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):(.*)$'
    result = []
    for file in files:
        print(file)
        with open(file, "r") as f:
            for i, line in enumerate(f.readlines()):
                if re.match(match_pattern, line.strip()):
                    linenum, [(status, task)] = i+1, \
                        re.findall(findall_pattern, line.strip())
                    result.append(Todo(
                        ID=ID,
                        # TODO: create enum for status
                        status = status,
                        file=file,
                        row_number=linenum,
                        # TODO: calculate priority
                        priority = 1,
                        task=task.strip()
                    ))
                    ID += 1
    return result

@dataclass
class Todo():
    ID: int
    status: str # Maybe will change it to some ENUM
    file: str
    row_number: int
    task: str
    priority: int

    def string(self):
        string = "{}:{}:{}"
        return string.format(self.file, self.row_number, self.task)

# curpath = os.getcwd()

def print_tasks(tasks):
    for todo in tasks:
        string = todo.string()
        print(string)

files = get_file_list('.')
print(files)

sct = SCT()

# [Todo]
tasks = get_all_todos(files)
print_tasks(tasks)
