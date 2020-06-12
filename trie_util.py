def mask_preceding(
    preceder, path, lvls, level, leaf_sizes, null_children, seps=[" ", " ", " "]
):
    mask_sep, path_sep, leaf_sep = seps
    if len(null_children) > 1:
        is_null_child = null_children[-1] == 1
        is_child_of_null_child = null_children[-2] == 1
    elif len(null_children) > 0:
        is_null_child = null_children[-1] == 1
        is_child_of_null_child = False
    else:
        is_null_child = False
        is_child_of_null_child = False
    leaf = path[len(preceder) :]
    leafsize = len(leaf)
    while leafsize > 1:
        preceder.append(leaf.pop())
        leafsize = len(leaf)
    leaflevel = len(preceder) + leafsize
    last_two_leaf_sizes = leaf_sizes[-2:]
    if is_null_child or is_child_of_null_child:
        pass
    elif leafsize == 0 and level == 0:
        # if leaflevel == 6: breakpoint()
        # make an "artificial leaf"
        leaf = [preceder[-1]]
        preceder.pop()
        leafsize += 1
        if last_two_leaf_sizes == [0, 0]:
            # jq-enumerated JSON paths will only ever have 1 node overhang at a time
            leafsize += 1
    mask_length = leaflevel - 2 + leafsize
    if level is None:
        mask_length = 0
    elif level < 0:
        mask_length += level
    elif is_null_child and is_child_of_null_child:
        mask_length += 1

    for n in range(mask_length):
        x = preceder[n]
        x = mask_sep * len(x)
        preceder[n] = x

    prec_str = path_sep.join(preceder)
    leaf_str = path_sep.join(leaf)

    last_two_lvls = lvls[-2:]
    # for debugging purposes
    nodeinfo = (
        f"      {level}, {leaflevel}, {leafsize},"
        + f"{mask_length}, {last_two_lvls}"
        + f"{last_two_leaf_sizes}, {null_children[-5:]}"
    )
    line = leaf_sep.join([prec_str, leaf_str])  # + nodeinfo
    return line


# def mask_preceding_arrows(preceder, path):
#    """
#    Deprecated very simple version
#    """
#    leaf = path[len(preceder) :]
#
#    prec_str = " ⇒ ".join(preceder)
#    leaf_str = " ⇢ ".join(seen[leaf])
#
#    line = " ⠶ ".join([prec_str, leaf_str])
#    return line
