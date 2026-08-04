import os
import re

import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reddit_comments_scored.csv")

SENTIMENT_ORDER = ["positive", "neutral", "negative"]
SENTIMENT_COLORS = {
    "positive": "#2e7d32",
    "negative": "#c62828",
    "neutral": "#9e9e9e",
}

# Display-only masking for the comment browser and callout cards. Scoring
# always runs on the original unmasked text in reddit_comments_scored.csv —
# this never touches the underlying data, only what gets rendered.
_PROFANITY_PATTERN = re.compile(
    r"\b(fuck\w*|shit\w*|damn\w*|ass(?:hat|hole)?|bitch\w*|hell)\b", re.IGNORECASE
)


def censor_profanity(text):
    return _PROFANITY_PATTERN.sub(lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1), text)


def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["approx_date"])
    df["sentiment_label"] = pd.Categorical(
        df["sentiment_label"], categories=SENTIMENT_ORDER, ordered=True
    )
    return df
