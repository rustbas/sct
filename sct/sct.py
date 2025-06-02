"""
Docstring
"""
from dataclasses import dataclass
import os
import re

def unimplemened():
    """
    Plug-function that raise NotImplementedError
    """
    raise NotImplementedError("Not implemented yet!")


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
    def __init__(self, args, suffixies = None):
        # Get arguments
        self.__path = args.path

        # Init attributes
        self._files = self.get_files_list(self.__path)
        self.__todos = []

        # Filter files
        self.suffixies = suffixies
        if suffixies is not None:
            self.filter_by_suffix()

        self.get_all_todos()

    def filter_by_suffix(self):
        """
        Filter files by it's suffix (source code extensions)
        """
        result = []
        for suffix in self.suffixies:
            tmp = filter(lambda x: x.endswith(suffix), self._files)
            result += list(tmp)
        self._files = result

    @property
    def todos(self):
        """
        Return list of Todo
        """
        return self.__todos

    def create_issue(self):
        """
        Create issue on GitHub
        """
        unimplemened()

    @staticmethod
    def is_included(path):
        """
        Docstring
        """
        if path[0] == '.': # Hidden dirs
            return False
        if path[0:2] == '__': # __pycache__, etc
            return False
        return True

    def list_directory_elements(self, path):
        """
        List all elements if path, excluded by 'is_included'
        """
        elements = os.listdir(path)

        # filter some paths
        elements = filter(self.is_included, elements)

        # add absolute (relatively root) path
        elements = list(map(lambda x: os.path.join(path, x), elements))
        return elements

    def elements_to_dirs_and_files(self, elements):
        """
        Segregate directory elements to directories and files
        """
        dirs = list(filter(os.path.isdir, elements))
        files = list(filter(os.path.isfile, elements))

        return dirs, files

    def get_files_list(self, pwd):
        """
        Docstring
        """

        elements = self.list_directory_elements(pwd)
        dirs, files = self.elements_to_dirs_and_files(elements)

        for directory in dirs:
            files += self.get_files_list(directory)

        return sorted(files)

    def get_all_todos(self):
        """
        Docstring
        """

        match_pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):.*$'
        findall_pattern = r'^.*(TOD[O]{1,3}|DON[E]{1,3}):(.*)$'
        for file in self._files:
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
