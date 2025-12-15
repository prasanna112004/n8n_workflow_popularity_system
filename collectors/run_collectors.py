# collectors/run_collectors.py
import os, json
from datetime import datetime
from collectors.youtube_collector import collect_for_keyword as yt_collect
from collectors.discourse_collector import collect_for_keyword as forum_collect
from collectors.google_trends_collector import collect_for_keyword as trends_collect

SEED_KEYWORDS = [
    "gmail automation", "google sheets", "slack integration",
    "whatsapp reminders", "twilio sms", "airtable sync",
    "shopify orders", "pdf parsing", "webhook", "jira automation"
]

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_workflows.json")

def run_youtube_collect(max_per_keyword=2):
    records = []
    for kw in SEED_KEYWORDS:
        for region in ("US", "IN"):
            try:
                items = yt_collect(kw, regionCode=region, maxResults=max_per_keyword)
                for it in items:
                    if not it.get("collected_at"):
                        it["collected_at"] = datetime.utcnow().isoformat() + "Z"
                    records.append(it)
            except Exception as e:
                print(f"YT Error collecting for {kw} {region}: {e}")
    return records

def run_forum_collect(max_per_keyword=3):
    records = []
    for kw in SEED_KEYWORDS:
        try:
            items = forum_collect(kw, limit=max_per_keyword)
            for it in items:
                if not it.get("collected_at"):
                    it["collected_at"] = datetime.utcnow().isoformat() + "Z"
                records.append(it)
        except Exception as e:
            print(f"Forum Error collecting for {kw}: {e}")
    return records

def run_trends_collect():
    records = []
    for kw in SEED_KEYWORDS:
        for country in ("US", "IN"):
            rec = trends_collect(f"n8n {kw}", country)
            if rec:
                records.append(rec)
    return records

def save_records(records):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"WROTE {len(records)} records to {OUTPUT_PATH}")

if __name__ == "__main__":
    recs = []
    recs.extend(run_youtube_collect(max_per_keyword=2))
    recs.extend(run_forum_collect(max_per_keyword=3))
    recs.extend(run_trends_collect())
    save_records(recs)