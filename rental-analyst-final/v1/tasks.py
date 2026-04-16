"""
Task definitions for the rental-analyst crew.
Each task maps to an agent and defines what it should produce.
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

    print("[Data tools complete. Starting agents...]\n")

    # Task 1: Data Profiling
    task_profile = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"Here are the data profiles for all three tables:\n\n"
            f"{listings_profile}\n\n"
            f"{reviews_profile}\n\n"
            f"{calendar_profile}\n\n"
            "Based on these profiles, provide:\n"
            "1. A summary of data quality issues\n"
            "2. Key distributions and patterns you notice\n"
            "3. Any data quirks that could affect the analysis\n"
            "4. Your recommendation for which dimensions to investigate"
        ),
        expected_output=(
            "A structured data quality report covering all three tables, "
            "with specific findings on nulls, outliers, and data quirks, "
            "plus a recommendation for analysis priorities."
        ),
        agent=agents["data_profiler"],
    )

    # Task 2: Pricing Analysis
    task_pricing = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"Here is the neighborhood pricing analysis:\n\n"
            f"{hood_pricing}\n\n"
            f"Here is the pricing gap analysis:\n\n"
            f"{price_gaps}\n\n"
            "Based on this data, provide:\n"
            "1. Which neighborhoods have the biggest pricing problems\n"
            "2. How many listings are significantly mispriced\n"
            "3. The estimated revenue impact of pricing corrections\n"
            "4. Specific pricing recommendations by neighborhood"
        ),
        expected_output=(
            "A pricing analysis report with specific neighborhoods flagged, "
            "counts of mispriced listings, and quantified revenue opportunity."
        ),
        agent=agents["pricing_analyst"],
        context=[task_profile],
    )

    # Task 3: Sentiment Analysis
    task_sentiment = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"Here is the sentiment analysis of guest reviews:\n\n"
            f"{sentiment}\n\n"
            f"Total reviews in dataset: {len(reviews):,}\n\n"
            "Based on this data, provide:\n"
            "1. Overall sentiment health of the marketplace\n"
            "2. What the negative reviews are complaining about\n"
            "3. Whether sentiment correlates with any pricing or neighborhood patterns\n"
            "4. Recommendations for improving guest satisfaction"
        ),
        expected_output=(
            "A sentiment analysis report with overall scores, key complaint themes, "
            "and actionable recommendations for hosts."
        ),
        agent=agents["sentiment_analyst"],
        context=[task_profile],
    )

    # Task 4: Root Cause Investigation
    task_rootcause = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            f"Here is the occupancy analysis:\n\n"
            f"{occupancy}\n\n"
            "You have access to findings from the pricing analyst and "
            "sentiment analyst (passed as context). Synthesize all findings to:\n"
            "1. Identify the primary root cause of the problem\n"
            "2. Drill through at least 3 dimensions (neighborhood, property type, price tier)\n"
            "3. Validate that the root cause is not a data artifact\n"
            "4. Quantify the impact of the root cause"
        ),
        expected_output=(
            "A root cause analysis that identifies the specific, actionable "
            "driver of the problem, validated across multiple dimensions, "
            "with quantified impact."
        ),
        agent=agents["root_cause_investigator"],
        context=[task_pricing, task_sentiment],
    )

    # Task 5: Executive Report
    task_report = Task(
        description=(
            f"The user asked: '{question}'\n\n"
            "You have access to all previous findings (data profile, pricing "
            "analysis, sentiment analysis, and root cause investigation). "
            "Write the final executive report:\n"
            "1. Context: What is the current state of the LA Airbnb market\n"
            "2. Tension: What is the specific problem and its dollar impact\n"
            "3. Resolution: 3 specific, prioritized recommendations with expected ROI\n"
            "4. Next steps: What additional data or analysis would strengthen these findings\n\n"
            "Keep it under 500 words. Every sentence must either inform or recommend."
        ),
        expected_output=(
            "An executive summary under 500 words following the "
            "Context-Tension-Resolution framework, with 3 quantified "
            "recommendations and clear next steps."
        ),
        agent=agents["report_writer"],
        context=[task_rootcause],
        output_file="outputs/executive_report.md",
    )

    return [task_profile, task_pricing, task_sentiment, task_rootcause, task_report]
