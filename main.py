#!/usr/bin/env python3

from dataclasses import dataclass
import os
import re

from sct import SCT
from argparse import ArgumentParser

default_parser = ArgumentParser()
# default_parser.add_argument('-i', '--input')

if __name__ == "__main__":
    default_parser.parse_args()
    sct = SCT(
            pwd = ".",
            )

    tasks = sct.todos
    print(tasks)
