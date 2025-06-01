#!/usr/bin/env python3

from dataclasses import dataclass
import os
import re

from sct import SCT

if __name__ == "__main__":
    sct = SCT(".")

    tasks = sct.todos
    print(tasks)
