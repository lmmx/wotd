# Removes:
# - .tweet.retweeted
# - .tweet.source
# - .tweet.display_text_range
# - .tweet.id
# - .tweet.truncated
# - .tweet.favorited
# - .tweet.possibly_sensitive

jq '[.[] | del(.tweet ["retweeted", "source", "display_text_range", "id", "truncated", "favorited", "possibly_sensitive"])]' wotd_tweet.json
