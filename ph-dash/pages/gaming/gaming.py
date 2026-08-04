import os
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# Player Perceptions of Artificial Intelligence in Video Games — sentiment
# analysis of 95 real, manually-collected Reddit comments (r/gamedev,
# r/antiai, r/pcmasterrace, r/OutOfTheLoop, r/IndieDev), scored with VADER.
# Replaces the earlier tech-history/literature-review version of this page.

PRIMARY_DARK = "#1f5c4a"

SENTIMENT_ORDER = ["positive", "neutral", "negative"]
SENTIMENT_COLORS = {
    "positive": "#2e7d32",
    "negative": "#c62828",
    "neutral": "#9e9e9e",
}
PROFANITY_COLORS = {"Contains profanity": "#c98a2c", "No profanity": "#3a6ea5"}

DATA_PATH = os.path.join(os.path.dirname(__file__), "gaming_data", "reddit_comments_scored.csv")

# Display-only masking for the comment browser and callout cards. Scoring
# always runs on the original unmasked text in reddit_comments_scored.csv —
# this never touches the underlying data, only what gets rendered.
_PROFANITY_PATTERN = re.compile(
    r"\b(fuck\w*|shit\w*|damn\w*|ass(?:hat|hole)?|bitch\w*|hell)\b", re.IGNORECASE
)


def _censor_profanity(text):
    return _PROFANITY_PATTERN.sub(lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1), text)


def _load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["approx_date"])
    df["sentiment_label"] = pd.Categorical(
        df["sentiment_label"], categories=SENTIMENT_ORDER, ordered=True
    )
    # Each approx_date bucket belongs to exactly one subreddit/thread, so
    # this grouping gives an honest categorical axis instead of implying
    # continuous daily sampling (approx_date is a coarse, relative-time
    # estimate derived from Reddit's relative timestamps).
    df["thread_key"] = df["subreddit"] + " · " + df["approx_date"].dt.strftime("%b %d, %Y")
    return df


DF = _load_data()
SUBREDDITS = sorted(DF["subreddit"].unique())
WORD_COUNT_MIN = int(DF["word_count"].min())
WORD_COUNT_MAX = int(DF["word_count"].max())
THEME_ORDER = DF["theme"].value_counts().index.tolist()
THREAD_ORDER = (
    DF[["thread_key", "approx_date"]]
    .drop_duplicates()
    .sort_values("approx_date")["thread_key"]
    .tolist()
)
_profanity_means = DF.groupby("contains_profanity", observed=True)["vader_compound"].mean()
MEAN_COMPOUND_PROFANE = _profanity_means.get(True, float("nan"))
MEAN_COMPOUND_CLEAN = _profanity_means.get(False, float("nan"))


def _kpi_card(value_id, initial_value, label, color=None):
    return dbc.Card(
        dbc.CardBody([
            html.H3(initial_value, id=value_id, className="mb-1 fw-bold", style={"color": color or PRIMARY_DARK}),
            html.P(label, className="text-muted mb-0 small text-uppercase"),
        ]),
        className="text-center shadow-sm h-100",
    )


def _chart_note(text):
    return html.P(text, className="text-muted small fst-italic mt-2 mb-0")


def _kpi_row():
    return dbc.Row([
        dbc.Col(_kpi_card("gaming-sentiment-kpi-total", str(len(DF)), "Comments Shown"), width=6, md=True, className="mb-2"),
        dbc.Col(_kpi_card("gaming-sentiment-kpi-pct-positive", "0%", "Positive", SENTIMENT_COLORS["positive"]), width=6, md=True, className="mb-2"),
        dbc.Col(_kpi_card("gaming-sentiment-kpi-pct-negative", "0%", "Negative", SENTIMENT_COLORS["negative"]), width=6, md=True, className="mb-2"),
        dbc.Col(_kpi_card("gaming-sentiment-kpi-pct-neutral", "0%", "Neutral", SENTIMENT_COLORS["neutral"]), width=6, md=True, className="mb-2"),
        dbc.Col(_kpi_card("gaming-sentiment-kpi-mean-compound", "0.000", "Mean Compound"), width=6, md=True, className="mb-2"),
        dbc.Col(_kpi_card("gaming-sentiment-kpi-threads", str(DF["thread_url"].fillna(DF["thread_title"]).nunique()), "# Threads"), width=6, md=True, className="mb-2"),
        dbc.Col(_kpi_card("gaming-sentiment-kpi-topics", str(DF["theme"].nunique()), "# AI Topics"), width=6, md=True, className="mb-2"),
    ], className="mb-1")


def _overall_caption():
    total = len(DF)
    pct_pos = (DF["sentiment_label"] == "positive").mean() * 100
    pct_neg = (DF["sentiment_label"] == "negative").mean() * 100
    pct_neu = (DF["sentiment_label"] == "neutral").mean() * 100
    mean_compound = DF["vader_compound"].mean()
    return html.P(
        f"KPIs above reflect the filters below. Unfiltered baseline, all {total} comments: "
        f"{pct_pos:.0f}% positive · {pct_neg:.0f}% negative · {pct_neu:.0f}% neutral · "
        f"mean compound {mean_compound:+.3f}.",
        className="text-muted small fst-italic mb-4",
    )


def _filter_bar():
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Subreddit", className="fw-bold small text-uppercase"),
                    dcc.Dropdown(
                        id="gaming-sentiment-subreddit-filter",
                        options=[{"label": s, "value": s} for s in SUBREDDITS],
                        value=SUBREDDITS,
                        multi=True,
                    ),
                ], md=6),
                dbc.Col([
                    html.Label("Theme", className="fw-bold small text-uppercase"),
                    dcc.Dropdown(
                        id="gaming-sentiment-theme-filter",
                        options=[{"label": t, "value": t} for t in THEME_ORDER],
                        value=THEME_ORDER,
                        multi=True,
                    ),
                ], md=6),
            ], className="g-3 align-items-start mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Sentiment", className="fw-bold small text-uppercase"),
                    dcc.Checklist(
                        id="gaming-sentiment-sentiment-filter",
                        options=[
                            {"label": f" {s.capitalize()}", "value": s} for s in SENTIMENT_ORDER
                        ],
                        value=SENTIMENT_ORDER,
                        inline=True,
                        inputStyle={"marginRight": "4px", "marginLeft": "12px"},
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Word Count", className="fw-bold small text-uppercase"),
                    dcc.RangeSlider(
                        id="gaming-sentiment-wordcount-filter",
                        min=WORD_COUNT_MIN,
                        max=WORD_COUNT_MAX,
                        value=[WORD_COUNT_MIN, WORD_COUNT_MAX],
                        tooltip={"placement": "bottom", "always_visible": False},
                        allowCross=False,
                    ),
                ], md=8),
            ], className="g-3 align-items-start"),
        ]),
        className="shadow-sm mb-4",
    )


def _comment_table():
    return dash_table.DataTable(
        id="gaming-sentiment-comment-table",
        columns=[
            {"name": "Subreddit", "id": "subreddit"},
            {"name": "Theme", "id": "theme"},
            {"name": "Sentiment", "id": "sentiment_label"},
            {"name": "Compound", "id": "vader_compound"},
            {"name": "Comment", "id": "comment_text"},
            {"name": "Upvotes", "id": "upvotes"},
            {"name": "Source", "id": "thread_url", "presentation": "markdown"},
        ],
        sort_action="native",
        page_size=10,
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "fontFamily": "inherit",
            "fontSize": "0.85rem",
            "padding": "8px",
        },
        style_cell_conditional=[
            {"if": {"column_id": "comment_text"}, "width": "45%"},
            {"if": {"column_id": "subreddit"}, "width": "12%"},
        ],
        style_data_conditional=[
            {"if": {"filter_query": "{sentiment_label} = positive"}, "backgroundColor": "#eaf5ea"},
            {"if": {"filter_query": "{sentiment_label} = negative"}, "backgroundColor": "#fbeaea"},
        ],
        style_header={"fontWeight": "bold"},
    )


def _profanity_figure():
    plot_df = DF.copy()
    plot_df["profanity_label"] = plot_df["contains_profanity"].map(
        {True: "Contains profanity", False: "No profanity"}
    )
    fig = px.box(
        plot_df,
        x="profanity_label",
        y="vader_compound",
        points="all",
        color="profanity_label",
        color_discrete_map=PROFANITY_COLORS,
        title="Compound Score by Profanity Flag (all 95 comments, unfiltered)",
        labels={"profanity_label": "", "vader_compound": "Compound score"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))
    return fig


def _extreme_comment_body(row):
    if row is None:
        return html.P("No comments match the current filters.", className="text-muted mb-0")
    return html.Div([
        html.Div([
            dbc.Badge(row["subreddit"], color="secondary", className="me-2"),
            html.Span(f"compound {row['vader_compound']:+.3f}", className="fw-bold"),
        ], className="mb-2"),
        html.P(_censor_profanity(row["comment_text"]), className="mb-2"),
        html.A("View source thread ↗", href=row["thread_url"], target="_blank", className="small"),
    ])


def layout():
    return dbc.Container([

        dbc.Row(dbc.Col([
            dcc.Link("← Back to Hub", href="/", className="back-link"),
            html.H1("Player Perceptions of Artificial Intelligence in Video Games", className="mt-3 mb-1"),
            html.P(
                "Built from 95 real Reddit comments collected across 5 subreddits "
                "(r/gamedev, r/antiai, r/pcmasterrace, r/OutOfTheLoop, r/IndieDev), "
                "scored with VADER sentiment analysis.",
                className="text-muted mb-4",
            ),
        ])),

        _kpi_row(),
        _overall_caption(),
        _filter_bar(),

        dbc.Row([
            dbc.Col(dcc.Graph(id="gaming-sentiment-pie", config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(id="gaming-sentiment-subreddit-bar", config={"displayModeBar": False}), md=6),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="gaming-sentiment-theme-sentiment-bar", config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(id="gaming-sentiment-theme-frequency-bar", config={"displayModeBar": False}), md=6),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="gaming-sentiment-histogram", config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(id="gaming-sentiment-wordcount-scatter", config={"displayModeBar": False}), md=6),
        ], className="g-3 mb-3"),

        dbc.Row(dbc.Col([
            dcc.Graph(id="gaming-sentiment-time-scatter", config={"displayModeBar": False}),
            _chart_note(
                "Each position on the x-axis is one Reddit discussion thread (grouped by "
                "subreddit + collection-relative date bucket), not an independent daily "
                "sample. approx_date is a coarse estimate derived from Reddit's relative "
                "timestamps (e.g. \"~2mo before collection\") — the 95 comments span only "
                "about 7 distinct date buckets, not 7 months of daily data."
            ),
        ], md=12), className="g-3 mb-4"),

        html.H4("Most Positive / Most Negative Comment", className="mt-2 mb-1"),
        html.P("Updates with the filters above.", className="text-muted small mb-3"),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Most Positive Comment"),
                    dbc.CardBody(id="gaming-sentiment-most-positive-body"),
                ], className="shadow-sm h-100", style={"borderLeft": f"4px solid {SENTIMENT_COLORS['positive']}"}),
                md=6,
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Most Negative Comment"),
                    dbc.CardBody(id="gaming-sentiment-most-negative-body"),
                ], className="shadow-sm h-100", style={"borderLeft": f"4px solid {SENTIMENT_COLORS['negative']}"}),
                md=6,
            ),
        ], className="g-3 mb-4"),

        html.H4("Data Quality Note: Profanity vs. Sentiment Score", className="mt-2 mb-1"),
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(figure=_profanity_figure(), config={"displayModeBar": False}),
                _chart_note(
                    f"Comments flagged as containing profanity score higher on average "
                    f"(mean compound {MEAN_COMPOUND_PROFANE:+.3f}) than non-profane comments "
                    f"(mean compound {MEAN_COMPOUND_CLEAN:+.3f}). This is likely VADER "
                    f"over-crediting intensifiers/slang rather than genuine extra positivity — "
                    f"see the Task 6 limitations discussion. Computed across all 95 comments; "
                    f"not affected by the filters above."
                ),
            ]),
            className="shadow-sm mb-4",
        ),

        html.H4("Browse Comments", className="mt-2 mb-1"),
        html.P(
            "Sorted by compound score (highest first) by default, filtered by the controls "
            "above. Source links trace each comment back to its original Reddit thread.",
            className="text-muted small mb-3",
        ),
        dbc.Card(dbc.CardBody(_comment_table()), className="shadow-sm mb-4"),

        html.Hr(),

        html.P(
            "Sentiment scored with VADER (Hutto & Gilbert, 2014). Sample is 95 "
            "manually-collected Reddit comments across 5 subreddits — not a random or "
            "statistically representative sample of players.",
            className="text-muted small mb-4",
        ),

    ], fluid=True, className="page-container gaming-page py-4")


def register_callbacks(app):
    @app.callback(
        Output("gaming-sentiment-kpi-total", "children"),
        Output("gaming-sentiment-kpi-pct-positive", "children"),
        Output("gaming-sentiment-kpi-pct-negative", "children"),
        Output("gaming-sentiment-kpi-pct-neutral", "children"),
        Output("gaming-sentiment-kpi-mean-compound", "children"),
        Output("gaming-sentiment-kpi-threads", "children"),
        Output("gaming-sentiment-kpi-topics", "children"),
        Output("gaming-sentiment-pie", "figure"),
        Output("gaming-sentiment-subreddit-bar", "figure"),
        Output("gaming-sentiment-theme-sentiment-bar", "figure"),
        Output("gaming-sentiment-theme-frequency-bar", "figure"),
        Output("gaming-sentiment-histogram", "figure"),
        Output("gaming-sentiment-wordcount-scatter", "figure"),
        Output("gaming-sentiment-time-scatter", "figure"),
        Output("gaming-sentiment-most-positive-body", "children"),
        Output("gaming-sentiment-most-negative-body", "children"),
        Output("gaming-sentiment-comment-table", "data"),
        Input("gaming-sentiment-subreddit-filter", "value"),
        Input("gaming-sentiment-theme-filter", "value"),
        Input("gaming-sentiment-sentiment-filter", "value"),
        Input("gaming-sentiment-wordcount-filter", "value"),
    )
    def _update(subreddits, themes, sentiments, word_count_range):
        subreddits = subreddits or []
        themes = themes or []
        sentiments = sentiments or []
        lo, hi = word_count_range

        filtered = DF[
            DF["subreddit"].isin(subreddits)
            & DF["theme"].isin(themes)
            & DF["sentiment_label"].isin(sentiments)
            & DF["word_count"].between(lo, hi)
        ]

        total = len(filtered)
        if total:
            pct_pos = f"{(filtered['sentiment_label'] == 'positive').mean() * 100:.0f}%"
            pct_neg = f"{(filtered['sentiment_label'] == 'negative').mean() * 100:.0f}%"
            pct_neu = f"{(filtered['sentiment_label'] == 'neutral').mean() * 100:.0f}%"
            mean_compound_kpi = f"{filtered['vader_compound'].mean():+.3f}"
        else:
            pct_pos = pct_neg = pct_neu = "0%"
            mean_compound_kpi = "n/a"

        n_threads = str(filtered["thread_url"].fillna(filtered["thread_title"]).nunique())
        n_topics = str(filtered["theme"].nunique())

        counts = (
            filtered["sentiment_label"]
            .value_counts()
            .reindex(SENTIMENT_ORDER)
            .fillna(0)
            .reset_index()
        )
        counts.columns = ["sentiment_label", "count"]
        pie_fig = px.pie(
            counts, names="sentiment_label", values="count",
            color="sentiment_label", color_discrete_map=SENTIMENT_COLORS,
            hole=0.45, title="Comments by Sentiment",
        )
        pie_fig.update_traces(textinfo="value+percent")
        pie_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10))

        by_subreddit = (
            filtered.groupby("subreddit", observed=True)["vader_compound"]
            .agg(mean_compound="mean", n="count")
            .sort_values("mean_compound")
            .reset_index()
        )
        bar_fig = px.bar(
            by_subreddit, x="mean_compound", y="subreddit", orientation="h",
            text=by_subreddit["n"].apply(lambda n: f"n={n}"),
            title="Mean Compound Score by Subreddit",
            labels={"mean_compound": "Mean compound score", "subreddit": ""},
        )
        bar_fig.update_traces(marker_color=PRIMARY_DARK, textposition="outside")
        bar_fig.add_vline(x=0, line_dash="dash", line_color="gray")
        bar_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))

        # Theme Frequency — comment counts per theme, sorted by full-dataset
        # count descending, stable across filters (zero-count themes still shown)
        theme_freq = (
            filtered["theme"].value_counts().reindex(THEME_ORDER).fillna(0).reset_index()
        )
        theme_freq.columns = ["theme", "count"]
        theme_freq_fig = px.bar(
            theme_freq, x="theme", y="count",
            category_orders={"theme": THEME_ORDER},
            title="Theme Frequency",
            labels={"theme": "", "count": "Comments"},
        )
        theme_freq_fig.update_traces(marker_color=PRIMARY_DARK)
        theme_freq_fig.update_xaxes(tickangle=-30)
        theme_freq_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))

        # Sentiment by Theme — stacked Positive/Negative/Neutral breakdown per
        # theme, with an n= label above each bar so low-sample themes (e.g.
        # Copyright and ownership, n=2) aren't visually overstated.
        theme_sentiment = (
            filtered.groupby(["theme", "sentiment_label"], observed=True)
            .size()
            .reset_index(name="count")
        )
        theme_sentiment_fig = px.bar(
            theme_sentiment, x="theme", y="count",
            color="sentiment_label", color_discrete_map=SENTIMENT_COLORS,
            category_orders={"theme": THEME_ORDER, "sentiment_label": SENTIMENT_ORDER},
            barmode="stack",
            title="Sentiment by Theme",
            labels={"theme": "", "count": "Comments"},
        )
        theme_sentiment_fig.update_xaxes(tickangle=-30)
        theme_totals = filtered.groupby("theme", observed=True).size()
        for theme in THEME_ORDER:
            n = int(theme_totals.get(theme, 0))
            if n > 0:
                theme_sentiment_fig.add_annotation(
                    x=theme, y=n, text=f"n={n}", showarrow=False, yshift=12, font={"size": 11}
                )
        theme_sentiment_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))

        hist_fig = px.histogram(
            filtered, x="vader_compound", nbins=20,
            title="Distribution of Compound Scores",
            labels={"vader_compound": "Compound score"},
        )
        hist_fig.update_traces(marker_color=PRIMARY_DARK)
        hist_fig.add_vline(x=0, line_dash="dash", line_color="gray")
        hist_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))

        scatter_fig = px.scatter(
            filtered, x="word_count", y="vader_compound",
            color="sentiment_label", color_discrete_map=SENTIMENT_COLORS,
            title="Word Count vs. Compound Score",
            labels={"word_count": "Word count", "vader_compound": "Compound score"},
            hover_data=["subreddit"],
        )
        scatter_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))

        time_fig = px.scatter(
            filtered, x="thread_key", y="vader_compound",
            color="sentiment_label", color_discrete_map=SENTIMENT_COLORS,
            category_orders={"thread_key": THREAD_ORDER},
            title="Compound Score by Discussion Thread (chronological order)",
            labels={"thread_key": "Discussion thread", "vader_compound": "Compound score"},
            hover_data=["subreddit"],
        )
        if not filtered.empty:
            thread_mean = (
                filtered.groupby("thread_key", observed=True)["vader_compound"]
                .mean()
                .reindex(THREAD_ORDER)
                .dropna()
                .reset_index()
            )
            time_fig.add_trace(go.Scatter(
                x=thread_mean["thread_key"], y=thread_mean["vader_compound"],
                mode="lines+markers", name="Thread mean",
                line={"color": "black", "dash": "dot"},
                marker={"symbol": "diamond", "size": 8, "color": "black"},
            ))
        time_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        time_fig.update_xaxes(categoryorder="array", categoryarray=THREAD_ORDER)
        time_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff", margin=dict(t=40, b=10))

        if filtered.empty:
            most_pos_body = _extreme_comment_body(None)
            most_neg_body = _extreme_comment_body(None)
        else:
            most_pos_body = _extreme_comment_body(filtered.loc[filtered["vader_compound"].idxmax()])
            most_neg_body = _extreme_comment_body(filtered.loc[filtered["vader_compound"].idxmin()])

        table_data = filtered.copy()
        table_data["vader_compound"] = table_data["vader_compound"].round(3)
        table_data["comment_text"] = table_data["comment_text"].apply(_censor_profanity)
        table_data["thread_url"] = table_data["thread_url"].apply(lambda url: f"[Link]({url})")
        table_data = table_data.sort_values("vader_compound", ascending=False)

        return (
            str(total), pct_pos, pct_neg, pct_neu, mean_compound_kpi, n_threads, n_topics,
            pie_fig, bar_fig, theme_sentiment_fig, theme_freq_fig, hist_fig, scatter_fig, time_fig,
            most_pos_body, most_neg_body,
            table_data.to_dict("records"),
        )


# This block here is necessary to be able to run this file individually,
# without the app_tech_disruptions hub page.
if __name__ == "__main__":
    import dash

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.LITERA],
        assets_folder=os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
    )

    app.layout = layout()
    register_callbacks(app)
    app.run(debug=True)
