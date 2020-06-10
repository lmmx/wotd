Analysis of WOTD data from Tweets marked #WordOfTheDay from my Twitter account

- Twitter search: [`#WordOfTheDay from:permutans`](https://twitter.com/search?q=%23WordOfTheDay%20from%3Apermutans)

# Preprocessing

For detailed preprocessing instructions see [PREPROCESSING.md](PREPROCESSING.md), which
in summary consists of the following to produce `wotd_tweet.json` from `tweet.js` (a file provided by Twitter):

```sh
function js2json () { tail -c +$(echo 3 + $(grep -b -o "=" <<<"$(head -1 $@)" | cut -d: -f1) | bc) $@; }

jq '[.[] | select(.tweet .entities .hashtags[] .text | test("wordoftheday"; "i"))]' <<<$(js2json tweet.js) > wotd_tweet.json
```

This file was big (188 tweets took up 24,000 lines), so the next step reduced its size by removing surplus info.

The step detailed in [DEJUNK.md](DEJUNK.md) and performed in [`dejunk.sh`](dejunk.sh) reduced `wotd_tweet.json`
from 24,000 lines to 22,000 lines but it was difficult to inspect the JSON tree's full contents
without enumerating all paths given how variable the tweet object structure can be.

- A 'path' here is a rooted path to any key, which I call a "unique key path" or UKP

Following this initial 'dejunk' step, I wanted to get a full account of what was in this JSON,
so I enumerated all the paths (there were 106 of them, I had removed only 7 in the initial 'dejunking'),
and turned these into a 'checklist' to be deleted from the JSON programmatically rather than by manually
writing a `del` command (it'd get very big, and hard to maintain if I wanted to change it later).

For many of these, the paths are 'inexact' i.e. 'globbed', as they're not present in all Tweet objects.
The inexact paths 'expand' to a much larger number of paths (they are 'one-to-many').

This basic auditing step allowed me to confirm that information such as geolocation were not in the JSON,
so I could be confident that uploading the file to GitHub wasn't being oblivious to security concerns
(and will also mean I can remain confident of this in future by inspect this 'UKP manifest').

The step detailed in [AUDIT.md](AUDIT.md) and performed in [`audit.sh`](audit.sh) reduced `wotd_tweet_dejunked.json`
from 12,330 lines to `TBC` lines in the file `wotd_tweet_reconciled.json`.
