"""
Task definitions for the rental-analyst crew.
Each task maps to an agent and defines what it should produce.

V2: Added Validation Agent task + confidence tags in data context.
"""

from crewai import Task
from tools.data_tools import (
    load_listings,
    load_reviews,
    load_calendar,
    profile_dataset,
    neighborhood_pricing,
    occupancy_analysis,
    pricing_gaps,
    sentiment_sample,
)


def create_tasks(agents: dict, question: str) -> list:
    """Create all tasks with pre-computed data context."""

    # Load data once and generate context strings for agents
    print("\n[Loading data...]")
    listings = load_listings()
    print(f"  Listings: {len(listings):,} rows, {len(listings.columns)} columns")

    reviews = load_reviews()
    print(f"  Reviews: {len(reviews):,} rows")

    calendar = load_calendar()
    print(f"  Calendar: {len(calendar):,} rows")

    # Pre-compute analysis results to pass as context
    print("\n[Running data tools...]")

    listings_profile = profile_dataset(listings, "Listings")
    reviews_profile = profile_dataset(reviews, "Reviews")
    calendar_profile = profile_dataset(calendar, "Calendar")

    hood_pricing = neighborhood_pricing(listings)
    occupancy = occupancy_analysis(calendar)
    price_gaps = pricing_gaps(listings)
    sentiment = sentiment_sample(reviews)

    # Build data availability summary for agents
    cal_price_nulls = calendar["price"].isna().sum() if "price" in calendar.columns else len(calendar)
    cal_price_pct = round(100 * cal_price_nulls / len(calendar), 1) if len(calendar) > 0 else 100

    listing_price_valid = listings["price"].notna().sum() if "price" in listings.columns else 0
    listing_price_pct = round(100 * listing_price_valid / len(listings), 1) if len(listings) > 0 else 0

    data_availability = (
        "=== DATA AVAILABILITY SUMMARY (READ THIS FIRST) ===\n"
        f"Listings price column: {listing_price_pct}% valid ({listing_price_valid:,} of {len(listings):,})\n"
        f"Calendar price column: {100 - cal_price_pct}% valid ({len(calendar) - cal_price_nulls:,} of {len(calendar):,}) "
        f"-- {'USABLE' if cal_price_pct < 50 else 'NOT USABLE: ' + str(cal_price_pct) + '% null'}\n"
        f"Reviews with comments: {reviews['comments'].notna().sum():,} of {len(reviews):,}\n"
        f"Sentiment sample size: 500 of {len(reviews):,} total reviews\n"
        "\nRULES FOR ALL AGENTS:\n"
        "- You can CALCULATE metrics from columns with >50% valid data\n"
        "- You CANNOT calculate revenue/dollar figures if price data is mostly null\n"
        "- Occupancy rates from calendar available/booked status ARE valid\n"
        "- Sentiment scores are from a 500-review sample, NOT the full dataset\n"
        "- Always label: [FROM DATA] for calculated values, [HYPOTHESIS] for interpretations\n"
        "================================================\n"
    )

    print(f"\n  Data availability summary:")
    print(f"    Listing prices: {listing_price_pct}% valid")
    print(f"    Calendar prices: {100 - cal_price_pct}% valid")
    print(f"    Reviews with text: {reviews['comments'].notna().sum():,}")

    print("\n[Data tools complete. Starting agents...]\n")

    # Task 1: Data Profiling
    task_profile = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"{data_availability}\n\n"
            f"Here are the data profiles for all three tables:\n\n"
            f"{listings_profile}\n\n"
            f"{reviews_profile}\n\n"
            f"{calendar_profile}\n\n"
            "Based on these profiles, provide:\n"
            "1. A summary of data quality issues, especially which columns are usable vs not\n"
            "2. Key distributions and patterns you notice\n"
            "3. EXPLICITLY list which analyses are POSSIBLE vs IMPOSSIBLE given data gaps\n"
            "4. Your recommendation for which dimensions to investigate\n\n"
            "IMPORTANT: If calendar price is mostly null, state clearly that revenue/dollar "
            "calculations are NOT possible from this dataset."
        ),
        expected_output=(
            "A structured data quality report covering all three tables, "
            "with specific findings on nulls, outliers, and data quirks. "
            "Must include a clear section on 'What We CAN Calculate' vs "
            "'What We CANNOT Calculate' based on data availability."
        ),
        agent=agents["data_profiler"],
    )

    # Task 2: Pricing Analysis
    task_pricing = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"{data_availability}\n\n"
            f"Here is the neighborhood pricing analysis:\n\n"
            f"{hood_pricing}\n\n"
            f"Here is the pricing gap analysis:\n\n"
            f"{price_gaps}\n\n"
            "Based on this data, provide:\n"
            "1. Which neighborhoods have the biggest pricing problems [FROM DATA]\n"
            "2. How many listings are significantly mispriced [FROM DATA]\n"
            "3. Revenue impact of pricing corrections -- ONLY if price data supports it.\n"
            "   If calendar prices are null, state: 'Revenue impact cannot be calculated "
            "   because daily rate data is unavailable.'\n"
            "4. Specific pricing recommendations by neighborhood\n\n"
            "Label every number: [FROM DATA] or [HYPOTHESIS]"
        ),
        expected_output=(
            "A pricing analysis report with specific neighborhoods flagged, "
            "counts of mispriced listings with [FROM DATA] labels, and "
            "honest acknowledgment of what cannot be calculated."
        ),
        agent=agents["pricing_analyst"],
        context=[task_profile],
    )

    # Task 3: Sentiment Analysis
    task_sentiment = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"{data_availability}\n\n"
            f"Here is the sentiment analysis of guest reviews:\n\n"
            f"{sentiment}\n\n"
            f"Total reviews in dataset: {len(reviews):,}\n"
            f"Sample analyzed: 500 reviews\n\n"
            "Based on this data, provide:\n"
            "1. Overall sentiment health of the marketplace [FROM DATA: 500-review sample]\n"
            "2. What the negative reviews are complaining about [FROM DATA]\n"
            "3. Whether sentiment correlates with any pricing or neighborhood patterns [HYPOTHESIS]\n"
            "4. Recommendations for improving guest satisfaction\n\n"
            "IMPORTANT: Always note that findings are from a 500-review sample out of "
            f"{len(reviews):,} total. This is indicative, not conclusive."
        ),
        expected_output=(
            "A sentiment analysis report with overall scores, key complaint themes, "
            "and actionable recommendations. Must include sample size caveat."
        ),
        agent=agents["sentiment_analyst"],
        context=[task_profile],
    )

    # Task 4: Root Cause Investigation
    task_rootcause = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"{data_availability}\n\n"
            f"Here is the occupancy analysis:\n\n"
            f"{occupancy}\n\n"
            "You have access to findings from the pricing analyst and "
            "sentiment analyst (passed as context). Synthesize all findings to:\n"
            "1. Identify the primary root cause [HYPOTHESIS with supporting data]\n"
            "2. Drill through at least 3 dimensions [FROM DATA]\n"
            "3. Validate that the root cause is not a data artifact\n"
            "4. Quantify impact ONLY using available data. "
            "   Use occupancy rates and listing counts (available). "
            "   Do NOT fabricate dollar amounts if price data is null.\n\n"
            "FORMAT YOUR FINDINGS AS:\n"
            "- DATA-BACKED FINDINGS: [things calculated from the dataset]\n"
            "- HYPOTHESES: [your interpretations that need further validation]\n"
            "- CANNOT DETERMINE: [things the data doesn't support]"
        ),
        expected_output=(
            "A root cause analysis with clearly separated sections for "
            "data-backed findings, hypotheses, and acknowledged data gaps. "
            "No fabricated dollar figures."
        ),
        agent=agents["root_cause_investigator"],
        context=[task_pricing, task_sentiment],
    )

    # Task 5: Validation (NEW in V2)
    task_validation = Task(
        description=(
            f"{data_availability}\n\n"
            "You are the fact-checker. Review ALL findings from previous agents.\n\n"
            "For EVERY quantitative claim in the previous agents' outputs, determine:\n"
            "- HIGH CONFIDENCE: Number was directly calculated from the dataset\n"
            "  (e.g., '45,585 listings' = row count, '48.7% occupancy' = calendar calculation)\n"
            "- LOW CONFIDENCE: Number was estimated or extrapolated by an agent\n"
            "  (e.g., any dollar figure when price data is null)\n"
            "- HALLUCINATED: Number has no basis in the data at all\n"
            "  (e.g., specific revenue figures when no revenue data exists)\n\n"
            "Produce a validation report with:\n"
            "1. A table of claims with confidence ratings\n"
            "2. List of hallucinated numbers that must be removed\n"
            "3. Corrected versions of any unsupported claims\n"
            "4. An overall confidence score for the analysis (A-F grade)\n\n"
            "Be ruthless. Better to flag a real number as questionable than "
            "to let a fabricated number through."
        ),
        expected_output=(
            "A validation report grading every quantitative claim as "
            "HIGH CONFIDENCE, LOW CONFIDENCE, or HALLUCINATED, with "
            "an overall analysis confidence score."
        ),
        agent=agents["validation_agent"],
        context=[task_rootcause, task_pricing, task_sentiment],
    )

    # Task 6: Executive Report (now uses validation)
    task_report = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"{data_availability}\n\n"
            "You have the validation report that grades every claim. "
            "Write the final executive report following these rules:\n\n"
            "1. ONLY use HIGH CONFIDENCE numbers as facts\n"
            "2. Present LOW CONFIDENCE numbers with 'estimated' or 'approximately'\n"
            "3. REMOVE any HALLUCINATED numbers entirely\n"
            "4. Where revenue cannot be quantified, say: 'Revenue impact requires "
            "   pricing data not available in this dataset.'\n\n"
            "Structure:\n"
            "- Context: Current state of LA Airbnb market [use only verified numbers]\n"
            "- Tension: The problem and its impact [use occupancy data, not fabricated revenue]\n"
            "- Resolution: 3 recommendations [actionable without fake ROI numbers]\n"
            "- Data Gaps: What data is needed to size the opportunity\n"
            "- Confidence Disclaimer: Overall analysis reliability\n\n"
            "Keep it under 500 words. Honesty over impressiveness."
        ),
        expected_output=(
            "An executive summary under 500 words with clearly labeled "
            "confidence levels, no hallucinated numbers, and transparent "
            "acknowledgment of data limitations."
        ),
        agent=agents["report_writer"],
        context=[task_validation],
        output_file="outputs/executive_report_v2.md",
    )

    return [
        task_profile,
        task_pricing,
        task_sentiment,
        task_rootcause,
        task_validation,
        task_report,
    ]
