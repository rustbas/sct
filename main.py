#!/usr/bin/env python3

from dataclasses import dataclass
import os
import re

@dataclass
class Todo():
    ID: int
    status: str # Maybe will change it to some ENUM
    file: str
    row_number: int
    task: str

def get_file_list(pwd, suffixes=None):
    elements = os.listdir(pwd)

    # Ignore hidden dirs
    elements = list(filter(lambda x: x[0] != '.', elements))

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
    # DONEE: Implement done status
    pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):.*$'
    for file in files:
        with open(file, "r") as f:
            for line in f.readlines():
                if re.match(pattern, line):
                    print(repr(line.strip()))

# curpath = os.getcwd()

files = get_file_list('.')
print(files)

# [Todo]
tasks = get_all_todos(files)
