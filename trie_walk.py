from path_trie import trie
from trie_util import mask_preceding


def trie_walk(
    root,
    showfunc=print,
    seen=[],
    preceder=[],
    level=1,
    level_keys=[],
    level_changes=None,
    leaf_sizes=None,
    null_children=None,
):
    """
    Reproduce the input by trie traversal and show it using `showfunc`.
    
    Default `showfunc` will simply print each path to STDOUT, however
    it can be replaced by any function definition or lambda.
    """
    if level_changes is None:
        level_changes = []  # initialise running tally of trie walkback step sizes
        leaf_sizes = []
    if null_children is None:
        null_children = []
    level_change = 0  # presume the trie will not be walked back, else decrement count
    level_keys.append(list(root.keys()))
    subtrees = [root.get(k) for k in root.keys()]
    yield subtrees
    for i, subtree in enumerate(subtrees):
        sk = list(root.keys())[i]
        seen.append(sk)
        if subtree == {None: None}:
            null_children = []
            # the subtree is a leaf
            if len(level_changes) > 0:
                prev_level_change = level_changes[-1]
            else:
                prev_level_change = None  # only for an initial
            leaf_size = len(seen[len(preceder) :])
            leaf_sizes.append(leaf_size)
            showfunc(preceder, seen, level_changes, prev_level_change, leaf_sizes, null_children)
            gone = seen.pop()  # leaf will not be remembered (after being shown)
            if i == len(subtrees) - 1:
                popped = seen.pop()
                preceder.pop()
                level_keys.pop()
                level -= 1
                level_change -= 1
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
                            level_change -= 1
                    elif popped == level_keys[len(preceder)][-1]:
                        while popped == level_keys[len(preceder)][-1]:
                            popped = seen.pop()
                            preceder.pop()
                            level_keys.pop()
                            level -= 1
                            level_change -= 1
            level_changes.append(level_change)
            continue
        elif subtree is None:
            # the 'subtree' is a 'null child' indicating the parent is 'also a leaf'
            null_children.append(1)
            popped = seen.pop()  # leaf will not be remembered (nor shown at all)
            if len(level_changes) > 0:
                prev_level_change = level_changes[-1]
            else:
                prev_level_change = None  # only for an initial
            if preceder[-1] == ".large": pass#breakpoint()
            leaf_size = len(seen[len(preceder) :])
            leaf_sizes.append(leaf_size)
            #print(preceder)
            showfunc(preceder, seen, level_changes, prev_level_change, leaf_sizes, null_children)
            level_changes.append(level_change)
            continue
        subtree_keys = list(subtree.keys())
        preceder.append(sk)
        yield from trie_walk(
            subtree, showfunc, seen, preceder, level + 1, level_keys, level_changes, leaf_sizes, null_children
        )


def mask_preceding_printing(preceder, seen, level_changelog, level_change, leaf_sizes, null_children):
    str_out = mask_preceding(preceder, seen, level_changelog, level_change, leaf_sizes, null_children)
    print(str_out)
    return


# r = list(trie_walk(trie))
r = list(trie_walk(trie, showfunc=mask_preceding_printing))
