# Auditing the unique key paths in a JSON file with a trie

## 1. Intro

To retrieve the paths marked with an `x` inside the checkbox indicating that the path is to be filtered out:

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2
```
⇣
```STDOUT
.[] .tweet .display_text_range
.[] .tweet .favorited
.[] .tweet .id
.[] .tweet .possibly_sensitive
.[] .tweet .retweeted
.[] .tweet .source
.[] .tweet .truncated
```

Each of these lines is a path that in turn can be passed to `jq`'s `del` command, providing that:

- Each `[]` iterator part of the path is 'expanded' before the `del` call,
- after opening an array,
- and closing this array after the `del` call (so as to return the iterated list contents into a list)


---

## 2. A quick summary view of the UKP checklist (`sed`, `cut`, `tr`)

Next we must examine the other types of path:

- Paths not `[x]`-marked which have multiple iterators
- Paths not `[x]`-marked which only have the top-level iterator

The first one is the less trivial, and can be listed with:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2
```
⇣
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
  sed 's/None None/—/g'
```
⇣
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

> (Actually the large leaf key is a parent, but for now imagine this is our entire tree,
> in which case it wouldn't be a parent as it's the last path in the list)

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

To do this, I will put down command line tools and write a proper parser in Python.

## 3. Proper Python parsing: taking a recursive walk on a trie

There are two ways to get return from a recursive function:
- print it out to STDOUT (as in [`trie_walk.py`](trie_walk.py))
- yield from the calls that would otherwise return after printing (as in [`trie_walk_yielding.py`](trie_walk_yielding.py))

> As a technical note, I think you'd call this recursive function "async but blocking", meaning it
> could technically run in parallel and have results from shallower parts of the tree come back before
> the deeper ones, but I want it to return in the same order as the lines so it's "blocking".  
> (Don't quote me on that)

What I want next is to align using whitespace to indicate where lines differ from the precedent line.

To begin with I split the path at each line into a `preceder` subpath, which can then be omitted from the
path as a 'common prefix'.  This is much simplified by the trie data structure, as the way to do so is to
simply replace all characters in the preceder subpath with whitespace unless the appendage to that subpath
is empty (i.e. the subpath has one of the aforementioned 'null child' leaves).

- I have written the STDOUT printing and async yielding versions of the program to both read from the same
  preprocessor function, `mask_preceding` in [`trie_util.py`](trie_util.py).

  - I piped the output of `trie_walk.py` using a simpler printing function into `trie_walked_arrows.txt`
    (the function is commented out in `trie_util.py` as `mask_preceding_arrows`)

```sh
python trie_walk.py | tee trie_walked.txt
```
⇣
```STDOUT
.[] .tweet .entities .hashtags[] .indices
                                 .text
                     .media[] .display_url
                              .expanded_url
                              .id
                              .id_str
                              .indices
                              .media_url
                              .media_url_https
                              .sizes 
                                     .large 
                                            .h
                                            .resize
                                            .w
                                     .medium 
                                             .h
                                             .resize
                                             .w
                                     .small 
                                            .h
                                            .resize
                                            .w
                                     .thumb 
                                            .h
                                            .resize
                                            .w
                              .source_status_id
                              .source_status_id_str
                              .source_user_id
                              .source_user_id_str
                              .type
                              .url
                     .urls[] .display_url
                             .expanded_url
                             .indices
                             .url
                     .user_mentions[] .id
                                      .id_str
                                      .indices
                                      .name
                                      .screen_name
           .extended_entities .media[] .additional_media_info 
                                                              .monetizable
                                       .display_url
                                       .expanded_url
                                       .id
                                       .id_str
                                       .indices
                                       .media_url
                                       .media_url_https
                                       .sizes 
                                              .large 
                                                     .h
                                                     .resize
                                                     .w
                                              .medium 
                                                      .h
                                                      .resize
                                                      .w
                                              .small 
                                                     .h
                                                     .resize
                                                     .w
                                              .thumb 
                                                     .h
                                                     .resize
                                                     .w
                                       .source_status_id
                                       .source_status_id_str
                                       .source_user_id
                                       .source_user_id_str
                                       .type
                                       .url
                                       .video_info 
                                                   .aspect_ratio
                                                   .duration_millis
                                                   .variants
                                                               .bitrate
                                                               .content_type
                                                               .url
```

## 4. Subtle but important: iterator masking

**N.B.** — an interesting side effect here is that due to the assumption that the input is
presorted (i.e. it permits/respects any lexicographic order), there's no demand for
parent keys to be called the same thing 'as a parent' vs. 'as a leaf' (so perhaps it's not
strictly a trie? I'm not sure, though the data structure is).

- For instance, though it's not shown, if we compare the final three lines:

Input:

```
.[] .tweet .extended_entities .media[] .video_info .variants
.[] .tweet .extended_entities .media[] .video_info .variants[] .bitrate
.[] .tweet .extended_entities .media[] .video_info .variants[] .content_type
.[] .tweet .extended_entities .media[] .video_info .variants[] .url
```

Trie processed output:

```
                                                   .variants
                                                               .bitrate
                                                               .content_type
                                                               .url
```

Note how the `variants` key becomes an 'iterated' key (as `variants[]`) when it's a parent
rather than a leaf (i.e. on the final 3 lines), but our algorithm does not do string matching
at all, so it doesn't "notice", it simply uses the 'stepping' up and down levels and presumes
that any 'stepping down' must be a single 'step' at a time (since a JSON path tree cannot
'skip' a step, it must proceed a level at a time).

- Where this occurs, the children of the parent key without an iterator (like
  those below `.variants`) will appear 'shifted along' by a couple of characters where the
  `[]` is masked as whitespace.
- Also note that the first line is treated differently, so as long as the paths are sorted
  following the initial line, the algorithm should display any set of JSON paths from jq correctly.

---

This was all in aid of getting a better look at the checklist of UKPs, and specifically
I want to pipe the `grep`'d subsets:

- Paths not `[x]`-marked which have multiple iterators
- Paths not `[x]`-marked which only have the top-level iterator

...and the paths marked by `[x]` were easily selected by:

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2
```

## 5. Through a proper Python parser, pipeably: trie walking from any STDIN

So far, the `summarise_paths.py` script takes input over STDIN (shell pipes) but then
that was piped into a hardcoded file (a variable named `trie` stored in `path_trie.py`).
`trie_walk.py` then read that file and printed out a nice readable masked version of the trie.

Now I've got my trie walking algorithm working consistently, and all edge cases worked out,
I want to be able to pipe any checklist into `trie_walk.py` and get its nicely presented masked
trie output, without going through the intermediate step of saving to a new file or overwriting
`path_trie.py`.

- To do this, I will add a single flag to `trie_walk.py`, the standard flag for reading
  input over a pipe which is `-`. This way I can pipe a subset of lines in the UKP checklist
  (from `grep`) and process them without going through `summarise_paths.py`.

- I added a simple `__name__ == "__main__"` check to `summarise_paths.py` to control the function
  which reads these lines from STDIN and prints their processed trie to STDOUT.
  - This function is called `pipe_trie`

- I added a simple `if "-" in sys.argv` check to `trie_walk.py` to override the imported
  `trie` variable from `path_trie` and instead generate a new trie via `summarise_paths`.
  - The list of lines are passed to the `pipe_trie` function as its `piped_input` parameter,
    replacing the list of lines read from the STDIN pipe when `summarise_paths` is invoked as
    `__main__`.
  - A bit of a hack, but pleasingly allows the `summarise_paths` module to be used in both modes:
    instead of a simple `print` statement for the constructed trie, `summarise_paths.py`⠶`pipe_trie`
    ends with the line `return outfunc(trie)`.
    - By default `outfunc=print`, but when calling it from another module (in this case, I'm
      calling it from `trie_walk.py`) I pass in the trivial lambda function `lambda x: x`, so
      the `outfunc` wrapper has no effect, and the result of `pipe_trie` becomes `return trie`,
      passing it back to the module the call came from (which in this case is `trie_walk.py`).

Now we can get the same output as in the non-piped script, but without relying on storing
grep output in a file (like `path_trie.py`, which is less adaptable).

So the new piped version of the original file-based command via `summarise_paths.py` becomes:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | python trie_walk.py -
```

We can even verify it's identical to the non-piped version
- `$(!!)` gets the output of rerunning the last command

```sh
diff <(python trie_walk.py) <(echo "$(!!)")
```

The nice thing about this is that we can view a subsection but still get the easy to read
masking of repeated subpaths on each line (whereas for instance just taking the `tail` of
the output of the hardcoded file would omit the first line making the full path unknown).

- This happened when I took the tail to show `variants`, above. I will come back to this below.

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -30 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .sizes 
                                              .large 
                                                     .h
                                                     .resize
                                                     .w
                                              .medium 
                                                      .h
                                                      .resize
                                                      .w
                                              .small 
                                                     .h
                                                     .resize
                                                     .w
                                              .thumb 
                                                     .h
                                                     .resize
                                                     .w
                                       .source_status_id
                                       .source_status_id_str
                                       .source_user_id
                                       .source_user_id_str
                                       .type
                                       .url
                                       .video_info 
                                                   .aspect_ratio
                                                   .duration_millis
                                                   .variants
                                                               .bitrate
                                                               .content_type
                                                               .url
```

or just the final 3 levels:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -7 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .video_info 
                                                   .aspect_ratio
                                                   .duration_millis
                                                   .variants
                                                               .bitrate
                                                               .content_type
                                                               .url
```

...and just the final 2 levels, then just the final 1 level, to show the omission of the iterator on the
variants key.

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -4 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .video_info .variants
                                                               .bitrate
                                                               .content_type
                                                               .url
```

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -3 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .video_info .variants[] .bitrate
                                                               .content_type
                                                               .url
```

(etc.)

---

## 6. Building a jq del call from a checklist

So to get back to the point here, the prototypical example of the `jq del` call we want to build from these
tries is `dejunk.sh` (which was described in `DEJUNK.md`)

```sh
# Removes:
# - .tweet.retweeted
# - .tweet.source
# - .tweet.display_text_range
# - .tweet.id
# - .tweet.truncated
# - .tweet.favorited
# - .tweet.possibly_sensitive

jq '[.[] | del(.tweet ["retweeted", "source", "display_text_range", "id", "truncated", "favorited", "possibly_sensitive"])]' wotd_tweet.json
```

If we produce the masked trie from the list of paths this `del` call targets, we get the following:

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .display_text_range
           .favorited
           .id
           .possibly_sensitive
           .retweeted
           .source
           .truncated
```

To recap what was said at the beginning of this file, the requirements for this `del` call are:

> - Each `[]` iterator part of the path is 'expanded' before the `del` call,
> - after opening an array,
> - and closing this array after the `del` call (so as to return the iterated list contents into a list)

Comparing these requirements to the masked trie representation from `trie_walk.py` for the simple `jq del`
call in `dejunk.sh`:

- At the same point (specifically, exactly before) each iterator is introduced, open an array (with a square bracket)

  - Here the only iterator introduced is `.[]`, and there's a `[` before it, which is closed at the end of the command

- Below the iterator, add any "preceder" parts of the subpath inside a `del` call, followed by an array of the leaves
  (this array requires another pair of square brackets, which close immediately before the `del` call's round bracket closes).

  - Here the only "preceder" part of the subpath below the only iterator (`.[]`) is `.tweet`,
    and `.tweet` is inside the opening of the `del` call, followed by an array of the leaves.

  - Note that `jq` has sorted the leaves alphabetically when enumerating the paths, so the masked trie leaf order
    is different to the one in the `dejunk.sh` file (which is in the order of appearance of the keys in the JSON).
    The alphabetical order is easier to read.

- At the "leaf" (i.e. the node following the masked "preceder" part/s of the subpath), presumably repeat the above
  steps upon reaching any 'sub-keys' (i.e. open another array to target the subkey).

  - Note that for a `del` call, keys and subkeys will be mutually exclusive. In other words, it makes no sense to
    delete a key and also a subkey of that key, because deleting a key will _ipso facto_ delete all subkeys of that key.

  - Here the leaves are the list read vertically from `.display_text_range` to `.truncated`, and none of them have
    subkeys.

  - Note that providing a non-whitespace character to the third element in the list parameter `seps` of the function
    `mask_preceding` (in the file `trie_util.py`) will add a distinguishing separator between the tree and the leaves
    to display this separation more clearly.

    - (This was used for development/debugging and is not exposed to the calling function `mask_preceding_printing`
      which initiates the write to STDOUT within the recursive function `trie_walk`).

Given this guesstimate of how to programmatically write a `del` call from the masked trie representation of a
JSON path list, I will write a simple Python script which takes as input the masked trie.

- It will not need to know the input for the masked trie (though we must take care to spot any omitted iterators,
  as their masked whitespace will be two characters longer than the key)
  - See the note on `variants`/`variants[]` above.

To begin, let's reproduce the `jq del` call in `dejunk.sh` from the trie which it was written to target.

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .display_text_range
           .favorited
           .id
           .possibly_sensitive
           .retweeted
           .source
           .truncated
```

...which I'll just write with `>>` into a Python string variable:

```py
del_call = """
.[] .tweet .display_text_range
           .favorited
           .id
           .possibly_sensitive
           .retweeted
           .source
           .truncated
""".strip("\n")
```

The goal is to recreate the `jq` command (in `dejunk.sh`):

```sh
jq '[.[] | del(.tweet ["retweeted", "source", "display_text_range", "id", "truncated", "favorited", "possibly_sensitive"])]' wotd_tweet.json
```

To get a better look at it, let's convert the jq command into pseudo-Python code so black will lint it:

- Extract the jq command from inside the single quotation marks
- Capitalise 'del' because it's a reserved word in Python (a keyword)
- Put a colon inside the iterator brackets after all key names
- Replace the prefixing dot in any key names with an underscore

black then lints the above command (saved as `dejunk_sh.py`) to:

```py
[
    _[:]
    | DEL(
        _tweet[
            "retweeted",
            "source",
            "display_text_range",
            "id",
            "truncated",
            "favorited",
            "possibly_sensitive",
        ]
    )
]
```

We can make it look a bit more like the original command again:

```sh
cat dejunk_sh.py | tr -d ":" | sed 's/DEL/del/' | sed 's/\s_/ \./g'
```
⇣
```STDOUT
[
    .[]
    | del(
        .tweet[
            "retweeted",
            "source",
            "display_text_range",
            "id",
            "truncated",
            "favorited",
            "possibly_sensitive",
        ]
    )
]
```

or all on one line:

```sh
cat dejunk_sh.py | tr -d ":" | sed 's/DEL/del/' | sed 's/\s_/ \./g' | tr -d "\n" | sed 's/\s\s*/ /g'
```
⇣
```STDOUT
[ .[] | del( .tweet[ "retweeted", "source", "display_text_range", "id", "truncated", "favorited", "possibly_sensitive", ] )]
```

Note how black introduces a comma after the final leaf is listed in the array for subkeys of `.tweet`:

```
            "possibly_sensitive",
        ]
    )
]
```

Note that this would cause jq to throw an error.

```sh
python build_del_call_pseudo.py
```
⇣
```STDOUT
[
    _[:]
    | DEL(
        _tweet[
            "display_text_range",
            "favorited",
            "id",
            "possibly_sensitive",
            "retweeted",
            "source",
            "truncated",
        ]
    )
]
```

If we now pipe this to `black`, it is returned without changes

```sh
python build_del_call_pseudo.py | black - > /dev/null
```
⇣
```STDOUT
All done! ✨ 🍰 ✨
1 file left unchanged.
```

In fact this is identical to the real call we wrote manually in all but the order of leaf keys, as already noted.

```sh
diff <(python build_del_call_pseudo.py) <(cat dejunk_sh.py)
```
⇣
```STDOUT
5,8d4
<             "display_text_range",
<             "favorited",
<             "id",
<             "possibly_sensitive",
10a7,8
>             "display_text_range",
>             "id",
11a10,11
>             "favorited",
>             "possibly_sensitive",
```

Adding a check at the beginning `if "-" in sys.argv`, I then made `build_del_call_pseudo.py` pipeable over STDIN too!

Now we can reproduce the same output we get from running `python build_del_call_pseudo.py` by the equivalent workflow:

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2 | python trie_walk.py - | python build_del_call_pseudo.py -
diff <(python build_del_call_pseudo.py) <(echo "$(!!)")
```

We now need to reobtain the actual `dejunk.sh` target file, not the pseudo-Python we derived from it in `dejunk_sh.py`.

To do this, I will use a modified program `build_simple_del_call.py` which:

- outputs less whitespace and no newlines within the command,
- does not add a colon inside iterator square brackets,
- does not capitalise the `del` call
- does not replace prefixing `.` in key names with an underscore
- retains a space, within the `del` call, between keys and the square brackets opening for subkeys
- removes the final comma in the list of leaves below an iterator

This cannot handle the changing levels of the real output tries, but it's a step towards a program that can.
Again, the output is identical except for the JSON keys becoming alphabetically ordered in the generated `jq` call.

```sh
python build_simple_del_call.py
```
⇣
```STDOUT
jq '[.[] | del(.tweet ["display_text_range", "favorited", "id", "possibly_sensitive", "retweeted", "source", "truncated"])]' wotd_tweet.json
```

Again, it can be called with input piped over STDIN (the command below gives the same output as the previous)

```sh
grep '\-\s\[x\]' ukp_manifest.md | cut -d\` -f2 | python trie_walk.py - | python build_simple_del_call.py -
```

### Levelling up (and down) to validate jq checklist input

It's now time to level up the checklist parser so that it can handle real
examples, to do which it must reject inconsistent configurations of the checklist.
In other words, it must validate the input paths that are piped into it.

Let's take a look at the example we saw earlier, monotonically descending 3 levels:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -7 | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .video_info 
                                                   .aspect_ratio
                                                   .duration_millis
                                                   .variants
                                                               .bitrate
                                                               .content_type
                                                               .url
```

Notice how this doesn't make sense as a filter: after filtering out the path to the
`video_info` key from the first line, the descendants below it will be gone. So
it is a waste of time to construct these paths as `jq` `del` calls at all.

Before we get to the separate issue of constructing jq programs from tries that step
up and down, let's first add a check that will abort the program entirely if it
is invalidly stated.

- A trie is invalid input to `build_del_call.py` if any key path it contains
  is an ancestor of any other (or vice versa, if any UKP it contains is a descendant
  of any other).
- Algorithmically, since we expect the trie input will be lexicographically sorted,
  we only need to consider the 'forward' or 'downward' case: if we encounter any
  key whose preceding subpath contains the full path to any previously encountered
  key, then abort the entire program and throw an error as the input is invalid.

So what does valid input look like?

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -6 | sed '/variants$/d' | python trie_walk.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .video_info .aspect_ratio
                                                   .duration_millis
                                                               .bitrate
                                                               .content_type
                                                               .url
```

There's a bug here. The output should be:

```
.[] .tweet .extended_entities .media[] .video_info .aspect_ratio
                                                   .duration_millis
                                                   .variants[] .bitrate
                                                               .content_type
                                                               .url
```

The difference between this (the expected output, which I'll fix now) and
the invalid masked trie output (with the first line ending with `.video_info`)
is the difference between valid and invalid output.

- As far as I can tell so far, valid input will have no 'null children', as
  any descendants must (by the definition of mutually exclusive descendants and
  ancestors) exclude their descendants from a list of filter paths.
- In other words, detecting paths which have these 'null children' will be
  sufficient to validate the masked trie list as input to `build_del_call.py`.

I will call this version of the program `trie_walk_v.py` (v for 'validated').
  - It doesn't seem like you can pass flags while piping over STDIN so I can't simply modify the behaviour
    of the existing program with a `-v` flag

Firstly, to see the nested dict structure of the trie built from an invalid input,
we'll pipe it into jq which gives a JSON-style whitespacing:

We want to reject this 2 line input:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | head -11 | tail -2 | cut -d\` -f2
```
⇣
```STDOUT
.[] .tweet .entities .media[] .sizes
.[] .tweet .entities .media[] .sizes .large
```

because the first line has a "null child", the "null" sibling of the key ".large".

When this input is processed into a trie, we get:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | head -11 | tail -2 | cut -d\` -f2 | python summarise_paths.py
```
⇣
```STDOUT
{'.[]': {'.tweet': {'.entities': {'.media[]': {'.sizes': {None: None, '.large': {None: None}}}}}}}
```

and to make this structure clearer to read, we can `sed` it into pseudo-JSON (i.e. make it
sufficiently JSON-like for `jq` to parse it and pretty print it indented by dict nesting level):

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | head -11 | tail -2 | cut -d\` -f2 | python summarise_paths.py | sed 's/None/"None"/g' | sed "s/'/\"/g" | jq .
```
⇣
```STDOUT
{
  ".[]": {
    ".tweet": {
      ".entities": {
        ".media[]": {
          ".sizes": {
            "None": "None",
            ".large": {
              "None": "None"
            }
          }
        }
      }
    }
  }
}
```

Which makes the null sibling very clear: this prints the keys in blue and values in green.
There are only two values (shown in green), both of which are `None` (the only value in our trie,
the `_end` signal), but whereas the value at the "deepest" level is an "only child" (the only
entry "child" inside the "parent" dict whose key is `.large`), the other 'null entry' is a sibling,
the 'null sibling' of the key `.large`.

- A "null entry" means an entry (i.e. a key-value pair) where both key and value are `None`
  - "has a null child" means "contains a key which is `None`, the value of which is also `None`"
- A "null sibling" means an entry which is both a 'null child' and the 'sibling' of a non-null entry
  - where 'sibling' means any entry sharing the same 'parent' key (i.e. an entry which is not an "only child")
  - where 'non-null entry' means any entry whose key is not `None` (but with no implication of this key's value).

So what we have is the same null entry, `"None": "None"`, either

- as an "only child" (i.e. the singleton entry of a dict), or
- as a "null sibling"
  - I previously called this "null sibling" a "null child" to emphasise the interpretation of its parent key,
    but now I wish to emphasise the role of its sibling key
    - (which will always occur 'after' the null entry, i.e. arise from a line below the line
       which produced the null sibling, due to the input file being lexicographically sorted).

In short, we can detect an invalid input when we detect any attempt to insert any key whatsoever after
(i.e. as a sibling to) a null entry (the null 'child' entry of the shared 'parent' key).

Phrased in another way, we want to require every null entry in our trie to be a singleton entry (or "only child").

In terms of Python's `dict` data structure, this will mean that we want to require every null entry in our trie
to be at the "deepest level": not globally but for the rooted path in the trie up to that null node. One way then
to phrase this requirement in computational terms is to require the `dict` to 'close' upon encountering a null entry,
and not reopen that key. This can be implemented as closing the parent key then throwing an error if the key is reopened.

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | head -11 | tail -2 | cut -d\` -f2 | python trie_walk_v.py -
```
⇣

> ValueError: Invalid input: ".[] .tweet .entities .media[] .sizes"
> is both a UKP path and a subpath above the key ".large"


To return to the earlier example with 3 levels:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -7 | python trie_walk_v.py -
```
⇣

> ValueError: Invalid input: ".[] .tweet .extended_entities .media[] .video_info"
> is both a UKP path and a subpath above the key ".aspect_ratio"

...and when that input is made valid by removing the path to the 'variants' key:

```sh
grep -v "\- \[x\]" ukp_manifest.md | grep "\[\].*\[\]" | cut -d\` -f2 | tail -6 | sed '/variants$/d' | python trie_walk_v.py -
```
⇣
```STDOUT
.[] .tweet .extended_entities .media[] .video_info .aspect_ratio
                                                   .duration_millis
                                                               .bitrate
                                                               .content_type
                                                               .url
```

We get the masked trie output without `ValueError` thrown, as this is valid input.

Now however it's clear that the bug that masks `variants[]` isn't caused by reading the line ending
with the `variants` key, as it still occurs after removing this line with `sed '/variants$/d'`.
