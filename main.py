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
default_parser.add_argument('-l', '--list',
                            action="store_true",
                            help="Printing all TODOs in quick_fix format")

if __name__ == "__main__":
    parsed_arguments = default_parser.parse_args()
    sct = SCT(
            args = parsed_arguments,
            suffixies = ["py"]
            )

    tasks = sct.todos
    # print(tasks)
    if (parsed_arguments.list):
        sct.print_as_strings()
