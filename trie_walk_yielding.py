from path_trie import trie
from trie_util import mask_preceding


def trie_walk_yielding(root, yieldfunc, seen=[], preceder=[], level=1, level_keys=[]):
    """
    Reproduce the input by trie traversal and show it using `yieldfunc`.
    """
    level_keys.append(list(root.keys()))
    subtrees = [root.get(k) for k in root.keys()]
    # yield subtrees
    for i, subtree in enumerate(subtrees):
        sk = list(root.keys())[i]
        seen.append(sk)
        if subtree == {None: None}:
            # the subtree is a leaf
            yield from yieldfunc(preceder, seen)
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
            yield from yieldfunc(preceder, seen)
            continue
        subtree_keys = list(subtree.keys())
        preceder.append(sk)
        yield from trie_walk_yielding(subtree, yieldfunc, seen, preceder, level + 1, level_keys)


def mask_preceding_yielding(preceder, seen):
    str_out = mask_preceding(preceder, seen)
    yield str_out


r = list(trie_walk_yielding(trie, yieldfunc=mask_preceding_yielding))
