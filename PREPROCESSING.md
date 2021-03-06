- Download your Twitter account archive, unzip, and make a copy of the file 'tweet.js' as 'tweet.json'
- On the first line, remove the variable assignment, i.e. change the line:

```js
window.YTD.tweet.part0 = [ {
```

  to the line

```json
[ {
```

- You must leave the `[` there as it signals the start of the list of tweets (to make valid JSON)
- You can verify the JSON file is valid with `jq` (pipe the result to `/dev/null` to prevent it clogging STDOUT)
  - `jq . tweet.json > /dev/null` will report an error if invalid json
  - `echo $?` will report the error code afterwards (0 if "the last output values was neither false nor null" [sic])
  - Exit code interpretation (allegedly `-e` is needed but I found it gave them without): https://stackoverflow.com/questions/46954692/check-if-string-is-a-valid-json-with-jq

---

There are a lot of Javascript files here that are just lists, and we can read any of them as such by omitting the first N characters
up to the list or dictionary start by getting the index of the equals symbol then reading the rest of the file as a string into `jq`


To get the index of the equals symbol:

```sh
grep -b -o "=" <<<"$(head -1 tweet.js)" | cut -d: -f1
```

- The `tail -c +NUM` outputs "starting with byte NUM", and this is 1-based index (i.e. NUM=1 will output the full file)
  - Not mentioned in the man pages, but using the above command with `NUM` of 0 vs. 1 shows no difference
  - `grep -b -o` gives the zero-based byte offset, i.e. we must add 1 to the output to pass it as the `NUM` value to `tail -c +NUM`
  - ...`grep -b -o` gives the offset of "the matching part itself", so to get the character afterwards we want to add a further 1 to the output index
  - ...and since these files have a space after the assignment, we want to add a further 1 to the output index
- Therefore to remove the `=` assignment preamble we must pass `tail -c +NUM` a value of NUM equal to the `grep -b -o` index plus 3 (since 1 + 1 + 1 = 3)

```sh
echo 3 + $(grep -b -o "=" <<<"$(head -1 tweet.js)" | cut -d: -f1) | bc
```

So in conclusion, we get the tail statement to offset a Javascript file to be fed as JSON to jq:

```sh
tail -c +$(echo 3 + $(grep -b -o "=" <<<"$(head -1 tweet.js)" | cut -d: -f1) | bc) tweet.js
```

Note that this requires typing out the filename twice, so we may as well make a function

```sh
function trivialjs2json () { tail -c +$(echo 3 + $(grep -b -o "=" <<<"$(head -1 $@)" | cut -d: -f1) | bc) $@; }
```

We can then check all Javascript files become valid JSON:

```sh
for jsfile in *.js; do trivialjs2json $jsfile | jq . > /dev/null; echo $?; done | uniq -c
```

- ⇒ `49 0`
- `find ./ -type f -name "*.js" | wc -l` ⇒ `49` i.e. there are indeed 49 Javascript files provided in the Twitter archive,
  so the above result of 49 exit codes of 0 checks out

---

Now we can actually access the tweets which have the #WordOfTheDay hashtag using jq

This would be expected to provide all the hashtags:

```sh
trivialjs2json tweet.js | jq '.[] .tweet .hashtags'
```

...but it returns a list of `null` (checkable with `uniq`), <strike>because Twitter have given us junk data</strike>

- **Edit** — oops, no, let's try that again

_This_ provides all the hashtags equal to "WordOfTheDay":

```sh
jq '[.[] .tweet .entities .hashtags[] .text | select(. == "WordOfTheDay")] | length' <<<$(trivialjs2json tweet.js)
```

- **Edit** but in fact there are others, we need to be case insensitive:

```sh
jq '[.[] .tweet .entities .hashtags[] .text]' <<<$(trivialjs2json tweet.js)  | sort | uniq -c | sort -rn | grep -i "wordoftheday"
```

```
    182   "WordOfTheDay",
      6   "WordoftheDay",
```

- **Edit** I'll come back to this in an addendum at the end to capture those remaining 6 tweets

```sh
grep "#WordOfTheDay" <<<$(trivialjs2json tweet.js) | wc -l
```

Shows there are 182 tweets with hashtag "#WordOfTheDay" (I thought there'd be more!)

- **Edit** and similarly using "WordoftheDay" there are 6

The rundown of where those hashtags are in the tweet text can be found like so:

```sh
trivialjs2json tweet.js | jq '.[] .tweet .full_text | index("#WordOfTheDay")' | sort -n | uniq -c
```

which shows that other than the 21,000+ tweets without the hashtag, there are:

- 11 tweets which have the hashtag at the start
- 138 tweets which have the hashtag starting at the 4th character (very likely these are all following "The ")
- A few in the range up to around 50 which are probably after a small introduction
- A few in the range of around 100-200 which are probably at the end of the tweet (perhaps before a link)

```
     11 0
  21244 null
    138 4
      1 8
      3 9
      1 15
      2 17
      8 19
      1 20
      1 23
      1 24
      1 32
      1 37
      1 45
      1 51
      1 106
      1 119
      1 124
      1 127
      1 149
      1 150
      1 155
      1 168
      1 201
      1 206
      1 264
```

- **Edit** and for "#WordoftheDay" all 6 were at index 4

So the number of tweets with the WOTD hashtag should be equal to the total tweet count minus 21,244 (the number of `null` matches above)

```sh
jq '.[] .tweet .files | arrays[] .count | tonumber - 21244' <<<$(trivialjs2json manifest.js)
```

...or we can do the same by just counting the tweets 

- Obviously this operation is slower than looking it up in the manifest:

```sh
jq '. | length - 21244' <<<$(trivialjs2json tweet.js)
```

Either gives 182, as does a simple grep query (therefore no tweet has more than one WOTD hashtag):

```sh
grep "#WordOfTheDay" <<<$(trivialjs2json tweet.js) | wc -l
```

---

The preprocessing step is complete after producing a list of WOTD tweets, so to finish, extract these:

- We expect the length of this JSON subset of tweets to be 182

```sh
trivialjs2json tweet.js | jq '[.[] | select(.tweet .full_text | index("#WordOfTheDay") >= 0)] | length'
```

...which gives 182, as expected

- Note that the iterator `.[]` prints out any resulting "matches" without comma-separation, so if
  this isn't "undone" by surrounding the entire jq command in `[]` parenthesis, we won't get a list,
  so we can't get the length of a list (here, the length is 182)

...so finally we will write these tweets to a file:

```sh
trivialjs2json tweet.js | jq '[.[] | select(.tweet .full_text | index("#WordOfTheDay") >= 0)]' > wotd_tweet.json
```

**Edit** — but on second thoughts, since we realised that this doesn't find other cases of the hashtag,
and doesn't use the structured information provided in the `hashtag` key, this is the proper way to do it:

```sh
jq '[.[] | select(.tweet .entities .hashtags[] .text | test("wordoftheday"; "i"))] | length' <<<$(trivialjs2json tweet.js)
```

...which shows 188, as expected from 182 + 6

In fact we can compare the running time of this to searching with a regex in the `full_text` value
and see it is (if only a little) quicker.

...Which finally leads to the corrected way to write these tweets to a file (case insensitively):

```sh
jq '[.[] | select(.tweet .entities .hashtags[] .text | test("wordoftheday"; "i"))]' <<<$(trivialjs2json tweet.js) > wotd_tweet.json
```

As a final note, for tasks where speed is more important, there is also `simdjson`:

- [simdjson](https://simdjson.org/) though `jq` is a nice tool (and preinstalled on my distro!)
