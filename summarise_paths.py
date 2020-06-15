import fileinput
import sys


def make_validated_trie(path_list):
    """
    https://stackoverflow.com/a/11016430/2668831
    """
    root = dict()
    _end = None
    for path in path_list:
        current_dict = root
        for key in path[:-1]:
            current_dict = current_dict.setdefault(key, {})
        if len(current_dict) > 0 and None in current_dict.keys():
            joined_path = " ".join(path[:-1])
            raise ValueError(
                f'Invalid input: "{joined_path}" is both a UKP path'
                + f' and a subpath above the key "{path[-1]}"'
            )
        # Final step adds null entry
        current_dict = current_dict.setdefault(path[-1], {})
        current_dict[_end] = _end
    return root


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


def pipe_trie(piped_input=None, outfunc=print, validate=False):
    if piped_input is None:
        piped_input = list(fileinput.input())
    path_list = list(map(line2path, piped_input))
    if validate:
        trie = make_validated_trie(path_list)
    else:
        trie = make_trie(path_list)
    # sys.stdin = open("/dev/tty")
    return outfunc(trie)


if __name__ == "__main__":
    pipe_trie()
