from path_trie import trie
from trie_util import mask_preceding


def trie_walk(root, showfunc=print, seen=[], preceder=[], level=1, level_keys=[]):
    """
    Reproduce the input by trie traversal and show it using `showfunc`.
    
    Default `showfunc` will simply print each path to STDOUT, however
    it can be replaced by any function definition or lambda.
    """
    level_keys.append(list(root.keys()))
    subtrees = [root.get(k) for k in root.keys()]
    yield subtrees
    for i, subtree in enumerate(subtrees):
        sk = list(root.keys())[i]
        seen.append(sk)
        if subtree == {None: None}:
            # the subtree is a leaf
            # showfunc(f"{preceder}::{seen}")
            showfunc(preceder, seen)
            # showfunc(seen)
            gone = seen.pop()  # leaf will not be remembered (after being shown)
            if i == len(subtrees) - 1:
                popped = seen.pop()
                preceder.pop()
                level_keys.pop()
                level -= 1
                if i == len(subtrees) - 1:
                    if level_keys[len(preceder)][0] is None:
                        while (
                            level_keys[len(preceder)][0] is None
                            and popped == level_keys[len(preceder)][-1]
                        ):
                            popped = seen.pop()
                            preceder.pop()
                            level_keys.pop()
                            level -= 1
                    elif popped == level_keys[len(preceder)][-1]:
                        while popped == level_keys[len(preceder)][-1]:
                            popped = seen.pop()
                            preceder.pop()
                            level_keys.pop()
                            level -= 1
            continue
        elif subtree is None:
            # the 'subtree' is a 'null child' indicating the parent is 'also a leaf'
            popped = seen.pop()  # leaf will not be remembered (nor shown at all)
            showfunc(preceder, seen)
            continue
        subtree_keys = list(subtree.keys())
        preceder.append(sk)
        yield from trie_walk(subtree, showfunc, seen, preceder, level + 1, level_keys)


def mask_preceding_printing(preceder, seen):
    str_out = mask_preceding(preceder, seen)
    print(str_out)
    return


# r = list(trie_walk(trie))
r = list(trie_walk(trie, showfunc=mask_preceding_printing))
