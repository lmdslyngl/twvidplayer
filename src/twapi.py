
from typing import List, Dict
import sys
import json
from functools import lru_cache, wraps
from datetime import datetime

import requests
import requests_oauthlib


class TwAPIException(Exception):
    pass


class TwAPIRateLimited(Exception):
    def __init__(self, message: str, reset_time: datetime):
        super().__init__(message)
        self.reset_time = reset_time

    @staticmethod
    def create_from_response(response: requests.Response) -> "TwAPIRateLimited":
        reset_time = int(response.headers.get("x-rate-limit-reset"))
        return TwAPIRateLimited(
            response.text,
            datetime.utcfromtimestamp(reset_time))


class RateLimitWrapper:
    @classmethod
    def get_ratelimit_dict(cls) -> Dict[str, int]:
        if hasattr(cls, "ratelimit_dict"):
            return cls.ratelimit_dict
        else:
            setattr(cls, "ratelimit_dict", {})
            return cls.ratelimit_dict

    @classmethod
    def wrap(cls, api_type: str):
        """ RateLimit中のAPIを呼ばないようにするデコレータ """

        def _wrap(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # RateLimit中かどうか確認する
                ratelimit_dict = cls.get_ratelimit_dict()
                if api_type in ratelimit_dict:
                    reset_time = ratelimit_dict[api_type]
                    if datetime.utcnow() < reset_time:
                        # RateLimit中の場合は，APIを呼ばずにRateLimit例外を投げる
                        raise TwAPIRateLimited("Rate limiting.", reset_time)
                    else:
                        # RateLimitが終了していた場合は，辞書から削除
                        ratelimit_dict.pop(api_type)

                try:
                    return func(*args, **kwargs)
                except TwAPIRateLimited as ex:
                    # RateLimit中だった場合は辞書に登録
                    ratelimit_dict[api_type] = ex.reset_time
                    raise

            return wrapper
        return _wrap


@lru_cache(maxsize=1)
def __create_auth() -> requests_oauthlib.OAuth1:
    with open("token.json", "r") as f:
        token = json.load(f)

    return requests_oauthlib.OAuth1(
        token["api_key"],
        token["api_key_secret"],
        token["access_token"],
        token["access_token_secret"])


@RateLimitWrapper.wrap("search")
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
        raise TwAPIRateLimited.create_from_response(r)
    elif r.status_code != 200:
        raise TwAPIException(r.text)

    return r.json()


def main():
    import pprint
    import time

    ctr = 0
    while True:
        try:
            search("#深夜の2時間DTM", count=1)
            print("succeeded: {}".format(ctr))
        except TwAPIRateLimited as ex:
            print("{}: {}, reset: {}".format(ex, ctr, ex.reset_time))
            time.sleep(1)
        ctr += 1

    # print(json.dumps(search("#深夜の2時間DTM exclude:retweets")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
