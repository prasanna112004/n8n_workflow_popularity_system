# scripts/score_and_dedupe.py
import json, os, math, re
from collections import defaultdict

DATA_IN = os.path.join("data", "sample_workflows.json")
DATA_OUT = os.path.join("data", "sample_workflows_scored.json")

def norm_title(t):
    if not t: return ""
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s\-\&\>]+", "", t)   # remove punctuation
    t = re.sub(r"\s+", " ", t).strip()
    return t

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0

def compute_youtube_raw(views, like_ratio, comment_ratio):
    # views compressed with log10
    v_term = 0.6 * math.log10(views + 1)
    l_term = 0.25 * (like_ratio * 100.0)
    c_term = 0.15 * (comment_ratio * 100.0)
    return v_term + l_term + c_term

def compute_for_discourse(metrics):
    # metrics: dict with replies, views, likes, contributors
    replies = safe_float(metrics.get("replies", 0))
    views = safe_float(metrics.get("views", 0))
    likes = safe_float(metrics.get("likes", 0))
    contributors = safe_float(metrics.get("contributors", 0))
    # create proxy ratios
    reply_ratio = replies / (views + 1)
    like_ratio = likes / (views + 1)
    contrib_term = math.log10(contributors + 1)
    # scale similar to youtube raw
    raw = 0.5 * math.log10(views + 1) + 0.3 * (like_ratio * 100.0) + 0.2 * (reply_ratio * 100.0) + 0.1 * contrib_term
    return raw

def main():
    if not os.path.exists(DATA_IN):
        print("Input data not found at", DATA_IN)
        return
    with open(DATA_IN, "r", encoding="utf-8") as f:
        rows = json.load(f)

    grouped = defaultdict(list)
    # Group by normalized title (dedupe strategy)
    for r in rows:
        key = norm_title(r.get("workflow") or r.get("source_url") or "")
        grouped[key].append(r)

    cleaned = []
    raw_scores = []

    for key, items in grouped.items():
        # pick best candidate per group as base (highest raw views or replies)
        best = None
        for it in items:
            if best is None:
                best = it
                continue
            # choose by views (YouTube) or replies (Discourse) or length
            v1 = safe_float(best.get("popularity_metrics", {}).get("views", 0))
            v2 = safe_float(it.get("popularity_metrics", {}).get("views", 0))
            # fallback: replies
            if v2 > v1:
                best = it

        rec = dict(best)  # shallow copy
        pm = rec.setdefault("popularity_metrics", {})

        # Ensure ratios exist
        if rec.get("platform","").lower() == "youtube":
            views = safe_float(pm.get("views", 0))
            likes = safe_float(pm.get("likes", 0))
            comments = safe_float(pm.get("comments", 0))
            like_ratio = likes / views if views else 0.0
            comment_ratio = comments / views if views else 0.0
            pm["like_to_view_ratio"] = round(like_ratio, 6)
            pm["comment_to_view_ratio"] = round(comment_ratio, 6)
            raw = compute_youtube_raw(views, like_ratio, comment_ratio)
        else:
            # discourse or other
            raw = compute_for_discourse(pm)

        rec["_raw_score"] = raw
        raw_scores.append(raw)
        cleaned.append(rec)

    # normalize raw scores to 0-100
    if raw_scores:
        min_r = min(raw_scores)
        max_r = max(raw_scores)
        span = max_r - min_r if max_r != min_r else 1.0
        for rec in cleaned:
            raw = rec.get("_raw_score", 0.0)
            norm = (raw - min_r) / span
            rec["score"] = round(norm * 100.0, 2)
            rec.pop("_raw_score", None)

    # sort by score desc
    cleaned.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    with open(DATA_OUT, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"WROTE {len(cleaned)} cleaned records to {DATA_OUT}")

if __name__ == "__main__":
    main()