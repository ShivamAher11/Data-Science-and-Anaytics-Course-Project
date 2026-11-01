"""
============================================================
DECODING THE STAY ECONOMY
Full Cleaning & Schema Alignment Pipeline
Airbnb London (listings.csv + calendar.csv + reviews.csv)
    vs
Booking.com London (Hotel_Reviews.csv, filtered to London addresses)
============================================================

HOW TO USE:
1. Put these 4 files in the SAME FOLDER as this script:
     - listings.csv
     - calendar.csv
     - reviews.csv
     - Hotel_Reviews.csv
   (If they're elsewhere, change RAW_DIR below.)

2. Install dependencies once in your VS Code terminal:
     pip install pandas numpy

3. Run:
     python clean_and_align_full.py

OUTPUTS (created in an "output" subfolder):
    airbnb_listings_clean.csv     - cleaned listings, one row per listing
    airbnb_calendar_clean.csv     - cleaned calendar, one row per listing-date
    airbnb_calendar_agg.csv       - calendar aggregated to one row per listing (demand signal)
    airbnb_reviews_clean.csv      - cleaned reviews, one row per review
    airbnb_reviews_agg.csv        - reviews aggregated to one row per listing (sentiment signal)
    airbnb_master.csv             - listings + calendar_agg + reviews_agg joined, one row per listing
    booking_london_clean.csv      - cleaned Booking.com reviews, London only
    comparison_schema.csv         - Airbnb master + Booking.com mapped to ONE shared schema
    cleaning_report.txt           - full log of every step, counts, and what was dropped

NOTE ON GRAIN: listings.csv, calendar.csv, and reviews.csv are at DIFFERENT
grains (one row per listing / one row per listing-date / one row per review).
We clean each separately, then AGGREGATE calendar and reviews UP to
listing-level before joining everything into one Airbnb "master" table.
That master table is then stacked (not merged) against Booking.com to
build the final comparison_schema.csv used for EDA/stats/dashboard.
============================================================
"""

import pandas as pd
import numpy as np
import os
import re

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
RAW_DIR = "."
OUT_DIR = "./output"
os.makedirs(OUT_DIR, exist_ok=True)

report_lines = []

def log(msg):
    print(msg)
    report_lines.append(str(msg))


# ============================================================
# STEP 1 — CLEAN listings.csv
# ============================================================
log("=" * 60)
log("STEP 1: AIRBNB listings.csv")
log("=" * 60)

listings = pd.read_csv(f"{RAW_DIR}/listings.csv", low_memory=False)
log(f"1.1  Raw shape: {listings.shape}")

keep_cols = [
    "id", "host_id", "host_is_superhost", "host_response_time",
    "host_response_rate", "host_acceptance_rate",
    "neighbourhood_cleansed", "latitude", "longitude",
    "property_type", "room_type", "accommodates", "bathrooms",
    "bedrooms", "beds", "price",
    "minimum_nights", "maximum_nights",
    "availability_30", "availability_60", "availability_90", "availability_365",
    "number_of_reviews", "number_of_reviews_ltm",
    "first_review", "last_review",
    "review_scores_rating", "review_scores_accuracy", "review_scores_cleanliness",
    "review_scores_checkin", "review_scores_communication",
    "review_scores_location", "review_scores_value",
    "instant_bookable", "reviews_per_month",
    "estimated_occupancy_l365d", "estimated_revenue_l365d",
]
listings = listings[[c for c in keep_cols if c in listings.columns]].copy()
log(f"1.2  After column selection: {listings.shape}")

# Clean price: "$234.50" -> 234.50
listings["price"] = listings["price"].astype(str).str.replace(r"[\$,]", "", regex=True)
listings["price"] = pd.to_numeric(listings["price"], errors="coerce")
log(f"1.3  Price cleaned. Missing: {listings['price'].isna().mean()*100:.1f}%")

listings = listings.dropna(subset=["price"])
log(f"1.4  Dropped rows with missing price. Shape: {listings.shape}")

low, high = listings["price"].quantile([0.005, 0.995])
before = len(listings)
listings = listings[(listings["price"] >= low) & (listings["price"] <= high)]
log(f"1.5  Removed {before - len(listings)} extreme price outliers "
    f"(kept £{low:.0f}-£{high:.0f}/night). Shape: {listings.shape}")

before = len(listings)
listings = listings.drop_duplicates(subset=["id"])
log(f"1.6  Removed {before - len(listings)} duplicate listing IDs")

for col in ["host_response_rate", "host_acceptance_rate"]:
    if col in listings.columns:
        listings[col] = listings[col].astype(str).str.replace("%", "", regex=False)
        listings[col] = pd.to_numeric(listings[col], errors="coerce")
log("1.7  Cleaned % fields (host_response_rate, host_acceptance_rate)")

for col in ["first_review", "last_review"]:
    listings[col] = pd.to_datetime(listings[col], errors="coerce")
log("1.8  Parsed date columns")

# CHECK YOUR SCALE: this was 0-5 in the sample checked earlier.
# If your file shows values up to 100 instead of 5, change the *2 in Step 5 to /10.
log(f"1.9  review_scores_rating range: {listings['review_scores_rating'].min()} "
    f"to {listings['review_scores_rating'].max()} — verify scale (0-5 or 0-100)")

listings["has_reviews"] = listings["number_of_reviews"] > 0
log(f"1.10 Zero-review listings: {(~listings['has_reviews']).mean()*100:.1f}% (flagged, not dropped)")

listings.to_csv(f"{OUT_DIR}/airbnb_listings_clean.csv", index=False)
log(f"1.11 SAVED airbnb_listings_clean.csv — {listings.shape}\n")


# ============================================================
# STEP 2 — CLEAN calendar.csv (demand / availability signal)
# ============================================================
log("=" * 60)
log("STEP 2: AIRBNB calendar.csv")
log("=" * 60)

# calendar.csv is usually large (365 rows per listing) — read efficiently
calendar = pd.read_csv(
    f"{RAW_DIR}/calendar.csv",
    parse_dates=["date"],
    dtype={"listing_id": "int64"},
    low_memory=False,
)
log(f"2.1  Raw shape: {calendar.shape}")

# Standard Inside Airbnb columns: listing_id, date, available (t/f), price,
# adjusted_price, minimum_nights, maximum_nights
log(f"2.2  Columns found: {calendar.columns.tolist()}")

# Clean price field the same way as listings
if "price" in calendar.columns:
    calendar["price"] = calendar["price"].astype(str).str.replace(r"[\$,]", "", regex=True)
    calendar["price"] = pd.to_numeric(calendar["price"], errors="coerce")
if "adjusted_price" in calendar.columns:
    calendar["adjusted_price"] = calendar["adjusted_price"].astype(str).str.replace(r"[\$,]", "", regex=True)
    calendar["adjusted_price"] = pd.to_numeric(calendar["adjusted_price"], errors="coerce")
log("2.3  Cleaned price / adjusted_price columns")

# Convert available "t"/"f" to boolean
if "available" in calendar.columns:
    calendar["is_available"] = calendar["available"].map({"t": True, "f": False})
    log("2.4  Converted 'available' t/f to boolean is_available")

# Drop rows with no date (shouldn't happen, but check)
before = len(calendar)
calendar = calendar.dropna(subset=["date"])
log(f"2.5  Dropped {before - len(calendar)} rows with invalid dates")

calendar.to_csv(f"{OUT_DIR}/airbnb_calendar_clean.csv", index=False)
log(f"2.6  SAVED airbnb_calendar_clean.csv — {calendar.shape}")

# --- 2.7 Aggregate calendar UP to one row per listing (this is your demand signal) ---
calendar_agg = calendar.groupby("listing_id").agg(
    avg_daily_price=("price", "mean"),
    price_volatility=("price", "std"),          # higher = more dynamic pricing over the year
    pct_days_booked=("is_available", lambda x: 1 - x.mean()),  # inverse of availability = booked ratio
    days_with_data=("date", "count"),
).reset_index()

calendar_agg.to_csv(f"{OUT_DIR}/airbnb_calendar_agg.csv", index=False)
log(f"2.7  SAVED airbnb_calendar_agg.csv (demand signal per listing) — {calendar_agg.shape}\n")


# ============================================================
# STEP 3 — CLEAN reviews.csv (guest-trust / sentiment signal)
# ============================================================
log("=" * 60)
log("STEP 3: AIRBNB reviews.csv")
log("=" * 60)

reviews = pd.read_csv(f"{RAW_DIR}/reviews.csv", low_memory=False)
log(f"3.1  Raw shape: {reviews.shape}")
log(f"3.2  Columns found: {reviews.columns.tolist()}")
# Standard columns: listing_id, id, date, reviewer_id, reviewer_name, comments

reviews["date"] = pd.to_datetime(reviews["date"], errors="coerce")
log("3.3  Parsed review date")

# Drop rows with no comment text or no listing_id
before = len(reviews)
reviews = reviews.dropna(subset=["comments", "listing_id"])
log(f"3.4  Dropped {before - len(reviews)} rows with missing comment text or listing_id")

# Basic text cleaning
reviews["comments"] = reviews["comments"].astype(str).str.strip()
reviews["comments"] = reviews["comments"].str.replace(r"<br\s*/?>", " ", regex=True)  # remove HTML line breaks
reviews["comment_word_count"] = reviews["comments"].str.split().str.len()
log("3.5  Cleaned comment text (stripped HTML breaks, computed word count)")

# --- 3.6 Lightweight sentiment proxy (no extra installs required) ---
# A simple keyword-based polarity score. This is a PROXY, not full NLP —
# state this clearly as a limitation in your report. For a stronger method,
# install textblob (pip install textblob) and use TextBlob(text).sentiment.polarity instead.
positive_words = {"great", "clean", "amazing", "excellent", "lovely", "perfect",
                   "wonderful", "comfortable", "friendly", "recommend", "beautiful",
                   "convenient", "spacious", "helpful", "fantastic", "good", "nice"}
negative_words = {"dirty", "bad", "terrible", "poor", "noisy", "awful",
                   "uncomfortable", "rude", "small", "disappointing", "issue",
                   "problem", "broken", "cancel", "worst", "horrible"}

def simple_sentiment(text):
    words = re.findall(r"\b\w+\b", text.lower())
    pos = sum(1 for w in words if w in positive_words)
    neg = sum(1 for w in words if w in negative_words)
    return pos - neg

reviews["sentiment_score"] = reviews["comments"].apply(simple_sentiment)
log("3.6  Built sentiment_score proxy (keyword-based; upgrade to TextBlob for real NLP if desired)")

reviews.to_csv(f"{OUT_DIR}/airbnb_reviews_clean.csv", index=False)
log(f"3.7  SAVED airbnb_reviews_clean.csv — {reviews.shape}")

# --- 3.8 Aggregate reviews UP to one row per listing ---
reviews_agg = reviews.groupby("listing_id").agg(
    review_text_count=("id", "count"),
    avg_sentiment_score=("sentiment_score", "mean"),
    avg_comment_length=("comment_word_count", "mean"),
    most_recent_review_date=("date", "max"),
).reset_index()

reviews_agg.to_csv(f"{OUT_DIR}/airbnb_reviews_agg.csv", index=False)
log(f"3.8  SAVED airbnb_reviews_agg.csv (sentiment signal per listing) — {reviews_agg.shape}\n")


# ============================================================
# STEP 4 — JOIN listings + calendar_agg + reviews_agg -> Airbnb MASTER table
# ============================================================
log("=" * 60)
log("STEP 4: BUILD AIRBNB MASTER TABLE")
log("=" * 60)

airbnb_master = listings.merge(
    calendar_agg, left_on="id", right_on="listing_id", how="left"
).merge(
    reviews_agg, on="listing_id", how="left"
)
log(f"4.1  Joined listings + calendar_agg + reviews_agg. Shape: {airbnb_master.shape}")

airbnb_master.to_csv(f"{OUT_DIR}/airbnb_master.csv", index=False)
log(f"4.2  SAVED airbnb_master.csv — {airbnb_master.shape}\n")


# ============================================================
# STEP 5 — CLEAN Hotel_Reviews.csv (Booking.com), filter to London
# ============================================================
log("=" * 60)
log("STEP 5: BOOKING.COM Hotel_Reviews.csv — filter to London")
log("=" * 60)

booking = pd.read_csv(f"{RAW_DIR}/Hotel_Reviews.csv")
log(f"5.1  Raw shape (all 6 European cities): {booking.shape}")

booking_london = booking[
    booking["Hotel_Address"].str.contains(r"\bLondon\b", case=False, na=False, regex=True)
].copy()
log(f"5.2  London rows after explicit address filter: {booking_london.shape}")

booking_london["Positive_Review"] = booking_london["Positive_Review"].fillna("No Positive").str.strip()
booking_london["Negative_Review"] = booking_london["Negative_Review"].fillna("No Negative").str.strip()
log("5.3  Cleaned review text fields")

booking_london["Review_Date"] = pd.to_datetime(booking_london["Review_Date"], errors="coerce")
log("5.4  Parsed Review_Date")

def extract_tag(tags_str, keywords):
    if pd.isna(tags_str):
        return np.nan
    for kw in keywords:
        if kw.lower() in tags_str.lower():
            return kw
    return np.nan

trip_keywords = ["Leisure trip", "Business trip"]
guest_keywords = ["Couple", "Solo traveler", "Group",
                   "Family with young children", "Family with older children",
                   "Travelers with friends"]

booking_london["trip_type"] = booking_london["Tags"].apply(lambda x: extract_tag(x, trip_keywords))
booking_london["guest_type"] = booking_london["Tags"].apply(lambda x: extract_tag(x, guest_keywords))
log(f"5.5  Extracted trip_type / guest_type from Tags "
    f"(trip_type missing: {booking_london['trip_type'].isna().mean()*100:.1f}%)")

before = len(booking_london)
booking_london = booking_london.drop_duplicates()
log(f"5.6  Removed {before - len(booking_london)} exact duplicate rows")

booking_london["sentiment_word_diff"] = (
    booking_london["Review_Total_Positive_Word_Counts"] - booking_london["Review_Total_Negative_Word_Counts"]
)
booking_london["has_positive_text"] = booking_london["Positive_Review"] != "No Positive"
booking_london["has_negative_text"] = booking_london["Negative_Review"] != "No Negative"
log("5.7  Built sentiment_word_diff proxy + text-presence flags")

booking_london.to_csv(f"{OUT_DIR}/booking_london_clean.csv", index=False)
log(f"5.8  SAVED booking_london_clean.csv — {booking_london.shape}\n")


# ============================================================
# STEP 6 — SCHEMA ALIGNMENT: Airbnb master + Booking.com -> ONE comparison table
# ============================================================
log("=" * 60)
log("STEP 6: SCHEMA ALIGNMENT")
log("=" * 60)

airbnb_common = pd.DataFrame({
    "platform": "airbnb",
    "city": "London",
    "record_id": airbnb_master["id"],
    "property_type": airbnb_master["room_type"],
    "price_per_night_gbp": airbnb_master["price"],
    "guests_capacity": airbnb_master["accommodates"],
    # rescale 0-5 -> 0-10; CHANGE to /10 instead if your file's scale is 0-100 (see step 1.9)
    "review_score_0to10": airbnb_master["review_scores_rating"] * 2,
    "review_count": airbnb_master["number_of_reviews"],
    "host_or_provider_id": airbnb_master["host_id"],
    "availability_365": airbnb_master["availability_365"],
    "instant_bookable": airbnb_master["instant_bookable"],
    "pct_days_booked": airbnb_master.get("pct_days_booked", np.nan),   # from calendar
    "price_volatility": airbnb_master.get("price_volatility", np.nan), # from calendar
    "trip_type": np.nan,   # Booking.com-only field
    "sentiment_signal": airbnb_master.get("avg_sentiment_score", np.nan),  # from reviews.csv
})
log("6.1  Mapped Airbnb master table to common schema (now includes calendar + review signals)")

booking_common = pd.DataFrame({
    "platform": "booking",
    "city": "London",
    "record_id": booking_london["Hotel_Name"],
    "property_type": "hotel_room",
    "price_per_night_gbp": np.nan,   # KNOWN GAP: no price field in this dataset
    "guests_capacity": np.nan,       # KNOWN GAP: not available at hotel level
    "review_score_0to10": booking_london["Reviewer_Score"],
    "review_count": booking_london.groupby("Hotel_Name")["Hotel_Name"].transform("count"),
    "host_or_provider_id": booking_london["Hotel_Name"],
    "availability_365": np.nan,
    "instant_bookable": np.nan,
    "pct_days_booked": np.nan,       # not applicable for Booking.com in this dataset
    "price_volatility": np.nan,
    "trip_type": booking_london["trip_type"],
    "sentiment_signal": booking_london["sentiment_word_diff"],
})
log("6.2  Mapped Booking.com to common schema")

comparison = pd.concat([airbnb_common, booking_common], ignore_index=True)
comparison.to_csv(f"{OUT_DIR}/comparison_schema.csv", index=False)

n_a, n_b = (comparison["platform"] == "airbnb").sum(), (comparison["platform"] == "booking").sum()
log(f"6.3  SAVED comparison_schema.csv — {comparison.shape[0]} rows ({n_a} Airbnb, {n_b} Booking.com)")

log("\n6.4  Field coverage by platform (% non-null):")
coverage = comparison.groupby("platform").apply(lambda d: d.notna().mean() * 100).round(1)
log(coverage.to_string())

# ============================================================
# STEP 7 — SAVE REPORT
# ============================================================
with open(f"{OUT_DIR}/cleaning_report.txt", "w") as f:
    f.write("\n".join(report_lines))

log(f"\nDONE. All outputs in: {os.path.abspath(OUT_DIR)}/")
