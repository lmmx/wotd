# Removes:
# - .tweet .retweeted
# - .tweet .source
# - .tweet .display_text_range
# - .tweet .id
# - .tweet .truncated
# - .tweet .favorited
# - .tweet .possibly_sensitive
# - .tweet .extended_entities

jq '[.[] | delpaths([["tweet", "retweeted"],
		     ["tweet", "source"],
                     ["tweet", "display_text_range"],
                     ["tweet", "id"],
                     ["tweet", "truncated"],
                     ["tweet", "favorited"],
                     ["tweet", "possibly_sensitive"],
                     ["tweet", "extended_entities"]
		    ])]' wotd_tweet.json
