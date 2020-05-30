
import sys
import json
from functools import lru_cache

import requests
import requests_oauthlib


class TwAPIException(Exception):
    pass


class TwAPIRateLimited(Exception):
    pass


@lru_cache(maxsize=1)
def __create_auth() -> requests_oauthlib.OAuth1:
    with open("token.json", "r") as f:
        token = json.load(f)

    return requests_oauthlib.OAuth1(
        token["api_key"],
        token["api_key_secret"],
        token["access_token"],
        token["access_token_secret"])


def search(
        q: str,
        count=100,
        since_id: int = None,
        max_id: int = None) -> dict:

    url = "https://api.twitter.com/1.1/search/tweets.json"
    params = {
        "q": q,
        "count": count,
        "result_type": "recent",
        "tweet_mode": "extended"
    }
    if since_id is not None: params["since_id"] = since_id
    if max_id is not None: params["max_id"] = max_id

    r = requests.get(url, params=params, auth=__create_auth())

    if r.status_code == 429:
        raise TwAPIRateLimited(r.text)
    elif r.status_code != 200:
        raise TwAPIException(r.text)

    return r.json()


def main():
    import pprint
    print(json.dumps(search("#深夜の2時間DTM exclude:retweets")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
