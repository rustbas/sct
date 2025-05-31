#!/usr/bin/env python3

from dataclasses import dataclass
import os
import re

from sct import SCT

sct = SCT(".")

# [Todo]
tasks = sct.get_all_todos()
print(tasks)
