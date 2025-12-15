# collectors/youtube_collector.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # optional; set in .env for real calls
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def _mock_video_record(title, video_id, region):
    # deterministic-ish fake metrics for testing without API key
    h = abs(hash(title)) % 10000
    views = 1000 + h
    likes = max(1, (views // 20) + (h % 50))
    comments = max(0, (views // 200) + (h % 10))
    return {
        "workflow": title,
        "platform": "YouTube",
        "popularity_metrics": {
            "views": views,
            "likes": likes,
            "comments": comments,
            "like_to_view_ratio": round(likes / views, 5) if views else 0.0,
            "comment_to_view_ratio": round(comments / views, 5) if views else 0.0
        },
        "country": "US" if region == "US" else ("IN" if region == "IN" else None),
        "score": None,
        "source_url": f"https://www.youtube.com/watch?v={video_id}",
        "collected_at": None
    }

def search_videos(keyword, regionCode=None, maxResults=3):
    """
    Returns a list of dicts: [{"videoId": "...", "title":"..."}]
    Uses real YouTube Data API if YOUTUBE_API_KEY exists; else returns mock results.
    """
    if not YOUTUBE_API_KEY:
        items = []
        for i in range(maxResults):
            vid = f"mock_{keyword.replace(' ','_')}_{regionCode}_{i}"
            items.append({"videoId": vid, "title": f"{keyword} - demo video {i+1}"})
        return items

    params = {
        "part": "snippet",
        "q": f"{keyword} n8n workflow",
        "type": "video",
        "maxResults": maxResults,
        "key": YOUTUBE_API_KEY
    }
    if regionCode:
        params["regionCode"] = regionCode
    r = requests.get(SEARCH_URL, params=params, timeout=15)
    r.raise_for_status()
    js = r.json()
    items = []
    for it in js.get("items", []):
        vid = it.get("id", {}).get("videoId")
        title = it.get("snippet", {}).get("title")
        if vid and title:
            items.append({"videoId": vid, "title": title})
    return items

def get_video_stats(video_ids):
    """
    video_ids: list[str]
    Returns list of stats dicts: [{"id":id, "views":int,"likes":int,"comments":int, "title": str}]
    If no API key present, returns empty list (caller will use mock).
    """
    if not YOUTUBE_API_KEY:
        return []

    params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    }
    r = requests.get(VIDEOS_URL, params=params, timeout=15)
    r.raise_for_status()
    js = r.json()
    out = []
    for v in js.get("items", []):
        stats = v.get("statistics", {})
        snippet = v.get("snippet", {})
        out.append({
            "id": v.get("id"),
            "title": snippet.get("title"),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)) if stats.get("likeCount") else 0,
            "comments": int(stats.get("commentCount", 0)) if stats.get("commentCount") else 0
        })
    return out

def collect_for_keyword(keyword, regionCode=None, maxResults=3):
    """
    Returns a list of normalized workflow records for the given keyword and region.
    """
    items = search_videos(keyword, regionCode=regionCode, maxResults=maxResults)
    video_ids = [it["videoId"] for it in items]
    stats = []
    if YOUTUBE_API_KEY and video_ids:
        stats = get_video_stats(video_ids)

    results = []
    # if real stats available, use them; else use mock
    if stats:
        for s in stats:
            views = s.get("views", 0)
            likes = s.get("likes", 0)
            comments = s.get("comments", 0)
            results.append({
                "workflow": s.get("title"),
                "platform": "YouTube",
                "popularity_metrics": {
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "like_to_view_ratio": round(likes / views, 5) if views else 0.0,
                    "comment_to_view_ratio": round(comments / views, 5) if views else 0.0
                },
                "country": "US" if regionCode == "US" else ("IN" if regionCode == "IN" else None),
                "score": None,
                "source_url": f"https://www.youtube.com/watch?v={s.get('id')}",
                "collected_at": None
            })
    else:
        # mock mode
        for it in items:
            results.append(_mock_video_record(it["title"], it["videoId"], regionCode))
    return results