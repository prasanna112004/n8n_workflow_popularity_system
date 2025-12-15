# collectors/google_trends_collector.py
from pytrends.request import TrendReq
from datetime import datetime
import pandas as pd

pytrends = TrendReq(hl="en-US", tz=360)

def collect_for_keyword(keyword, country="US"):
    """
    Returns Google Trends popularity record for a keyword
    """
    try:
        geo = "US" if country == "US" else "IN"
        pytrends.build_payload(
            kw_list=[keyword],
            timeframe="today 3-m",
            geo=geo
        )
        df = pytrends.interest_over_time()
        if df.empty:
            return None

        avg_interest = int(df[keyword].mean())
        recent = df[keyword][-7:].mean()
        older = df[keyword][:7].mean()
        trend_change = int(((recent - older) / max(older, 1)) * 100)

        return {
            "workflow": keyword,
            "platform": "GoogleTrends",
            "popularity_metrics": {
                "avg_interest": avg_interest,
                "trend_30d_change": trend_change
            },
            "country": country,
            "source_url": f"https://trends.google.com/trends/explore?q={keyword}",
            "collected_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        print("Trend error:", keyword, country, e)
        return None