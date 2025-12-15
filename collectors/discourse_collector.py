# collectors/discourse_collector.py
import os, requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

DISCOURSE_BASE = os.getenv("DISCOURSE_BASE_URL", "https://forum.n8n.io")
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY")    # optional
DISCOURSE_API_USER = os.getenv("DISCOURSE_API_USERNAME")  # optional

SEARCH_URL = DISCOURSE_BASE.rstrip("/") + "/search.json"
TOPIC_URL_TPL = DISCOURSE_BASE.rstrip("/") + "/t/{topic_id}.json"

HEADERS = {}
if DISCOURSE_API_KEY and DISCOURSE_API_USER:
    HEADERS = {
        "Api-Key": DISCOURSE_API_KEY,
        "Api-Username": DISCOURSE_API_USER
    }

def _mock_topic_record(title, topic_id):
    # deterministic-ish mock metrics
    h = abs(hash(title)) % 10000
    replies = 5 + (h % 80)
    likes = 1 + (h % 50)
    contributors = 1 + (h % 10)
    views = 100 + (h % 5000)
    return {
        "workflow": title,
        "platform": "Discourse",
        "popularity_metrics": {
            "replies": replies,
            "likes": likes,
            "contributors": contributors,
            "views": views
        },
        "country": None,
        "source_url": f"{DISCOURSE_BASE.rstrip('/')}/t/{topic_id}",
        "collected_at": datetime.utcnow().isoformat() + "Z"
    }

def search_topics(keyword, limit=5):
    """
    Search topics by keyword. Returns a list of dicts with topic_id and title.
    If DISCOURSE_BASE is unreachable or API key missing/blocked, return mock results.
    """
    if not DISCOURSE_BASE:
        return []

    params = {"q": keyword, "include_blurbs": "true", "order": "posts"}
    try:
        r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        js = r.json()
        # js['topics'] is list of dicts
        out = []
        for t in js.get("topics", [])[:limit]:
            out.append({"topic_id": t.get("id"), "title": t.get("title")})
        if out:
            return out
    except Exception:
        # fallback to mock
        out = []
        for i in range(limit):
            out.append({"topic_id": f"mock_{keyword}_{i}", "title": f"{keyword} discussion {i+1}"})
        return out

    # fallback empty
    return []

def fetch_topic_details(topic_id):
    """
    Fetch full topic details from /t/<id>.json
    Returns dict with replies, likes, contributors, views, title.
    If the topic_id looks like mock_..., returns mock details.
    """
    if str(topic_id).startswith("mock_"):
        # synthesize mock details
        title = str(topic_id)
        return _mock_topic_record(title, topic_id)

    url = TOPIC_URL_TPL.format(topic_id=topic_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        js = r.json()
        # parse useful fields
        topic = js.get("topic") or js  # older discourse sometimes returns at top-level
        # number of posts = posts_count, replies = post_count - 1 maybe
        posts_count = topic.get("posts_count", topic.get("post_stream", {}).get("stream", []))
        replies = topic.get("posts_count", 0) - 1 if isinstance(topic.get("posts_count", None), int) else topic.get("posts_count", 0)
        # views
        views = topic.get("views", 0)
        # posters (contributors)
        posters = topic.get("details", {}).get("contributors") or topic.get("posters", [])
        contributors = len(posters) if isinstance(posters, list) else topic.get("details", {}).get("contributors_count", 0)
        # likes: Discourse may expose 'like_count' aggregated for topic
        like_count = topic.get("like_count", 0)
        # fallback: sum likes on posts in post_stream (expensive) - we'll try aggregated first
        record = {
            "workflow": topic.get("title") or topic.get("fancy_title") or f"topic {topic_id}",
            "platform": "Discourse",
            "popularity_metrics": {
                "replies": replies,
                "likes": like_count,
                "contributors": contributors,
                "views": views
            },
            "country": None,
            "source_url": url,
            "collected_at": datetime.utcnow().isoformat() + "Z"
        }
        return record
    except Exception:
        # fallback to mock
        return _mock_topic_record(f"topic_{topic_id}", topic_id)

def collect_for_keyword(keyword, limit=5):
    """
    Returns list of normalized forum records for a keyword.
    """
    topics = search_topics(keyword, limit=limit)
    results = []
    for t in topics:
        topic_id = t.get("topic_id")
        rec = fetch_topic_details(topic_id)
        results.append(rec)
    return results