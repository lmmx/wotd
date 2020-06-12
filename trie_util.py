def mask_preceding(preceder, path, lvls, level, leaf_sizes, masksep=" ", null_child=False):
    leaf = path[len(preceder) :]
    leafsize = len(leaf)
    while leafsize > 1:
        #print(leaf)
        preceder.append(leaf.pop())
        leafsize = len(leaf)
    leaflevel = len(preceder) + leafsize
    last_two_leaf_sizes = leaf_sizes[-2:]
    if leafsize == 0 and level == 0 and not null_child:
        #if leaflevel == 6: breakpoint()
        # make an "artificial leaf"
        leaf = [preceder[-1]]
        preceder.pop()
        leafsize += 1
        if last_two_leaf_sizes == [0,0]:
            # JSON will only ever have 1 node overhang at a time
            leafsize += 1
    mask_length = leaflevel - 2 + leafsize 
    if level is None:
        mask_length = 0
    elif level < 0:
        mask_length += level

    for n in range(mask_length):
        x = preceder[n]
        x = masksep * len(x)
        #x = "".join([s.capitalize() for s in x])
        preceder[n] = x

    prec_str = " ".join(preceder)
    leaf_str = " ".join(leaf)
    
    last_two_lvls = lvls[-2:]
    nodeinfo = f"      {level}, {leaflevel}, {leafsize}," + \
               f"{mask_length}, {last_two_lvls}" + \
               f"{last_two_leaf_sizes}"
    line = "⠶".join([prec_str, leaf_str]) #+ nodeinfo
    return line


def mask_preceding_arrows(preceder, path):
    leaf = path[len(preceder) :]

    prec_str = " ⇒ ".join(preceder)
    leaf_str = " ⇢ ".join(seen[leaf])

    line = " ⠶ ".join([prec_str, leaf_str])
    return line
