#!/usr/bin/env python3

import os

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


# curpath = os.getcwd()

files = get_file_list('.')
print(files)
