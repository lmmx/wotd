Analysis of WOTD data from Tweets marked #WordOfTheDay from my Twitter account

- Twitter search: [`#WordOfTheDay from:permutans`](https://twitter.com/search?q=%23WordOfTheDay%20from%3Apermutans)

# Preprocessing

For detailed preprocessing instructions see [PREPROCESSING.md](PREPROCESSING.md), which
in summary consists of the following to produce `wotd_tweet.json` from `tweet.js` (a file provided by Twitter):

```sh
function js2json () { tail -c +$(echo 3 + $(grep -b -o "=" <<<"$(head -1 $@)" | cut -d: -f1) | bc) $@; }

jq '[.[] | select(.tweet .entities .hashtags[] .text | test("wordoftheday"; "i"))]' <<<$(js2json tweet.js) > wotd_tweet.json
```
