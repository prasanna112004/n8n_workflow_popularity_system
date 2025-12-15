Overview

This project builds a Workflow Popularity System for n8n automations, aggregating popularity signals from multiple public platforms and exposing the results through a REST API.

The system identifies popular n8n workflows using real, verifiable evidence such as:
	•	YouTube views, likes, comments, and engagement ratios
	•	n8n Forum (Discourse) thread activity
	•	Google Search interest via Google Trends

All data is real-time, API-driven, country-segmented, and automation-ready.


🎯 Objective

To identify and rank the most popular n8n workflows across platforms using clear, quantitative popularity evidence and expose them via a production-ready API.


📊 Data Sources & Popularity Signals

1️⃣ YouTube (YouTube Data API v3)

Used to analyze n8n tutorial and workflow videos.

Popularity Metrics
	•	View count
	•	Like count
	•	Comment count
	•	Like-to-view ratio
	•	Comment-to-view ratio

Evidence Example

“WhatsApp AI Agent analyzes Google Sheets”
385,000+ views, 16,000+ likes, strong engagement


2️⃣ n8n Forum (Discourse)

Uses the public Discourse API from forum.n8n.io.

Popularity Metrics
	•	Number of replies
	•	Number of likes
	•	Number of contributors
	•	Topic view count

Evidence Example

“Shopify Order Creation Event not triggering”
Active discussion, multiple contributors, consistent views


3️⃣ Google Search (Google Trends)

Uses Google Trends to measure relative search interest and trend momentum.

Popularity Metrics
	•	Average interest score (0–100)
	•	30-day trend change (%)
	•	Country-specific trends (US, India)

Note: Google Trends provides relative, not absolute, search volume — this is industry standard.


🌍 Country Segmentation

All data is segmented by:
	•	🇺🇸 United States (US)
	•	🇮🇳 India (IN)

This allows region-specific popularity insights.


🧠 Popularity Scoring

Each workflow receives a normalized popularity score (0–100).

Scoring Philosophy

Popularity is not just views, but a combination of:
	•	Reach (views)
	•	Engagement quality (likes/views, comments/views)
	•	Community activity (forum replies, contributors)
	•	Search momentum (Google Trends)

Scores are normalized so workflows from different platforms can be compared fairly.
