# Preamble

The notes below document my reasoning while exploring Twitter JSON. I later came to realise
that a lot of my initial approach was wrong, for example `delpaths` annuls the value of a key,
and I wanted `map(del(array_of_paths))` instead.

The script 'dejunk.sh' was intended to remove many of the
components of the JSON in `wotd_tweet.json` and produce `wotd_tweet_dejunked.json`

I discovered some features of `jq` while writing this, for instance the (`jq`)
command `unique` can replace the Unix tool `uniq` (and it sorts too).

I figured out towards the end of this initial exploration that the way to delete keys
which are not always present is more complicated, see the next step ([AUDIT.md](AUDIT.md))

Links that explain what this data means and how to use `jq` are in [DOCS.md](DOCS.md)

To that effect, the notes below are to be taken with a pinch of salt, as
the 'workings out' during an exploration. They may be useful if you want
an idea about either Twitter's JSON format or use of `jq`.

# Dejunking process: initial pass at munging Twitter JSON

Neal Rauhauser [says](https://twitter.com/nrauhauser/status/1269841406975074305):

> "There are a wide variety of structures that come back from the Tweepy streaming API - much more than the three cases the documentation shows."
>  which he has enumerated in [this gist](https://gist.github.com/NetwarSystem/4d84981ec080838ddb81da33a3b31a2b)

- The full set of these can be obtained by the following:

```sh
xclip -o | tr ',' '\n' | sed 's/^\s//' | sed 's/\]$//' | tr -d "'" | sort | uniq
```

- I stored them in `all_variable_keys.list` and this list minus the ones I removed is `unexamined_variable_keys.list`

---

- Start line count: 23924

I will be taking an aggressive approach to removing anything not strictly relevant to
my particular interest at this moment, and this may not suit everyone.

- Remove `tweet.retweeted`, whether I retweeted my own tweet (all false)
- Remove `tweet.source`, whether the tweet was sent from mobile app or web app etc.
- Keep `tweet.display_text_range`, "display text range (indexes of tweet text without RT and leading user mentions)"
  - Always length 2, always present
- Remove `tweet.display_text_range` after checking that it can be determined in Python
  - Firstly, determine that the start index is always 0:

```sh
jq '.[] .tweet .display_text_range[0]' wotd_tweet.json | uniq
```

  - Secondly, check that the end index is always just the length of the string:
    - (This isn't fast, but it's just to check an intuition and only done once to confirm)

```sh
end_indexes=($(jq -r '.[] .tweet .display_text_range[1]' wotd_tweet.json))
for i in $(seq $( echo "${#end_indexes[@]} - 1" | bc) ); do
  end_index=${end_indexes[$i]}
  tweet=$(jq -r --arg I $i '.[$I | tonumber] .tweet .full_text' wotd_tweet.json)
  python -c "from sys import argv; check = len(argv[1]) == $end_index; print(f'{check} on {argv[2]}')" "$tweet" "$i"
done
```

- Keep `tweet.favorite_count` (not all zero)

```sh
jq '.[] .tweet .favorite_count' wotd_tweet.json | sort | uniq -c
```

```STDOUT
    118 "0"
     44 "1"
     22 "2"
      1 "3"
      1 "4"
      2 "5"
```

- Remove `id` after checking that it is the same as `id_str`
  - Note that it is quoted into a string in JSON here
  - The following gives 0 i.e. no difference between the two lists
```sh
jq '.[] .tweet .id' wotd_tweet.json > all_id.list
jq '.[] .tweet .id_str' wotd_tweet.json > all_id_str.list
diff all_id_str.list all_id.list | wc -l
```

- Remove `tweet.truncated` as it's always `false`
  - `jq '.[] .tweet .truncated' wotd_tweet.json | uniq`

- Remove `tweet.favorited` (i.e. whether I favorited my own tweet) as it's always `false`
  - `jq '.[] .tweet .favorited' wotd_tweet.json | uniq`

- Remove `tweet.possibly_sensitive` (i.e. whether I favorited my own tweet) as it's always `false` or `null` (i.e. absent)
  - It's unclear why it's `null` for some rather than just `false`
    - I thought perhaps only those without media, but there are 48 without media
      - these 15 and 33 others (the others having `possibly_sensitive` = `false`)

```sh
jq '.[] | select(.tweet .possibly_sensitive == null) .tweet .entities .media' wotd_tweet.json | uniq -c
jq '.[] | select(.tweet .possibly_sensitive == false) .tweet .entities .media | select (. == null)' wotd_tweet.json | uniq -c
```

- Keep `tweet.created_at` (the date and time of tweet publication)
- Keep `tweet.full_text` (the tweet text)
- Keep `tweet.lang` (even though it misdetects the language, it detects French excerpts correctly)

```sh
jq '.[] .tweet .lang' wotd_tweet.json | sort | uniq -c
```

```STDOUT
      2 "ca"
    172 "en"
      3 "fr"
      4 "ro"
      7 "und"
```

  - Language codes taken from [docs here](https://developer.twitter.com/en/docs/tweets/rules-and-filtering/overview/premium-operators)
    and saved as a CSV file using:

```sh
xclip -o | sed '/^\s*$/d' | sed -E 's/^\s*//' | sed -E 's/\s*$//' | sed 's/\s-\s/,/' > lang_bcp_codes.csv
```

  - Then examine each "non-English language" tweet, by language

```sh
langs=($(jq -r '[.[] .tweet .lang | select(. != "en")] | unique | .[]' wotd_tweet.json))
for lang in ${langs[@]}; do
  clear
  echo "Language: $lang"
  jq --arg L $lang '.[] | select(.tweet .lang == $L) .tweet .full_text' wotd_tweet.json
  read dummyvar
  clear
done
```

  - "ca" appears to be for detected Greek (but not documented as such: Greek is supposed to be "el", maybe ancient Greek?)
  - "fr" is for French (and correctly so)
  - "ro" is for Romanian (semicorrectly for one Czech name, since Czechs are an ethnic minority in Romania, but still not correct),
    and also misdetects Greek and Latin as Romanian
  - "und" are more tweets with a mix of languages, some with both Latin and Greek for example (but all are tweets in English).
  - ...so in conclusion, keep this `tweet.language` key and perhaps try and do a better job of language detection myself.

- Keep `tweet.full_text` (obviously)
- (**TODO**: Not sure how?) Remove `tweet.extended_entities.media.sizes`
  - Just a lot of thumbnail dimensions which aren't relevant as I have the original uncropped/undownsized image files
    in the archive I downloaded.

  - **TODO**: I can't figure out how to delete these, you can't use the iterator `"media[]"` in a `delpaths` array

```sh
jq '.[] | select(.tweet .extended_entities .media != null) .tweet .extended_entities .media[] .sizes' wotd_tweet.json
```

- Keep `tweet.extended_entities` (containing multimedia metadata)

---

The resulting command is in [`dejunk.sh`](dejunk.sh).

- The output from `dejunk.sh` was stored as `wotd_tweet_dejunked.json`

```sh
jq '[.[] | delpaths([ ["tweet", "retweeted"] , ["tweet", "source"] , ["tweet", "display_text_range"] , ["tweet", "id"],
    ["tweet", "truncated"], ["tweet", "favorited"], ["tweet", "possibly_sensitive"] ])]' wotd_tweet.json | wc -l
jq '[.[] | del(.tweet ["retweeted", "source", "display_text_range", "id", "truncated", "favorited", "possibly_sensitive"] )]' wotd_tweet.json
```

To view what changed, we can run `diff` on the JSON before and after

- Note that you can determine that the output consists of the 'old' lines (i.e. in FILE1 not in FILE2, i.e. the keys before but not after) by adding
  the flag `--old-line-format=":%L"` (which will prepend all the lines with a colon, whereas passing the same value as `--new-file-format` will not)

```sh
diff --unchanged-line-format="" <(jq -r '[.[] .tweet | keys | .[]] | unique | .[]' wotd_tweet.json) <(jq -r '[.[] .tweet | keys | .[]] | unique | .[]' wotd_tweet_dejunked.json)
```

```STDOUT
display_text_range
favorited
id
possibly_sensitive
retweeted
source
truncated
```

This matches our aim for `dejunk.sh` (listed in the file's comments), though note it doesn't tell us
that these keys are uniquely present at the path we removed them from under (that is, as keys of the `tweet` object).

To see that, we can use the recursive descent operator `..` to produce every value, and then `select` only the
objects, then list their keys, then filter for uniqueness. We can do that to the original and the dejunked JSON
to determine if the overall key changes match the key changes for the top-level `tweet` object.

```sh
diff --unchanged-line-format="" <(jq -r '[.. | select(type=="object") | keys | .[]] | unique | .[]' wotd_tweet.json) <(jq -r '[.. | select(type=="object") | keys | .[]] | unique | .[]' wotd_tweet_dejunked.json)
```

This gives only 6 values:

```STDOUT
display_text_range
favorited
possibly_sensitive
retweeted
source
truncated
```

The one that's not here is `id`, which means that some object(s) other than `tweet` use `id` as a key too!

---

The following command will enumerate all paths and summarise exact paths into inexact paths:

- Note we access the `tweet` object before calling `paths`, so all paths are below `.[] .tweet`

```sh
jq '[[.[] .tweet | paths | map(tostring) | join(" .")] | unique | .[] | ".\(.)" |
    gsub(" .[0-9]"; "[]")] | unique | .[]' wotd_tweet_dejunked.json
```

Lastly it just needs to ignore the lines ending on an inexact path (as these are not paths to any specifically named key)

- This is possible as the last part of these paths will be a number (an array index) rather than a string (a key name),
  which can be replaced and merged with the parent key as an iterator parens (from `.parent_key .0` to `.parent_key[]`)

```sh
jq '[[.[] .tweet | paths | select(last | type != "number") | map(tostring) |
    join(" .")] | unique | .[] | ".\(.)" | gsub(" .[0-9]"; "[]")] | unique | .[]' wotd_tweet_dejunked.json
```

```STDOUT
...
".entities .user_mentions[] .indices"
".entities .user_mentions[] .name"
".entities .user_mentions[] .screen_name"
...
```

- If you instead wanted that as array-style paths (i.e. `["a", "b", "c[]", "d"]` rather than `.a .b .c[] .d` style paths),
  you'd use the following:

```sh
jq -c '[[.[] .tweet | paths | select(last | type != "number") | map(tostring) | join(" ")] |
    unique | .[] | gsub(" [0-9]"; "[]") ] | unique | .[] | split(" ")' wotd_tweet_dejunked.json
```

```STDOUT
...
["entities","user_mentions[]","indices"]
["entities","user_mentions[]","name"]
["entities","user_mentions[]","screen_name"]
...
```

Note that these paths are 'inexact', they iterate over 'numeric keys' (i.e. not really keys, but indices of an array),
such as the array `user_mentions` above.

- **Edit** I originally wrote the `paths` call above as `paths(..)` but the recursive descent does not do what I thought it did!
  - Importantly, any argument to `paths` discards any paths that have a `false` value.
  - In addition, the recursive descent produces unrooted paths, making the number of UKPs appear much greater.

Inexact paths can be 'expanded out' to the individual paths (which the `gsub` call removes in the previous 2 `jq` commands),
but it is useful to keep them 'inexact' like this for the purpose of review before passing to a `delpaths` call if we
then decide to remove them.

This is slightly more complex, so I end the first pass 'dejunking' step at this point, and
will do a thorough 'audit' of all these paths in the next step, [AUDIT.md](AUDIT.md)

To facilitate the next step, the following command makes a 'checklist' of the UKPs:

```sh
jq '[[.[] .tweet | paths | select(last | type != "number") | map(tostring) | 
    join(" .")] | unique | .[] | ".\(.)" | gsub(" .[0-9]"; "[]")] | unique |
    .[] | "- [ ] `.[] .tweet \(.)`"' wotd_tweet.json > ukp_manifest.md
```

Then to get it started, just manually check off the 7 paths already chosen
to be filtered out of the JSON. See [AUDIT.md](AUDIT.md) for the rest of this process.

---




As a final query, let's find out what the other paths are that end in an `id` key:

```sh
jq '[[.[] .tweet | .. | paths | select(last == "id") | map(tostring) |
    join(" .")] | unique | .[] | ".\(.)" | gsub(" .[0-9]"; "[]")] | unique | .[]' wotd_tweet_dejunked.json
```

```STDOUT
".entities .media[] .id"
".entities .user_mentions[] .id"
".extended_entities .media[] .id"
```

The answer is `media` and `user_mentions` objects.

We can inspect the first of these `.entities .media[] .id` like so, being careful to `select` only the subset which
have (with `has`) the elements in the path we want (to avoid an error being thrown):

```sh
jq '[.[] | select(.tweet | has("entities")) | select(.tweet .entities | has("media")) |
    select(.tweet .entities .media[] | has("id")) | .tweet .entities .media[]]' wotd_tweet_dejunked.json
```

Querying its length shows that 140 of the 188 WOTD tweets have such an `id` key (for a `media` object in `tweet.entities`),
and upon inspecting the first one of them it is clearly _not_ the `id` of a tweet status, but rather a unique ID given
to a photo attached to a tweet with a different `id`. This is important to know!

```sh
jq '[.[] | select(.tweet | has("entities")) | select(.tweet .entities | has("media")) |
    select(.tweet .entities .media[] | has("id")) | .tweet .entities .media[]] | .[0]' wotd_tweet_dejunked.json | head
```

```STDOUT
{
  "expanded_url": "https://twitter.com/permutans/status/1268105099404083200/photo/1",
  "indices": [
    "278",
    "301"
  ],
  "url": "https://t.co/k0yoHRM2Je",
  "media_url": "http://pbs.twimg.com/media/EZk22MXWoAELL-V.jpg",
  "id_str": "1268105074741518337",
  "id": "1268105074741518337",
```

Note how this media `id` (ending in `3200`) is not the tweet status `id` (ending in `8337`), though
they both begin in `12681050` (suggesting they're generated at the same time by the same identifier system).

The same command as for `entities` but with `extended_entities` shows a very similar `id` (as I'd expect).
In fact, the 0th `media` item is identical to the 0th `media` item of the `entities`, but the 1st `media`
item of the `extended_entities` is the metadata for the 2nd photo attachment.

- i.e. The 0th `media` object in `extended_entities` duplicates the 0th/only `media` object of `entities`,
  as its name might suggest.

- The [0-based] 1st `media` object of `extended_entities` (i.e. the metadata of the 2nd photo
  if we count in 1-based numbers) has the same `expanded_url` as the 0th `media` object, in other words
  this URL shows all the images (despite how the URL ends in `/photo/1` this doesn't indicate an index within the photoset).

- The `media_url` key of this `media` object shares a prefix of 5 characters with the same key of the previous object in the same photoset.

```STDOUT
{
  "expanded_url": "https://twitter.com/permutans/status/1268105099404083200/photo/1",
  "indices": [
    "278",
    "301"
  ],
  "url": "https://t.co/k0yoHRM2Je",
  "media_url": "http://pbs.twimg.com/media/EZk22lKWAAAZkV7.jpg",
  "id_str": "1268105081397837824",
  "id": "1268105081397837824",
```

Lastly, the same command run for `user_mentions` instead of `media` (since the path is otherwise identical)
shows that the `id` for a mentioned user is much shorter (so probably not from the same identifier system as above):

```STDOUT
{
  "name": "CCFC",
  "screen_name": "commercialfree",
  "indices": [
    "34",
    "49"
  ],
  "id_str": "30001583",
  "id": "30001583"
}
```
