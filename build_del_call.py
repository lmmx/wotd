# grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2 | python trie_walk.py -
del_call = """
.[] .tweet .display_text_range
           .favorited
           .id
           .possibly_sensitive
           .retweeted
           .source
           .truncated
""".strip("\n")
