#!/usr/bin/env python3

from dataclasses import dataclass
import os
import re

from sct import SCT
from argparse import ArgumentParser

default_parser = ArgumentParser()
default_parser.add_argument('-p', '--path',
                            #required=True,
                            default=".",
                            type=str,
                            help="Searching for TODOs directory (default: \".\")")

if __name__ == "__main__":
    parsed_arguments = default_parser.parse_args()
    sct = SCT(
            args = parsed_arguments
            )

    tasks = sct.todos
    print(tasks)
