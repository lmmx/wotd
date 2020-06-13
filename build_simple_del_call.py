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

print("jq '[", end="")
closers.append("]")

for l_no, line in enumerate(path_lines[1:]):
    postamble_subline = line.lstrip()  # the 'unmasked' (sub)string
    postamble_subpath = postamble_subline.split()  # (sub)path list to the postamble
    line_len = len(line)
    postamble_len = len(postamble_subline)  # postamble char count of conjoined subpath
    mask_len = line_len - postamble_len  # len of whitespace 'mask'
    comma_sep = ", "
    if preamble_subpath is None:
        preamble_subline = init_line[:mask_len]  # inclusive of final space-sep.
        # preamble_subpath gives the prefixing subpath for each line,
        # until/unless it changes (it changes when mask_len < preamble_len)
        preamble_subpath = preamble_subline.split()  # split to list of key strings
        for preamble_i, preamble_part in enumerate(preamble_subpath):
            assert preamble_part.startswith(".")
            if preamble_part.endswith("[]"):
                print(preamble_part, end="")
            else:
                print(" | del(", end="")
                closers.append(")")
                print(f"{preamble_part} [", end="")
                closers.append("]")
        # preamble_space_sep_count === len(preamble_subpath)
        preamble_len = len(preamble_subline)
        init_postamble_subline = init_line[mask_len:]
        init_postamble_subpath = init_postamble_subline.split()
        for init_postamble_part in init_postamble_subpath:
            print('"' + init_postamble_part.lstrip(".") + f'"{comma_sep}', end="")
        for postamble_part in postamble_subpath:
            print('"' + postamble_part.lstrip(".") + f'"{comma_sep}', end="")
    else:
        if len(old_preamble_subpath) == len(preamble_subpath):
            for postamble_part in postamble_subpath:
                if l_no == len(path_lines) - 2:
                    comma_sep = "" # omit comma-separator on final line
                print('"' + postamble_part.lstrip(".") + f'"{comma_sep}', end="")
    # print(preamble_subpath, postamble_subpath)
    # compare path at each line and pop it once per space-sep. dedent
    old_preamble_subpath = preamble_subpath.copy()
    old_postamble_subpath = postamble_subpath.copy()

for closer in closers:
    print(closer, end="")
print("' wotd_tweet.json")
