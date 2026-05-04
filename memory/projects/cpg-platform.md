# CPG & Retail Intelligent Platform

## Summary
Production-ready end-to-end analytics platform for CPG & Retail. Goes from raw data to a boardroom-ready executive PowerPoint in under 60 seconds.

## Status
✅ Complete & live on GitHub Pages

## Links
- Live: https://jessleung131-prog.github.io/CPG-and-Retail-Intelligent-Platform/
- Code: https://github.com/jessleung131-prog/CPG-and-Retail-Intelligent-Platform

## Key Numbers
- $78.8M revenue modelled (2-year synthetic dataset, online + offline)
- 6.17× Email ROAS (top channel, 8-channel MMM)
- 25,019 CRM contacts tracked
- 8 FastAPI endpoints
- 33 passing tests
- MMM R² = 0.933, MAPE = 1.63% (strong model fit)

## Architecture
1. Synthetic data generation (online sales, offline POS, CRM funnel, media spend)
2. BigQuery warehouse (raw → staging → mart → ML → monitoring)
3. Forecasting models (Prophet + XGBoost, 70/15/15 chronological split)
4. MMM (Ridge regression, geometric adstock, Hill saturation, 8 channels: Paid Search, FB/IG, TikTok, Reddit, Display, TV/CTV, Email, Influencer)
5. FastAPI dashboard (8 endpoints, lru_cache, reliability warnings)
6. Claude AI insights (claude-opus-4-6, structured JSON output)
7. Executive PPTX deck (python-pptx, --upload flag for Google Slides)
8. Monitoring (anomaly detection, freshness checks, Slack alerts)

## Files
- `docs/index.html` — interactive HTML showcase (GitHub Pages)
- `docs/CPG_Retail_Platform_Showcase.pptx` — 12-slide showcase deck
- `docs/linkedin_thumbnail.png` — LinkedIn project thumbnail
- `TASKS.md` — task tracker
