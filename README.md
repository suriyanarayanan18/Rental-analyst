# rental-analyst

A multi-agent Airbnb analytics system built with CrewAI and Claude. Now with anti-hallucination safeguards.

## The Story

**V1:** I built a 5-agent system to analyze 45K Airbnb listings in LA. It produced a polished executive report claiming "$40M in annual revenue at risk" with an "11:1 ROI" recovery plan. Impressive, except the revenue figures were completely fabricated. The calendar price column was 100% null, meaning no revenue calculation was possible. The agents confidently invented numbers that didn't exist in the data.

**V2:** I traced the exact hallucination chain across all 5 agents, identified three root causes (missing prompt constraints, no validation layer, lost data provenance), and engineered fixes at every level. The result is a system that explicitly labels what it knows vs what it's guessing, and refuses to fabricate numbers when data is missing.

## What Changed (V1 to V2)

| Layer | V1 Problem | V2 Fix |
|-------|-----------|--------|
| Agent prompts | "Quantify the impact" with no data constraint | "Only cite numbers from data. Label [FROM DATA] vs [HYPOTHESIS]" |
| Architecture | 5 agents, no fact-checking | 6 agents: added Validation Agent between Root Cause and Report Writer |
| Data tools | Raw numbers, no context | Every output tagged with confidence level and data availability warnings |
| Report output | Confident fabrications | Honest uncertainty: "Revenue impact requires pricing data not available in this dataset" |

## Quick Start

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Set your API key
```
# Windows CMD
set ANTHROPIC_API_KEY=your-key-here

# Windows PowerShell
$env:ANTHROPIC_API_KEY="your-key-here"
```

### 3. Download Airbnb data
Go to https://insideairbnb.com/get-the-data/
Download for Los Angeles:
- listings.csv (detailed)
- reviews.csv
- calendar.csv

Place them in the `data/` folder.

### 4. Run the crew
```
python main.py
```

Or with a custom question:
```
python main.py "What neighborhoods have the worst guest experience and why?"
```

## Agents (V2)

| # | Agent | Role | Anti-hallucination constraint |
|---|-------|------|------------------------------|
| 1 | Data Profiler | Data quality lead | Explicitly flags which columns are usable vs null |
| 2 | Pricing Analyst | Pricing strategist | Cannot fabricate revenue figures if price data is null |
| 3 | Sentiment Analyst | Review intelligence | Must state sample size and note findings are indicative |
| 4 | Root Cause Investigator | Diagnostic analyst | Must label every number [FROM DATA] or [HYPOTHESIS] |
| 5 | Validation Agent | Fact-checker (NEW) | Grades every claim as HIGH/LOW/HALLUCINATED confidence |
| 6 | Report Writer | Stakeholder communicator | Only uses validated numbers, removes hallucinated ones |

## Architecture (V2)

```
User Question
    |
    v
[Data Profiler] --> profiles schema + flags data gaps
    |
    v
[Pricing Analyst] + [Sentiment Analyst]  (with data availability context)
    |                    |
    v                    v
[Root Cause Investigator] --> labels [FROM DATA] vs [HYPOTHESIS]
    |
    v
[Validation Agent] --> grades every claim, catches hallucinations  <-- NEW
    |
    v
[Report Writer] --> only uses validated findings
```

## Key Learnings

1. **AI agents hallucinate when optimized for confidence over accuracy.** V1 agents were told to "quantify impact" and they did, even when the data didn't support it. The fix: constrain agents to acknowledge uncertainty.

2. **Hallucinations compound across agent chains.** Agent 4 estimated a number, Agent 5 treated it as fact. By the final report, a fabricated figure looked authoritative. The fix: add a validation layer that traces every number to its source.

3. **Data provenance is lost in text-based agent communication.** When agents pass findings as plain text, the downstream agent can't distinguish "calculated from row counts" from "estimated from assumptions." The fix: tag every number with its source at the data tool level.

## Tech Stack
- CrewAI (multi-agent orchestration)
- Claude Sonnet 4 (via Anthropic API)
- Pandas (data manipulation)
- VADER (sentiment analysis)
- Python 3.10+

## Cost
- CrewAI: Free (open source)
- Airbnb data: Free (Inside Airbnb)
- Claude API: ~$1-2 per full pipeline run
- Total project cost: Under $10
