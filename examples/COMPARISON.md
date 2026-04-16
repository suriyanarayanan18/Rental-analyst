# V1 vs V2 Comparison: How Anti-Hallucination Safeguards Changed the Output

## The Experiment

Same dataset. Same question. Same LLM (Claude Sonnet 4). The only difference: V2 added anti-hallucination constraints to agent prompts, a Validation Agent, and confidence-tagged data tools.

## Side-by-Side Results

| Metric | V1 (No Safeguards) | V2 (With Safeguards) | Verdict |
|--------|-------------------|---------------------|---------|
| Listing count | 45,585 | 45,585 | Both correct [FROM DATA] |
| Review count | 1.8M | 1.8M | Both correct [FROM DATA] |
| Occupancy: Dec 2025 | 61.7% | 61.7% | Both correct [FROM DATA] |
| Occupancy: Feb 2026 | 48.7% | 48.7% | Both correct [FROM DATA] |
| Revenue impact | "$40M annual" | "Cannot quantify: price data is null" | V1 hallucinated. V2 correct. |
| Monthly losses | "$3.4M" | Not stated | V1 hallucinated. V2 refused. |
| Investment plan | "$3.5M for 11:1 ROI" | "Collect data before sizing" | V1 hallucinated. V2 honest. |
| Sentiment finding | "-0.99 international guest score" | "500-review sample too small for conclusions" | V1 overstated. V2 cautious. |
| Root cause | "International guest death spiral" | "Seasonal pattern; cause unclear without pricing data" | V1 invented narrative. V2 acknowledged uncertainty. |
| Recommendations | 3 with fake dollar ROI | 3 focused on data collection | V2 more actionable because honest |

## What Caused the Hallucinations in V1

### The Chain Reaction

```
Data Profiler (Agent 1)
  -> Correctly noted calendar price is 100% null
  -> BUT didn't explicitly warn downstream agents

Pricing Analyst (Agent 2)
  -> Received null price warning but was told to "quantify revenue opportunity"
  -> Estimated revenue from general knowledge, not from data

Root Cause Investigator (Agent 4)
  -> Received Agent 2's estimates as "findings"
  -> Had no way to know the numbers were fabricated
  -> Built an elaborate causal narrative around them

Report Writer (Agent 5)
  -> Received the narrative as validated analysis
  -> Presented fabricated numbers as facts
  -> Created specific ROI calculations from fake base figures
```

### Three Root Causes

1. **Prompt problem**: Agents were told to "quantify impact" without being told "only use actual data." They optimized for impressive output over accurate output.

2. **Architecture problem**: No validation layer existed between analysis and reporting. Fabricated numbers flowed unchecked from Agent 4 to Agent 5.

3. **Data provenance problem**: When findings pass between agents as plain text, the source of each number is lost. Agent 5 couldn't distinguish "calculated from 2M calendar rows" from "estimated from assumptions."

## What V2 Fixed

### Layer 1: Prompt Constraints
Every agent now includes:
```
"CRITICAL RULE: Only cite numbers that come directly from the data
provided to you. If data is missing, explicitly state 'cannot be
calculated because [specific data] is unavailable.' Never fabricate
dollar figures. Label every number: [FROM DATA] or [HYPOTHESIS]."
```

### Layer 2: Validation Agent (New)
Agent 5 in V2 is a dedicated fact-checker that:
- Reviews every quantitative claim from all previous agents
- Grades each as HIGH CONFIDENCE, LOW CONFIDENCE, or HALLUCINATED
- Rewrites unsupported claims with honest uncertainty language
- Produces a confidence score for the overall analysis

### Layer 3: Confidence-Tagged Data Tools
Every Python function now outputs data with explicit tags:
```
"Overall occupancy analysis [FROM DATA]:"
"  Occupancy rate: 55.1%"
"  WARNING: Calendar price column is 100.0% null."
"  Revenue calculations are NOT possible. [DO NOT ESTIMATE]"
```

## Key Takeaway

AI agents hallucinate when optimized for confidence over accuracy. The fix is not just better prompts. It requires architectural changes: validation layers, confidence scoring, and data provenance tracking. This is why AI governance matters in production systems.
