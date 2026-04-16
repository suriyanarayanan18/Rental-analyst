# V1 Code (Before Anti-Hallucination Fixes)

This folder contains the original V1 code with 5 agents and no hallucination safeguards.

**Do not run this version for production analysis.** It is preserved here to demonstrate how the system evolved.

## What's different from the main (V2) code

- 5 agents instead of 6 (no Validation Agent)
- No [FROM DATA] / [HYPOTHESIS] labeling
- No data availability warnings in task prompts
- No confidence tags in data tool outputs
- Agents told to "quantify impact" without data constraints

## Files

- `main.py` - Original entry point (5 agents)
- `agents.py` - Original agent definitions without anti-hallucination rules
- `tasks.py` - Original tasks without confidence context

## To run V1 (for comparison only)

Copy these files to the project root (replacing the V2 versions), ensure data is in `data/`, set your API key, and run `python main.py`. The V1 output will contain hallucinated revenue figures.

See `examples/COMPARISON.md` for the full V1 vs V2 analysis.
