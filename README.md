Analysis of WOTD data from Tweets marked #WordOfTheDay from my Twitter account

- Twitter search: [`#WordOfTheDay from:permutans`](https://twitter.com/search?q=%23WordOfTheDay%20from%3Apermutans)

# Preprocessing

For detailed preprocessing instructions see [PREPROCESSING.md](PREPROCESSING.md)

```sh
function trivialjs2json () { tail -c +$(echo 3 + $(grep -b -o "=" <<<"$(head -1 $@)" | cut -d: -f1) | bc) $@; }

trivialjs2json tweet.js | jq '[.[] | select(.tweet .full_text | index("#WordOfTheDay") >= 0)]' > wotd_tweet.json
```
