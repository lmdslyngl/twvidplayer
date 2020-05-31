
from typing import List, Dict
import sys
import json
from functools import lru_cache, wraps
from datetime import datetime
from base64 import b64encode

import requests
import requests_oauthlib

from util import get_logger


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
def __load_token() -> dict:
    with open("token.json", "r") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def __create_auth() -> requests_oauthlib.OAuth1:
    token = __load_token()
    return requests_oauthlib.OAuth1(
        token["api_key"],
        token["api_key_secret"],
        token["access_token"],
        token["access_token_secret"])


@lru_cache(maxsize=1)
def __get_token() -> str:
    get_logger().info("__get_token is called.")

    token = __load_token()
    encoded_key = b64encode(
        (token["api_key"] + ":" + token["api_key_secret"]).encode("ascii")).decode("ascii")

    url = "https://api.twitter.com/oauth2/token"
    params = {"grant_type": "client_credentials"}
    headers = {
        "Authorization": "Basic " + encoded_key,
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }

    r = requests.post(url, params=params, headers=headers)
    if r.status_code != 200:
        raise TwAPIException(r.text)

    return r.json()["access_token"]


@RateLimitWrapper.wrap("search")
def search(
        q: str,
        count=100,
        since_id: int = None,
        max_id: int = None) -> dict:

    url = "https://api.twitter.com/1.1/search/tweets.json"
    headers = {"Authorization": "Bearer " + __get_token()}
    params = {
        "q": q,
        "count": count,
        "result_type": "recent",
        "tweet_mode": "extended"
    }
    if since_id is not None: params["since_id"] = since_id
    if max_id is not None: params["max_id"] = max_id

    r = requests.get(url, params=params, headers=headers)

    if r.status_code == 429:
        raise TwAPIRateLimited.create_from_response(r)
    elif r.status_code != 200:
        raise TwAPIException(r.text)

    search_result = r.json()

    msg = "API called: search, q={}, since_id={}, max_id={}, result_count={}".format(
        q, since_id, max_id, len(search_result["statuses"]))
    get_logger().info(msg)

    return search_result


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
