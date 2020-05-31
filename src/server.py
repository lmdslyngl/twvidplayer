
from typing import Optional, List
import json
from functools import wraps
import traceback
import re

from flask import Flask, request, Response, send_from_directory
import twapi
from util import TwPlayerException, get_logger, init_logger


init_logger()
get_logger().info("Server started.")
app = Flask(
    __name__,
    static_folder="static")


def error_response_on_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except twapi.TwAPIRateLimited as ex:
            traceback.print_exc()
            get_logger().exception(ex)
            return Response(
                json.dumps({
                    "error": "Too many requests. Rate limited.",
                    "error_type": "ratelimit"
                }),
                status=429)
        except Exception as ex:
            traceback.print_exc()
            get_logger().exception(ex)
            return Response(
                json.dumps({
                    "error": "Type: {}\nError: {}".format(type(ex), str(ex)),
                    "error_type": "other"
                }),
                status=500)
    return wrapper


@app.route("/api/search", methods=["GET"])
@error_response_on_exception
def search():
    q = request.args.get("q")

    if "max_id" in request.args:
        max_id = int(request.args.get("max_id")) - 1
    else:
        max_id = None

    for retry_count in range(3):
        search_result = twapi.search(q, max_id=max_id)
        video_tweets = extract_video_tweets(search_result)
        if 0 < len(video_tweets):
            return json.dumps(video_tweets)
        else:
            max_id = search_result["search_metadata"]["max_id"] - 1

    return "[]"


@app.route("/", methods=["GET"])
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/search-newer", methods=["GET"])
@error_response_on_exception
def search_prev():
    q = request.args.get("q")

    if "since_id" in request.args:
        since_id = int(request.args.get("since_id")) + 1
    else:
        raise TwPlayerException("Not specified since_id.")

    for retry_count in range(3):
        search_result = twapi.search(q, since_id=since_id)
        video_tweets = extract_video_tweets(search_result)
        if 0 < len(video_tweets):
            return json.dumps(video_tweets)
        else:
            since_id = search_result["search_metadata"]["since_id"] + 1

    return "[]"


def extract_video_tweets(twapi_search_response: dict) -> dict:
    response_tweets = []
    for tweet in twapi_search_response["statuses"]:
        if "retweeted_status" in tweet:
            # リツイートは除外
            continue

        video_url_candidates = [
            get_video_url_from_tweet(tweet),
            get_soundcloud_url_from_tweet(tweet),
            get_youtube_url_from_tweet(tweet)
        ]
        video_types = ["video", "soundcloud", "youtube"]

        # Twitterビデオ，SoundCloud，Youtubeのいずれか1つのURLを選択
        selected_video_url = None
        for video_url, video_type in zip(video_url_candidates, video_types):
            if video_url is not None:
                selected_video_url = video_url
                break

        # ビデオのURLが無かったときはこのツイートを無視
        if selected_video_url is None:
            continue

        response_tweet = {
            "id": tweet["id_str"],
            "text": tweet["full_text"],
            "author": tweet["user"]["name"],
            "author_screen_name": tweet["user"]["screen_name"],
            "author_thumbnail": tweet["user"]["profile_image_url_https"],
            "video_url": selected_video_url,
            "video_type": video_type
        }
        response_tweets.append(response_tweet)

    return response_tweets


def get_video_url_from_tweet(tweet: dict) -> Optional[str]:
    if "extended_entities" not in tweet:
        return None

    entities = tweet["extended_entities"]
    if "media" not in entities:
        return None

    media_list = entities["media"]
    for media in media_list:
        if media["type"] == "video":
            video_info = media["video_info"]
            video_variants = video_info["variants"]

            # 一番ビットレートの高いvideo/mp4を選択
            video_selected = sorted(
                filter(lambda x: x["content_type"] == "video/mp4", video_variants),
                key=lambda x: x["bitrate"],
                reverse=True)[0]

            return video_selected["url"]

    return None


def get_urls_from_tweet(tweet: dict) -> List[str]:
    if "entities" not in tweet:
        return None

    entities = tweet["entities"]
    if "urls" not in entities:
        return None

    return [url["expanded_url"] for url in entities["urls"]]


def get_soundcloud_url_from_tweet(tweet: dict) -> Optional[str]:
    urls = filter(lambda x: "soundcloud.com" in x, get_urls_from_tweet(tweet))
    try:
        return next(urls)
    except StopIteration:
        return None


def get_youtube_url_from_tweet(tweet: dict) -> Optional[str]:
    urls = filter(lambda x: "youtube.com/watch" in x, get_urls_from_tweet(tweet))
    try:
        return next(urls)
    except StopIteration:
        pass

    # 短縮URL版を探す
    urls = filter(lambda x: "youtu.be" in x, get_urls_from_tweet(tweet))
    try:
        # 短縮URLを展開して返す
        url = next(urls)
        v = re.sub(r".*youtu\.be/(.*)", r"\1", url)
        return "https://www.youtube.com/watch?v=" + v
    except StopIteration:
        return None


if __name__ == "__main__":
    app.run()
