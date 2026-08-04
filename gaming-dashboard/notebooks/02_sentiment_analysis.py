import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

INPUT_PATH = "../data/reddit_comments_clean.csv"
OUTPUT_PATH = "../data/reddit_comments_scored.csv"

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def label_sentiment(compound):
    if compound >= POSITIVE_THRESHOLD:
        return "positive"
    if compound <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def main():
    df = pd.read_csv(INPUT_PATH)
    analyzer = SentimentIntensityAnalyzer()

    scores = df["comment_text"].apply(analyzer.polarity_scores).apply(pd.Series)
    scores = scores.rename(columns={
        "neg": "vader_neg",
        "neu": "vader_neu",
        "pos": "vader_pos",
        "compound": "vader_compound",
    })

    df = pd.concat([df, scores], axis=1)
    df["sentiment_label"] = df["vader_compound"].apply(label_sentiment)

    df.to_csv(OUTPUT_PATH, index=False)

    print("=== Sentiment distribution ===")
    print(df["sentiment_label"].value_counts())
    print()

    print("=== Mean compound score per subreddit ===")
    print(df.groupby("subreddit")["vader_compound"].mean().sort_values(ascending=False))
    print()

    print("=== Overall compound score ===")
    print(f"Mean:   {df['vader_compound'].mean():.4f}")
    print(f"Median: {df['vader_compound'].median():.4f}")
    print()

    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
