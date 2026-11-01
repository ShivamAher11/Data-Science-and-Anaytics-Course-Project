"""Create analysis features from the cleaned Airbnb listing-level master table.

Run from any working directory:
    python scripts/feature_engineering.py

The source file is read-only. The feature table is written to data/processed/.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_DIR / "data" / "processed" / "airbnb_master.csv"
OUTPUT_PATH = PROJECT_DIR / "data" / "processed" / "airbnb_features.csv"
MIN_BENCHMARK_GROUP_SIZE = 20
RAW_LISTINGS_CANDIDATES = [
    PROJECT_DIR / "data" / "raw" / "listings.csv",
    PROJECT_DIR.parent / "listings.csv" / "listings.csv",
    PROJECT_DIR.parent / "main" / "listings.csv",
]


def enrich_from_raw_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Join privacy-minimized, pre-review features from the raw listing export."""
    raw_path = next((path for path in RAW_LISTINGS_CANDIDATES if path.exists()), None)
    if raw_path is None:
        print("Raw listings.csv not found; raw-listing enrichment skipped.")
        return df

    usecols = [
        "id", "amenities", "description", "bathrooms_text", "last_scraped",
        "host_since", "license", "host_response_rate", "host_acceptance_rate",
        "host_response_time", "instant_bookable", "neighborhood_overview", "picture_url",
    ]
    header = pd.read_csv(raw_path, nrows=0, low_memory=False).columns
    usecols = [column for column in usecols if column in header]
    raw = pd.read_csv(raw_path, usecols=usecols, low_memory=False)
    if "id" not in raw.columns:
        raise ValueError(f"Raw listings file has no id column: {raw_path}")
    raw = raw.drop_duplicates("id", keep="last")
    available_raw_fields = [column for column in raw.columns if column != "id"]
    enriched = df.merge(raw[["id", *available_raw_fields]], on="id", how="left", validate="one_to_one")

    def parse_amenities(value: object) -> list[str]:
        if not isinstance(value, str):
            return []
        try:
            parsed = json.loads(value)
            return [str(item).strip().lower() for item in parsed] if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    amenity_lists = enriched["amenities"].map(parse_amenities) if "amenities" in enriched else pd.Series([[]] * len(enriched), index=enriched.index)
    enriched["amenity_count"] = amenity_lists.map(len)
    amenity_flags = {
        "amenity_wifi": ("wifi", "wireless internet"),
        "amenity_kitchen": ("kitchen",),
        "amenity_washer": ("washer", "washing machine"),
        "amenity_air_conditioning": ("air conditioning", "air conditioner"),
        "amenity_workspace": ("dedicated workspace", "workspace"),
        "amenity_parking": ("parking",),
        "amenity_pool": ("pool",),
        "amenity_self_check_in": ("self check-in", "self check in"),
    }
    for feature, terms in amenity_flags.items():
        enriched[feature] = amenity_lists.map(
            lambda items, terms=terms: int(any(term in item for item in items for term in terms))
        )

    if "description" in enriched:
        description = enriched["description"].fillna("").astype(str).str.replace(r"<[^>]+>", " ", regex=True)
        enriched["description_length_chars"] = description.str.len()
        enriched["description_word_count"] = description.str.findall(r"\b\w+\b").str.len()
        enriched.drop(columns=["description"], inplace=True)
    if "bathrooms_text" in enriched:
        bath = enriched["bathrooms_text"].fillna("").astype(str).str.lower()
        enriched["bathroom_privacy"] = np.select(
            [bath.str.contains("shared", regex=False), bath.str.contains("private", regex=False)],
            ["shared", "private"], default="unspecified"
        )
        enriched.drop(columns=["bathrooms_text"], inplace=True)
    # These source fields were audited but are missing in all rows; omit them.
    all_missing = [c for c in ["host_since", "license", "host_response_rate", "host_acceptance_rate", "host_response_time", "instant_bookable", "neighborhood_overview"] if c in enriched and enriched[c].isna().all()]
    if all_missing:
        enriched.drop(columns=all_missing, inplace=True)
    # Do not retain photo URLs or raw review-adjacent text in the model table.
    if "picture_url" in enriched:
        enriched.drop(columns=["picture_url"], inplace=True)
    if "amenities" in enriched:
        enriched.drop(columns=["amenities"], inplace=True)
    if "last_scraped" in enriched:
        enriched.drop(columns=["last_scraped"], inplace=True)
    print(f"Raw listing enrichment joined from {raw_path}; retained aggregate feature columns only.")
    return enriched


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(
            f"Input is missing required columns: {missing}. "
            "Run the cleaning pipeline first."
        )


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}. Run the cleaning pipeline first."
        )

    df = pd.read_csv(INPUT_PATH, low_memory=False)
    df = enrich_from_raw_listings(df)
    require_columns(
        df,
        [
            "id", "host_id", "neighbourhood_cleansed", "room_type", "price",
            "accommodates", "pct_days_booked", "last_review", "reviews_per_month",
        ],
    )

    # 1. Compare each listing with the local market for its room type.
    market_keys = ["neighbourhood_cleansed", "room_type"]
    grouped_price = df.groupby(market_keys, dropna=False)["price"]
    df["local_room_type_price_median_gbp"] = grouped_price.transform("median")
    df["local_room_type_listing_count"] = grouped_price.transform("count")
    too_small = df["local_room_type_listing_count"] < MIN_BENCHMARK_GROUP_SIZE
    df.loc[too_small, "local_room_type_price_median_gbp"] = np.nan
    df["price_vs_local_median_pct"] = (
        (df["price"] / df["local_room_type_price_median_gbp"] - 1) * 100
    )
    df["price_position_vs_local_market"] = pd.cut(
        df["price_vs_local_median_pct"],
        bins=[-np.inf, -10, 10, np.inf],
        labels=["below_local_median", "near_local_median", "above_local_median"],
        right=False,
    ).astype("string")
    df.loc[too_small, "price_position_vs_local_market"] = "insufficient_local_sample"

    # 2. Describe host portfolio size (not host identity).
    host_counts = df.groupby("host_id")["id"].transform("count")
    df["host_listing_count"] = host_counts
    df["host_portfolio_segment"] = pd.cut(
        host_counts,
        bins=[0, 1, 5, 20, np.inf],
        labels=["1_listing", "2_to_5_listings", "6_to_20_listings", "21_plus_listings"],
    ).astype("string")

    # 3. Normalize listed nightly price by the listing's stated guest capacity.
    capacity = pd.to_numeric(df["accommodates"], errors="coerce")
    price = pd.to_numeric(df["price"], errors="coerce")
    df["listed_price_per_guest_gbp"] = price.div(capacity.where(capacity > 0))

    # 4. Preserve the availability measure as a proxy, not confirmed bookings.
    unavailability = pd.to_numeric(df["pct_days_booked"], errors="coerce")
    df["calendar_unavailability_rate_proxy"] = unavailability.clip(0, 1)
    df["calendar_unavailability_band_proxy"] = pd.cut(
        df["calendar_unavailability_rate_proxy"],
        bins=[-np.inf, 0.25, 0.50, np.inf],
        labels=["lower_unavailability", "mid_unavailability", "higher_unavailability"],
        right=False,
    ).astype("string")

    # 5. Measure review recency relative to the latest review in this snapshot.
    # This avoids assuming that the download date equals the current date.
    review_date = pd.to_datetime(df["last_review"], errors="coerce")
    latest_observed_review = review_date.max()
    df["days_since_latest_observed_review"] = (
        latest_observed_review - review_date
    ).dt.days.astype("Float64")
    df["review_activity_band"] = pd.cut(
        pd.to_numeric(df["reviews_per_month"], errors="coerce"),
        bins=[-np.inf, 0.25, 1.0, np.inf],
        labels=["low_activity", "moderate_activity", "high_activity"],
        right=False,
    ).astype("string")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Source rows: {len(df):,}")
    print(f"Saved feature table: {OUTPUT_PATH}")
    print(f"Price benchmark groups under {MIN_BENCHMARK_GROUP_SIZE} listings: "
          f"{int(too_small.sum()):,} rows use the insufficient-sample label")
    print(f"Listings with calendar unavailability proxy: "
          f"{df['calendar_unavailability_rate_proxy'].notna().sum():,}")
    print(f"Listings with observed last-review date: {review_date.notna().sum():,}")


if __name__ == "__main__":
    main()
