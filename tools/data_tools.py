"""
Tools for Airbnb data analysis.
These are the functions that agents call to interact with the data.

V2: Added confidence tags to all outputs so agents know what's reliable.
"""

import pandas as pd
import os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_listings() -> pd.DataFrame:
    """Load and clean the listings dataset."""
    path = os.path.join(DATA_DIR, "listings.csv")
    df = pd.read_csv(path, low_memory=False)

    # Clean price column (remove $ and commas, handle multiple formats)
    if "price" in df.columns:
        df["price"] = (
            df["price"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        valid = df["price"].notna().sum()
        total = len(df)
        print(
            f"  Price column: {valid} valid ({round(100*valid/total,1)}%), "
            f"{total - valid} null, median=${df['price'].median()}"
        )

    return df


def load_reviews() -> pd.DataFrame:
    """Load the reviews dataset."""
    path = os.path.join(DATA_DIR, "reviews.csv")
    df = pd.read_csv(path, low_memory=False)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_calendar() -> pd.DataFrame:
    """Load and clean the calendar dataset (sampled to save memory)."""
    path = os.path.join(DATA_DIR, "calendar.csv")
    df = pd.read_csv(
        path,
        low_memory=False,
        usecols=["listing_id", "date", "available", "price"],
        nrows=2_000_000,
    )

    if "price" in df.columns:
        df["price"] = (
            df["price"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def profile_dataset(df: pd.DataFrame, name: str) -> str:
    """Generate a text profile of a dataframe with confidence tags."""
    lines = []
    lines.append(f"=== {name} [ALL NUMBERS FROM DATA] ===")
    lines.append(f"Rows: {len(df):,} [FROM DATA]")
    lines.append(f"Columns: {len(df.columns)} [FROM DATA]")
    lines.append("")

    lines.append("Column types:")
    for col in df.columns:
        dtype = df[col].dtype
        nulls = df[col].isnull().sum()
        null_pct = round(100 * nulls / len(df), 1) if len(df) > 0 else 0
        usability = "USABLE" if null_pct < 50 else "NOT USABLE (>50% null)"
        lines.append(
            f"  {col}: {dtype} (nulls: {nulls}, {null_pct}%) -- {usability}"
        )

    lines.append("")

    # Numeric summary
    numeric_cols = df.select_dtypes(include=["number"]).columns[:10]
    if len(numeric_cols) > 0:
        lines.append("Numeric summary (first 10) [FROM DATA]:")
        for col in numeric_cols:
            if df[col].notna().sum() > 0:
                lines.append(
                    f"  {col}: min={df[col].min()}, "
                    f"median={df[col].median()}, "
                    f"max={df[col].max()}, "
                    f"mean={df[col].mean():.2f}"
                )
            else:
                lines.append(f"  {col}: ALL NULL -- cannot calculate any metrics from this column")

    return "\n".join(lines)


def neighborhood_pricing(df: pd.DataFrame, top_n: int = 20) -> str:
    """Analyze pricing by neighborhood with confidence tags."""
    hood_col = None
    for candidate in [
        "neighbourhood_cleansed",
        "neighbourhood",
        "neighborhood",
        "neighborhood_cleansed",
    ]:
        if candidate in df.columns:
            hood_col = candidate
            break

    if hood_col is None:
        hood_col = next(
            (c for c in df.columns if "neighbour" in c.lower() or "neighborhood" in c.lower()),
            None,
        )

    if hood_col is None:
        return f"No neighborhood column found. Available columns: {', '.join(df.columns[:20])}"

    valid = df.dropna(subset=["price"])
    valid = valid[valid["price"] > 0]

    if len(valid) == 0:
        return "No valid price data found. [CANNOT CALCULATE neighborhood pricing]"

    coverage = round(100 * len(valid) / len(df), 1)

    stats = (
        valid.groupby(hood_col)["price"]
        .agg(["count", "median", "mean", "std"])
        .sort_values("count", ascending=False)
        .head(top_n)
    )
    stats = stats.round(2)

    lines = [
        f"Top {top_n} neighborhoods by listing count [FROM DATA]:",
        f"(Based on {len(valid):,} listings with valid prices, {coverage}% of total)\n",
    ]
    for hood, row in stats.iterrows():
        lines.append(
            f"  {hood}: {int(row['count'])} listings, "
            f"median ${row['median']:.0f}, "
            f"mean ${row['mean']:.0f}"
        )
    return "\n".join(lines)


def occupancy_analysis(calendar_df: pd.DataFrame) -> str:
    """Calculate occupancy rates from calendar data with confidence tags."""
    if "available" not in calendar_df.columns:
        return "No 'available' column found in calendar data."

    total = len(calendar_df)
    if total == 0:
        return "Calendar data is empty."

    booked = (calendar_df["available"] == "f").sum()
    available = (calendar_df["available"] == "t").sum()
    occ_rate = round(100 * booked / total, 1)

    lines = [
        "Overall occupancy analysis [FROM DATA]:",
        f"  Total calendar entries: {total:,}",
        f"  Booked (unavailable): {booked:,}",
        f"  Available: {available:,}",
        f"  Occupancy rate: {occ_rate}%",
        f"  NOTE: Based on {total:,} sampled rows, not full calendar file.",
    ]

    if "date" in calendar_df.columns and calendar_df["date"].notna().sum() > 0:
        cal = calendar_df.copy()
        cal["month"] = cal["date"].dt.to_period("M")
        monthly = cal.groupby("month")["available"].apply(
            lambda x: round(100 * (x == "f").sum() / len(x), 1) if len(x) > 0 else 0
        )
        lines.append("\nMonthly occupancy rates [FROM DATA]:")
        for month, rate in monthly.items():
            lines.append(f"  {month}: {rate}%")

    # Check if price data is available for revenue calculations
    if "price" in calendar_df.columns:
        price_nulls = calendar_df["price"].isna().sum()
        price_pct = round(100 * price_nulls / total, 1)
        if price_pct > 50:
            lines.append(
                f"\n  WARNING: Calendar price column is {price_pct}% null. "
                f"Revenue and dollar-based calculations are NOT possible. "
                f"[DO NOT ESTIMATE revenue figures]"
            )
        else:
            avg_price = calendar_df["price"].mean()
            lines.append(f"\n  Average daily rate: ${avg_price:.2f} [FROM DATA]")

    return "\n".join(lines)


def pricing_gaps(df: pd.DataFrame) -> str:
    """Find listings significantly above or below market rate with confidence tags."""
    hood_col = None
    for candidate in [
        "neighbourhood_cleansed",
        "neighbourhood",
        "neighborhood",
        "neighborhood_cleansed",
    ]:
        if candidate in df.columns:
            hood_col = candidate
            break

    if hood_col is None:
        hood_col = next(
            (c for c in df.columns if "neighbour" in c.lower() or "neighborhood" in c.lower()),
            None,
        )

    if hood_col is None:
        return f"No neighborhood column found. Available columns: {', '.join(df.columns[:20])}"

    if "room_type" not in df.columns:
        return f"No 'room_type' column found. Available columns: {', '.join(df.columns[:20])}"

    df = df.copy()
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]

    if len(df) == 0:
        return "No valid price data after filtering nulls and zeros. [CANNOT CALCULATE pricing gaps]"

    group_cols = [hood_col, "room_type"]
    medians = df.groupby(group_cols)["price"].median().reset_index()
    medians.columns = list(group_cols) + ["median_price"]

    merged = df.merge(medians, on=group_cols, how="left")
    merged = merged[merged["median_price"] > 0]

    if len(merged) == 0:
        return "No valid data after merging with median prices. [CANNOT CALCULATE pricing gaps]"

    merged["price_gap_pct"] = round(
        100 * (merged["price"] - merged["median_price"]) / merged["median_price"], 1
    )

    overpriced = merged[merged["price_gap_pct"] > 30]
    underpriced = merged[merged["price_gap_pct"] < -30]

    lines = [
        "Pricing gap analysis (vs neighborhood + room type median) [FROM DATA]:",
        f"  Total listings analyzed: {len(merged):,}",
        f"  Overpriced (>30% above median): {len(overpriced):,} ({round(100 * len(overpriced) / len(merged), 1)}%)",
        f"  Underpriced (>30% below median): {len(underpriced):,} ({round(100 * len(underpriced) / len(merged), 1)}%)",
        "",
        "  NOTE: These are listing asking prices, not actual booking revenue.",
        "  Revenue impact CANNOT be calculated without daily rate + booking data.",
        "",
        "Top overpriced neighborhoods [FROM DATA]:",
    ]

    over_by_hood = (
        overpriced.groupby(hood_col).size().sort_values(ascending=False).head(5)
    )
    for hood, count in over_by_hood.items():
        lines.append(f"  {hood}: {count} overpriced listings")

    lines.append("\nTop underpriced neighborhoods [FROM DATA]:")
    under_by_hood = (
        underpriced.groupby(hood_col).size().sort_values(ascending=False).head(5)
    )
    for hood, count in under_by_hood.items():
        lines.append(f"  {hood}: {count} underpriced listings")

    return "\n".join(lines)


def sentiment_sample(reviews_df: pd.DataFrame, sample_size: int = 500) -> str:
    """Run basic sentiment analysis on a sample of reviews with confidence tags."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        return "vaderSentiment not installed. Run: pip install vaderSentiment"

    if "comments" not in reviews_df.columns:
        return f"No 'comments' column found in reviews. Available columns: {', '.join(reviews_df.columns)}"

    reviews_with_comments = reviews_df.dropna(subset=["comments"])
    if len(reviews_with_comments) == 0:
        return "No reviews with comments found."

    sample = reviews_with_comments.sample(
        min(sample_size, len(reviews_with_comments)), random_state=42
    )

    analyzer = SentimentIntensityAnalyzer()
    scores = sample["comments"].apply(
        lambda x: analyzer.polarity_scores(str(x))["compound"]
    )

    neg_count = (scores < -0.05).sum()
    neu_count = ((scores >= -0.05) & (scores <= 0.05)).sum()
    pos_count = (scores > 0.05).sum()

    lines = [
        f"Sentiment analysis [FROM DATA but LIMITED SAMPLE]:",
        f"  Sample size: {len(sample)} reviews out of {len(reviews_df):,} total",
        f"  Coverage: {round(100 * len(sample) / len(reviews_df), 3)}% of all reviews",
        f"  CONFIDENCE NOTE: These results are INDICATIVE, not conclusive.",
        f"",
        f"  Mean sentiment: {scores.mean():.3f} (scale: -1 negative to +1 positive)",
        f"  Median sentiment: {scores.median():.3f}",
        f"  Negative reviews (score < -0.05): {neg_count} ({round(100 * neg_count / len(scores), 1)}%)",
        f"  Neutral reviews: {neu_count}",
        f"  Positive reviews (score > 0.05): {pos_count} ({round(100 * pos_count / len(scores), 1)}%)",
    ]

    # Most negative reviews
    sample = sample.copy()
    sample["sentiment"] = scores.values
    worst = sample.nsmallest(3, "sentiment")
    lines.append("\nMost negative reviews from sample:")
    for _, row in worst.iterrows():
        comment = str(row["comments"])[:150]
        lines.append(f"  [{row['sentiment']:.2f}] {comment}...")

    return "\n".join(lines)
