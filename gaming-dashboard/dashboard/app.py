import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dash_table, dcc, html

from data import SENTIMENT_COLORS, SENTIMENT_ORDER, censor_profanity, load_data

df = load_data()

SUBREDDITS = sorted(df["subreddit"].unique())
WORD_COUNT_MIN = int(df["word_count"].min())
WORD_COUNT_MAX = int(df["word_count"].max())
THEME_ORDER = df["theme"].value_counts().index.tolist()

# Each approx_date bucket belongs to exactly one subreddit/thread, so this
# grouping gives an honest categorical axis instead of implying continuous
# daily sampling (approx_date is a coarse, relative-time estimate).
df["thread_key"] = df["subreddit"] + " · " + df["approx_date"].dt.strftime("%b %d, %Y")
THREAD_ORDER = (
    df[["thread_key", "approx_date"]]
    .drop_duplicates()
    .sort_values("approx_date")["thread_key"]
    .tolist()
)

PROFANITY_COLORS = {"Contains profanity": "#c98a2c", "No profanity": "#3a6ea5"}
_profanity_means = df.groupby("contains_profanity", observed=True)["vader_compound"].mean()
MEAN_COMPOUND_PROFANE = _profanity_means.get(True, float("nan"))
MEAN_COMPOUND_CLEAN = _profanity_means.get(False, float("nan"))

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Player Perceptions of AI in Video Games"
server = app.server


def kpi_card(label, value_id, initial_value, color=None):
    style = {"color": color} if color else {}
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(initial_value, id=value_id, className="card-title mb-0", style=style),
                html.P(label, className="card-text text-muted mb-0"),
            ]
        ),
        className="text-center shadow-sm",
    )


def build_kpi_row():
    return dbc.Row(
        [
            dbc.Col(kpi_card("Comments Shown", "kpi-total", str(len(df))), md=True),
            dbc.Col(kpi_card("% Positive", "kpi-pct-positive", "0%", SENTIMENT_COLORS["positive"]), md=True),
            dbc.Col(kpi_card("% Negative", "kpi-pct-negative", "0%", SENTIMENT_COLORS["negative"]), md=True),
            dbc.Col(kpi_card("% Neutral", "kpi-pct-neutral", "0%", SENTIMENT_COLORS["neutral"]), md=True),
            dbc.Col(kpi_card("Mean Compound", "kpi-mean-compound", "0.000"), md=True),
            dbc.Col(kpi_card("# Threads", "kpi-threads", str(df["thread_url"].fillna(df["thread_title"]).nunique())), md=True),
            dbc.Col(kpi_card("# AI Topics", "kpi-topics", str(df["theme"].nunique())), md=True),
        ],
        className="g-3 mb-2",
    )


def build_overall_caption():
    total = len(df)
    pct_pos = (df["sentiment_label"] == "positive").mean() * 100
    pct_neg = (df["sentiment_label"] == "negative").mean() * 100
    pct_neu = (df["sentiment_label"] == "neutral").mean() * 100
    mean_compound = df["vader_compound"].mean()
    return html.P(
        f"KPIs above reflect the filters below. Unfiltered baseline, all {total} comments: "
        f"{pct_pos:.0f}% positive · {pct_neg:.0f}% negative · {pct_neu:.0f}% neutral · "
        f"mean compound {mean_compound:+.3f}.",
        className="text-muted small fst-italic mb-4",
    )


def build_filter_bar():
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Subreddit", className="fw-bold"),
                                dcc.Dropdown(
                                    id="subreddit-filter",
                                    options=[{"label": s, "value": s} for s in SUBREDDITS],
                                    value=SUBREDDITS,
                                    multi=True,
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Theme", className="fw-bold"),
                                dcc.Dropdown(
                                    id="theme-filter",
                                    options=[{"label": t, "value": t} for t in THEME_ORDER],
                                    value=THEME_ORDER,
                                    multi=True,
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="g-3 align-items-start mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Sentiment", className="fw-bold"),
                                dcc.Checklist(
                                    id="sentiment-filter",
                                    options=[
                                        {"label": f" {s.capitalize()}", "value": s}
                                        for s in SENTIMENT_ORDER
                                    ],
                                    value=SENTIMENT_ORDER,
                                    inline=True,
                                    inputStyle={"marginRight": "4px", "marginLeft": "12px"},
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                html.Label("Word Count", className="fw-bold"),
                                dcc.RangeSlider(
                                    id="wordcount-filter",
                                    min=WORD_COUNT_MIN,
                                    max=WORD_COUNT_MAX,
                                    value=[WORD_COUNT_MIN, WORD_COUNT_MAX],
                                    tooltip={"placement": "bottom", "always_visible": False},
                                    allowCross=False,
                                ),
                            ],
                            md=8,
                        ),
                    ],
                    className="g-3 align-items-start",
                ),
            ]
        ),
        className="shadow-sm mb-4",
    )


def build_profanity_figure():
    plot_df = df.copy()
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
    fig.update_layout(showlegend=False)
    return fig


def extreme_comment_body(row):
    if row is None:
        return html.P("No comments match the current filters.", className="text-muted mb-0")
    return html.Div(
        [
            html.Div(
                [
                    dbc.Badge(row["subreddit"], color="secondary", className="me-2"),
                    html.Span(f"compound {row['vader_compound']:+.3f}", className="fw-bold"),
                ],
                className="mb-2",
            ),
            html.P(censor_profanity(row["comment_text"]), className="mb-2"),
            html.A("View source thread ↗", href=row["thread_url"], target="_blank", className="small"),
        ]
    )


app.layout = dbc.Container(
    [
        html.Div(
            [
                html.H2("Player Perceptions of Artificial Intelligence in Video Games"),
                html.P(
                    "Built from 95 real Reddit comments collected across 5 subreddits "
                    "(r/gamedev, r/antiai, r/pcmasterrace, r/OutOfTheLoop, r/IndieDev), "
                    "scored with VADER sentiment analysis.",
                    className="text-muted",
                ),
            ],
            className="my-4",
        ),
        build_kpi_row(),
        build_overall_caption(),
        build_filter_bar(),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="sentiment-pie"), md=6),
                dbc.Col(dcc.Graph(id="subreddit-bar"), md=6),
            ],
            className="g-3 mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="theme-sentiment-bar"), md=6),
                dbc.Col(dcc.Graph(id="theme-frequency-bar"), md=6),
            ],
            className="g-3 mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="compound-histogram"), md=6),
                dbc.Col(dcc.Graph(id="wordcount-scatter"), md=6),
            ],
            className="g-3 mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id="time-scatter"),
                        html.P(
                            "Each position on the x-axis is one Reddit discussion thread "
                            "(grouped by subreddit + collection-relative date bucket), not an "
                            "independent daily sample. approx_date is a coarse estimate derived "
                            "from Reddit's relative timestamps (e.g. “~2mo before "
                            "collection”) — the 95 comments span only about 7 distinct "
                            "date buckets, not 7 months of daily data.",
                            className="text-muted small fst-italic",
                        ),
                    ],
                    md=12,
                ),
            ],
            className="g-3 mb-4",
        ),
        html.H4("Most Positive / Most Negative Comment", className="mt-2"),
        html.P(
            "Updates with the filters above.",
            className="text-muted small mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Most Positive Comment"),
                            dbc.CardBody(id="most-positive-body"),
                        ],
                        className="shadow-sm h-100",
                        style={"borderLeft": f"4px solid {SENTIMENT_COLORS['positive']}"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Most Negative Comment"),
                            dbc.CardBody(id="most-negative-body"),
                        ],
                        className="shadow-sm h-100",
                        style={"borderLeft": f"4px solid {SENTIMENT_COLORS['negative']}"},
                    ),
                    md=6,
                ),
            ],
            className="g-3 mb-4",
        ),
        html.H4("Data Quality Note: Profanity vs. Sentiment Score", className="mt-2"),
        dbc.Card(
            dbc.CardBody(
                [
                    dcc.Graph(figure=build_profanity_figure()),
                    html.P(
                        f"Comments flagged as containing profanity score higher on average "
                        f"(mean compound {MEAN_COMPOUND_PROFANE:+.3f}) than non-profane comments "
                        f"(mean compound {MEAN_COMPOUND_CLEAN:+.3f}). This is likely VADER "
                        f"over-crediting intensifiers/slang rather than genuine extra positivity "
                        f"— see the Task 6 limitations discussion. Computed across all 95 "
                        f"comments; not affected by the filters above.",
                        className="text-muted small fst-italic mt-2 mb-0",
                    ),
                ]
            ),
            className="shadow-sm mb-4",
        ),
        html.H4("Browse Comments", className="mt-2"),
        html.P("Sorted by compound score (highest first) by default.", className="text-muted small mb-2"),
        dash_table.DataTable(
            id="comment-table",
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
                {
                    "if": {"filter_query": "{sentiment_label} = positive"},
                    "backgroundColor": "#eaf5ea",
                },
                {
                    "if": {"filter_query": "{sentiment_label} = negative"},
                    "backgroundColor": "#fbeaea",
                },
            ],
            style_header={"fontWeight": "bold"},
        ),
        html.Hr(className="mt-4"),
        html.P(
            [
                "Sentiment scored with VADER (Hutto & Gilbert, 2014). Sample is 95 "
                "manually-collected Reddit comments across 5 subreddits — not a "
                "random or statistically representative sample of players.",
            ],
            className="text-muted small mb-4",
        ),
    ],
    fluid=True,
)


@app.callback(
    Output("kpi-total", "children"),
    Output("kpi-pct-positive", "children"),
    Output("kpi-pct-negative", "children"),
    Output("kpi-pct-neutral", "children"),
    Output("kpi-mean-compound", "children"),
    Output("kpi-threads", "children"),
    Output("kpi-topics", "children"),
    Output("sentiment-pie", "figure"),
    Output("subreddit-bar", "figure"),
    Output("theme-sentiment-bar", "figure"),
    Output("theme-frequency-bar", "figure"),
    Output("compound-histogram", "figure"),
    Output("wordcount-scatter", "figure"),
    Output("time-scatter", "figure"),
    Output("most-positive-body", "children"),
    Output("most-negative-body", "children"),
    Output("comment-table", "data"),
    Input("subreddit-filter", "value"),
    Input("theme-filter", "value"),
    Input("sentiment-filter", "value"),
    Input("wordcount-filter", "value"),
)
def update_dashboard(subreddits, themes, sentiments, word_count_range):
    subreddits = subreddits or []
    themes = themes or []
    sentiments = sentiments or []
    lo, hi = word_count_range

    filtered = df[
        df["subreddit"].isin(subreddits)
        & df["theme"].isin(themes)
        & df["sentiment_label"].isin(sentiments)
        & df["word_count"].between(lo, hi)
    ]

    # KPIs
    total = len(filtered)
    if total:
        pct_pos = f"{(filtered['sentiment_label'] == 'positive').mean() * 100:.0f}%"
        pct_neg = f"{(filtered['sentiment_label'] == 'negative').mean() * 100:.0f}%"
        pct_neu = f"{(filtered['sentiment_label'] == 'neutral').mean() * 100:.0f}%"
        mean_compound = f"{filtered['vader_compound'].mean():+.3f}"
    else:
        pct_pos = pct_neg = pct_neu = "0%"
        mean_compound = "n/a"

    n_threads = str(filtered["thread_url"].fillna(filtered["thread_title"]).nunique())
    n_topics = str(filtered["theme"].nunique())

    # a. sentiment distribution
    counts = (
        filtered["sentiment_label"]
        .value_counts()
        .reindex(SENTIMENT_ORDER)
        .fillna(0)
        .reset_index()
    )
    counts.columns = ["sentiment_label", "count"]
    pie_fig = px.pie(
        counts,
        names="sentiment_label",
        values="count",
        color="sentiment_label",
        color_discrete_map=SENTIMENT_COLORS,
        hole=0.45,
        title="Comments by Sentiment",
    )
    pie_fig.update_traces(textinfo="value+percent")

    # b. mean compound per subreddit, with sample size labeled on each bar
    by_subreddit = (
        filtered.groupby("subreddit", observed=True)["vader_compound"]
        .agg(mean_compound="mean", n="count")
        .sort_values("mean_compound")
        .reset_index()
    )
    bar_fig = px.bar(
        by_subreddit,
        x="mean_compound",
        y="subreddit",
        orientation="h",
        text=by_subreddit["n"].apply(lambda n: f"n={n}"),
        title="Mean Compound Score by Subreddit",
        labels={"mean_compound": "Mean compound score", "subreddit": ""},
    )
    bar_fig.update_traces(marker_color="#3a6ea5", textposition="outside")
    bar_fig.add_vline(x=0, line_dash="dash", line_color="gray")

    # Theme Frequency — comment counts per theme, sorted by full-dataset
    # count descending, stable across filters (zero-count themes still shown)
    theme_freq = (
        filtered["theme"]
        .value_counts()
        .reindex(THEME_ORDER)
        .fillna(0)
        .reset_index()
    )
    theme_freq.columns = ["theme", "count"]
    theme_freq_fig = px.bar(
        theme_freq,
        x="theme",
        y="count",
        category_orders={"theme": THEME_ORDER},
        title="Theme Frequency",
        labels={"theme": "", "count": "Comments"},
    )
    theme_freq_fig.update_traces(marker_color="#3a6ea5")
    theme_freq_fig.update_xaxes(tickangle=-30)

    # Sentiment by Theme — stacked Positive/Negative/Neutral breakdown per
    # theme, with an n= label above each bar so low-sample themes (e.g.
    # Copyright and ownership, n=2) aren't visually overstated.
    theme_sentiment = (
        filtered.groupby(["theme", "sentiment_label"], observed=True)
        .size()
        .reset_index(name="count")
    )
    theme_sentiment_fig = px.bar(
        theme_sentiment,
        x="theme",
        y="count",
        color="sentiment_label",
        color_discrete_map=SENTIMENT_COLORS,
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

    # c. histogram of compound scores
    hist_fig = px.histogram(
        filtered,
        x="vader_compound",
        nbins=20,
        title="Distribution of Compound Scores",
        labels={"vader_compound": "Compound score"},
    )
    hist_fig.update_traces(marker_color="#3a6ea5")
    hist_fig.add_vline(x=0, line_dash="dash", line_color="gray")

    # e. word count vs compound
    scatter_fig = px.scatter(
        filtered,
        x="word_count",
        y="vader_compound",
        color="sentiment_label",
        color_discrete_map=SENTIMENT_COLORS,
        title="Word Count vs. Compound Score",
        labels={"word_count": "Word count", "vader_compound": "Compound score"},
        hover_data=["subreddit"],
    )

    # d. compound by discussion thread (chronological, categorical — not a
    # continuous date axis, since approx_date is a coarse relative estimate)
    time_fig = px.scatter(
        filtered,
        x="thread_key",
        y="vader_compound",
        color="sentiment_label",
        color_discrete_map=SENTIMENT_COLORS,
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
        time_fig.add_trace(
            go.Scatter(
                x=thread_mean["thread_key"],
                y=thread_mean["vader_compound"],
                mode="lines+markers",
                name="Thread mean",
                line={"color": "black", "dash": "dot"},
                marker={"symbol": "diamond", "size": 8, "color": "black"},
            )
        )
    time_fig.add_hline(y=0, line_dash="dash", line_color="gray")
    time_fig.update_xaxes(categoryorder="array", categoryarray=THREAD_ORDER)

    # most positive / most negative comment in current view
    if filtered.empty:
        most_pos_body = extreme_comment_body(None)
        most_neg_body = extreme_comment_body(None)
    else:
        most_pos_body = extreme_comment_body(filtered.loc[filtered["vader_compound"].idxmax()])
        most_neg_body = extreme_comment_body(filtered.loc[filtered["vader_compound"].idxmin()])

    table_data = filtered.copy()
    table_data["vader_compound"] = table_data["vader_compound"].round(3)
    table_data["comment_text"] = table_data["comment_text"].apply(censor_profanity)
    table_data["thread_url"] = table_data["thread_url"].apply(
        lambda url: f"[Link]({url})"
    )
    table_data = table_data.sort_values("vader_compound", ascending=False)

    return (
        str(total),
        pct_pos,
        pct_neg,
        pct_neu,
        mean_compound,
        n_threads,
        n_topics,
        pie_fig,
        bar_fig,
        theme_sentiment_fig,
        theme_freq_fig,
        hist_fig,
        scatter_fig,
        time_fig,
        most_pos_body,
        most_neg_body,
        table_data.to_dict("records"),
    )


if __name__ == "__main__":
    app.run(debug=True)
