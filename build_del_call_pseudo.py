import sys
import fileinput

if "-" in sys.argv:
    del_call = "\n".join([s.rstrip("\n") for s in fileinput.input()]).strip("\n")
else:
    # grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2 | python trie_walk.py -
    del_call = """
.[] .tweet .display_text_range
           .favorited
           .id
           .possibly_sensitive
           .retweeted
           .source
           .truncated
""".strip(
        "\n"
    )

path_lines = del_call.split("\n")

init_line = path_lines[0]
init_lens = [len(s) for s in init_line.split()]
init_line_len = sum(init_lens)
preamble_subpath = None

closers = []

print_depth = 0
print("[")
closers.append("]")
print_depth += 1

for line in path_lines[1:]:
    postamble_subline = line.lstrip()  # the 'unmasked' (sub)string
    postamble_subpath = postamble_subline.split()  # (sub)path list to the postamble
    line_len = len(line)
    postamble_len = len(postamble_subline)  # postamble char count of conjoined subpath
    mask_len = line_len - postamble_len  # len of whitespace 'mask'
    if preamble_subpath is None:
        preamble_subline = init_line[:mask_len]  # inclusive of final space-sep.
        # preamble_subpath gives the prefixing subpath for each line,
        # until/unless it changes (it changes when mask_len < preamble_len)
        preamble_subpath = preamble_subline.split()  # split to list of key strings
        for preamble_i, preamble_part in enumerate(preamble_subpath):
            assert preamble_part.startswith(".")
            if preamble_part.endswith("[]"):
                whitespace = "    " * print_depth
                print(whitespace + "_" + preamble_part.lstrip(".").replace("[]", "[:]"))
            else:
                whitespace = "    " * print_depth
                print(whitespace + "| DEL(")
                closers.append(")")
                print_depth += 1
                print("    " * print_depth + "_" + preamble_part.lstrip(".") + "[")
                closers.append("]")
        # preamble_space_sep_count === len(preamble_subpath)
        preamble_len = len(preamble_subline)
        init_postamble_subline = init_line[mask_len:]
        init_postamble_subpath = init_postamble_subline.split()
        for init_postamble_part in init_postamble_subpath:
            print(f'            "' + init_postamble_part.lstrip(".") + '",')
        for postamble_part in postamble_subpath:
            print(f'            "' + postamble_part.lstrip(".") + '",')
    else:
        if len(old_preamble_subpath) == len(preamble_subpath):
            for postamble_part in postamble_subpath:
                print(f'            "' + postamble_part.lstrip(".") + '",')
    # print(preamble_subpath, postamble_subpath)
    # compare path at each line and pop it once per space-sep. dedent
    old_preamble_subpath = preamble_subpath.copy()
    old_postamble_subpath = postamble_subpath.copy()

for closer in closers:
    print("    " * print_depth + closer)
    print_depth -= 1
