
To retrieve the paths marked with an `x` inside the checkbox indicating that the path is to be filtered out:

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2
```

```STDOUT
.[] .tweet .display_text_range
.[] .tweet .favorited
.[] .tweet .id
.[] .tweet .possibly_sensitive
.[] .tweet .retweeted
.[] .tweet .source
.[] .tweet .truncated
```

Each of these lines is a path that can be provided to `jq`'s `del` command, providing that

- Each `[]` iterator part of the path is 'expanded' before the `del` call,
- after opening an array,
- and closing this array after the `del` call (so as to return the iterated list contents into a list)

---

Next we must examine the other types of path:

- Paths not `[x]`-marked which have multiple iterators
- Paths not `[x]`-marked which only have the top-level iterator

The first one is the less trivial, and can be listed with:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2
```

```STDOUT
.[] .tweet .entities .hashtags[] .indices
.[] .tweet .entities .hashtags[] .text
.[] .tweet .entities .media[] .display_url
.[] .tweet .entities .media[] .expanded_url
.[] .tweet .entities .media[] .id
.[] .tweet .entities .media[] .id_str
.[] .tweet .entities .media[] .indices
.[] .tweet .entities .media[] .media_url
.[] .tweet .entities .media[] .media_url_https
.[] .tweet .entities .media[] .sizes
.[] .tweet .entities .media[] .sizes .large
.[] .tweet .entities .media[] .sizes .large .h
.[] .tweet .entities .media[] .sizes .large .resize
.[] .tweet .entities .media[] .sizes .large .w
.[] .tweet .entities .media[] .sizes .medium
.[] .tweet .entities .media[] .sizes .medium .h
.[] .tweet .entities .media[] .sizes .medium .resize
.[] .tweet .entities .media[] .sizes .medium .w
.[] .tweet .entities .media[] .sizes .small
.[] .tweet .entities .media[] .sizes .small .h
.[] .tweet .entities .media[] .sizes .small .resize
.[] .tweet .entities .media[] .sizes .small .w
.[] .tweet .entities .media[] .sizes .thumb
.[] .tweet .entities .media[] .sizes .thumb .h
.[] .tweet .entities .media[] .sizes .thumb .resize
.[] .tweet .entities .media[] .sizes .thumb .w
.[] .tweet .entities .media[] .source_status_id
.[] .tweet .entities .media[] .source_status_id_str
.[] .tweet .entities .media[] .source_user_id
.[] .tweet .entities .media[] .source_user_id_str
.[] .tweet .entities .media[] .type
.[] .tweet .entities .media[] .url
...
```

Clearly this could use some summarisation. For each line, let's split the path into
individual parts to group the listings according to their shared hierarchy: as a
data structure we call this a trie. Code for this is in `summarise_paths.py`).

```sh
echo "trie = "$(grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | \
  cut -d\` -f2 | python summarise_paths.py) > path_trie.py
black path_trie.py
```

Just as a nice touch, we can 'pretty print' just the structure from this nicely formatted
Python dictionary layout thanks to black. Stripping out everything but key names and
whitespace shows the structure of the hierarchy

- Note: this actually deletes some keys, we need a better solution

```sh
cat path_trie.py | sed 's/: {None: None}//g'| sed '/\},*/d' | cut -d " " -f 5- | \
  sed '/^\s*$/d' | tr -d ":" | tr -d '"' | tr -d "{" | tr -d "." | \
  sed 's/None None/—/g' | s
```

```STDOUT
[] 
    tweet 
        entities 
            media[] 
                display_url,
                expanded_url,
                id,
                id_str,
                indices,
                media_url,
                media_url_https,
                sizes 
                    —,
                    large 
                        —,
                        h,
                        resize,
                        w,
                    medium 
                        —,
                        h,
                        resize,
                        w,
                    small 
                        —,
                        h,
                        resize,
                        w,
                    thumb 
                        —,
                        h,
                        resize,
                        w,
                source_status_id,
                source_status_id_str,
                source_user_id,
                source_user_id_str,
                type,
                url,
            urls[] 
                display_url,
                expanded_url,
                indices,
                url,
            user_mentions[] 
                id,
                id_str,
                indices,
                name,
                screen_name,
        extended_entities 
            media[] 
                additional_media_info 
                    —,
                    monetizable,
                display_url,
                expanded_url,
                id,
                id_str,
                indices,
                media_url,
                media_url_https,
                sizes 
                    —,
                    large 
                        —,
                        h,
                        resize,
                        w,
                    medium 
                        —,
                        h,
                        resize,
                        w,
                    small 
                        —,
                        h,
                        resize,
                        w,
                    thumb 
                        —,
                        h,
                        resize,
                        w,
                source_status_id,
                source_status_id_str,
                source_user_id,
                source_user_id_str,
                type,
                url,
                video_info 
                    —,
                    aspect_ratio,
                    duration_millis,
                    variants,
                    variants[] 
                        bitrate,
                        content_type,
                        url,

```

Note that in a trie the nodes with subnodes (i.e. parent nodes) can themselves be
entries ("parents can be leaves in their own right" I think you might say?)

Consider how in our path list above, there are these two lines:

```
.[] .tweet .entities .media[] .sizes
.[] .tweet .entities .media[] .sizes .large
```

i.e. the "sizes" key is both a leaf and a parent. The "large" leaf key is not a parent.

- We will say that the "sizes" key has a "null child" (as well as the "large" key as a 2nd child).
- In the 'minimalist' representation, note that there is a `—` underneath sizes to show this

```
                sizes 
                    —,
                    large 
```

from

```
                    ".sizes": {
                        None: None,
                        ".large": {
```

Rather than just print it out arbitrarily indented, I want to print it out so that
the node names align with their parent nodes (and this should make clear when parent
nodes are and are not also leaves).

There are two ways to get return from an async function:
- print it out to STDOUT (as in [`trie_walk.py`](trie_walk.py))
- yield from the calls that would otherwise return after printing (as in [`trie_walk_yielding.py`](trie_walk_yielding.py))

What I want next is to align using whitespace to indicate where lines differ from the precedent line.

To begin with I split the path at each line into a `preceder` subpath, which can then be omitted from the path as a 'common prefix'.
This is much simplified by the trie data structure, as the way to do so is to simply replace all characters in the preceder subpath
with whitespace unless the appendage to that subpath is empty (i.e. the subpath has one of the aforementioned 'null child' leaves).

- I have written the STDOUT printing and async yielding versions of the program to both read from the same preprocessor function, `mask_preceding` in [`trie_util.py`](trie_util.py).
  - I piped the output of `trie_walk.py` using a simpler printing function into `trie_walked_arrows.txt` (the function is available in `trie_util.py` as `mask_preceding_arrows`)

```sh
python trie_walk.py | tee trie_walked.txt
```

```STDOUT
.[] .tweet .entities .hashtags[]⠶.indices
                                ⠶.text
                     .media[]⠶.display_url
                             ⠶.expanded_url
                             ⠶.id
                             ⠶.id_str
                             ⠶.indices
                             ⠶.media_url
                             ⠶.media_url_https
                              .sizes⠶
                                     .large⠶
                                           ⠶.h
                                           ⠶.resize
                                           ⠶.w
                                     .medium⠶
                                            ⠶.h
                                            ⠶.resize
                                            ⠶.w
                                     .small⠶
                                           ⠶.h
                                           ⠶.resize
                                           ⠶.w
                                     .thumb⠶
                                           ⠶.h
                                           ⠶.resize
                                           ⠶.w
                             ⠶.source_status_id
                             ⠶.source_status_id_str
                             ⠶.source_user_id
                             ⠶.source_user_id_str
                             ⠶.type
                             ⠶.url
                     .urls[]⠶.display_url
                            ⠶.expanded_url
                            ⠶.indices
                            ⠶.url
                     .user_mentions[]⠶.id
                                     ⠶.id_str
                                     ⠶.indices
                                     ⠶.name
                                     ⠶.screen_name
           .extended_entities .media[] .additional_media_info⠶
                                                             ⠶.monetizable
                                      ⠶.display_url
                                      ⠶.expanded_url
                                      ⠶.id
                                      ⠶.id_str
                                      ⠶.indices
                                      ⠶.media_url
                                      ⠶.media_url_https
                                       .sizes⠶
                                              .large⠶
                                                    ⠶.h
                                                    ⠶.resize
                                                    ⠶.w
                                              .medium⠶
                                                     ⠶.h
                                                     ⠶.resize
                                                     ⠶.w
                                              .small⠶
                                                    ⠶.h
                                                    ⠶.resize
                                                    ⠶.w
                                              .thumb⠶
                                                    ⠶.h
                                                    ⠶.resize
                                                    ⠶.w
                                      ⠶.source_status_id
                                      ⠶.source_status_id_str
                                      ⠶.source_user_id
                                      ⠶.source_user_id_str
                                      ⠶.type
                                      ⠶.url
                                       .video_info⠶
                                                  ⠶.aspect_ratio
                                                  ⠶.duration_millis
                                                  ⠶.variants
                                                              ⠶.bitrate
                                                              ⠶.content_type
                                                              ⠶.url

```
