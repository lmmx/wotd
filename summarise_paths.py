import fileinput
import sys

def make_trie(path_list):
    """
    https://stackoverflow.com/a/11016430/2668831
    """
    root = dict()
    _end = None
    for path in path_list:
        current_dict = root
        for key in path:
            current_dict = current_dict.setdefault(key, {})
        current_dict[_end] = _end
    return root

def line2path(line):
    path = line.rstrip("\n").split()
    return path

piped_input = list(fileinput.input())
path_list = list(map(line2path, piped_input))
trie = make_trie(path_list)
#sys.stdin = open("/dev/tty")
#breakpoint()
print(trie)