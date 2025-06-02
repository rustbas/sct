"""
Docstring
"""
from dataclasses import dataclass
import os
import re

def ignore_file_condition(path):
    """
    Docstring
    """
    if path[0] == '.': # Hidden dirs
        return False
    if path[0:2] == '__': # __pycache__, etc
        return False
    return True

@dataclass
class Todo():
    """
    Docstring
    """
    # ID: int
    file: str
    row_number: int
    task: str
    priority: int
    status: bool = False # Maybe will change it to some ENUM
    # DONE: create status

    @property
    def as_string(self):
        """
        Docstring
        """
        string = "{}:{}:{}"
        return string.format(self.file, self.row_number, self.task)

class SCT():
    """
    Docstring
    """
    def __init__(self, args, suffixes=None):
        # Get arguments
        self.__path = args.path

        self.__files = self.get_file_list(self.__path, suffixes)
        self.__todos = []
        self.get_all_todos()


    @property
    def todos(self):
        """
        Return list of Todo
        """
        return self.__todos

    def get_file_list(self, pwd, suffixes=None):
        """
        Docstring
        """
        elements = os.listdir(pwd)

        # Ignore some dirs dirs
        elements = list(filter(ignore_file_condition, elements))

        # Add root prefix
        elements = list(map(lambda x: os.path.join(pwd, x), elements))

        files = list(filter(os.path.isfile, elements))
        dirs = list(filter(os.path.isdir, elements))

        for directory in dirs:
            files += self.get_file_list(directory)

        if not suffixes is None:
            # TODO: Implement suffix filter
            pass

        return sorted(files)

    def get_all_todos(self):
        """
        Docstring
        """

        match_pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):.*$'
        findall_pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):(.*)$'
        for file in self.__files:
            with open(file, "r", encoding="utf-8") as code_file:
                for i, line in enumerate(code_file.readlines()):
                    if re.match(match_pattern, line.strip()):
                        linenum, [(status, task)] = i+1, \
                            re.findall(findall_pattern, line.strip())
                        if status == 'TODO':
                            status = False
                        else:
                            status = True
                        self.__todos.append(Todo(
                            # ID=0,
                            file=file,
                            row_number=linenum,
                            # TODO: calculate priority
                            priority = 1,
                            task=task.strip(),
                            status=status
                        ))

    def print_as_strings(self):
        """
        Print all current TODOs in quick fix format (for Emacs/Vim parsing ability)
        """
        for todo in self.__todos:
            if not todo.status:
                print(todo.as_string)
