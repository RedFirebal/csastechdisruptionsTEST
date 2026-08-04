import numpy as np
import pandas as pd
from datetime import date
from io import StringIO
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# This try and except block is here so that this film.py file can run independently
# when it doesn't know the parent directory.
try:
    from .film_data.tmdb_fetcher import fetch_cgi_movies, fetch_tmdb_reviews
    from .film_data.manual_movies import get_manual_movies_df
    from .film_data.letterboxd_fetcher import fetch_letterboxd_ratings
    from .film_data.cgi_revenue import build_cgi_revenue_chart
    from .film_data.ai_acceptance import build_ai_acceptance_chart
    from .film_data.rotten_tomatoes_fetcher import (
        get_movie_options, build_freshness_chart, MAX_SELECTED_FILMS,
    )
except ImportError:
    from film_data.tmdb_fetcher import fetch_cgi_movies, fetch_tmdb_reviews
    from film_data.manual_movies import get_manual_movies_df
    from film_data.letterboxd_fetcher import fetch_letterboxd_ratings
    from film_data.cgi_revenue import build_cgi_revenue_chart
    from film_data.ai_acceptance import build_ai_acceptance_chart
    from film_data.rotten_tomatoes_fetcher import (
        get_movie_options, build_freshness_chart, MAX_SELECTED_FILMS,
    )

# Safety cap
MAX_LETTERBOXD_FILMS = 500

# Google Trends parameters
GOOGLE_TRENDS_KEYWORD = "/m/021ny"
GOOGLE_TRENDS_START = "2004-01-01"
GOOGLE_TRENDS_END = "2026-01-01"
GOOGLE_TRENDS_EMBED_LOADER = "https://ssl.gstatic.com/trends_nrtr/3620_RC01/embed_loader.js"

# TimelineJS embed source
TIMELINE_EMBED_SRC = (
    "https://cdn.knightlab.com/libs/timeline3/latest/embed/index.html"
    "?source=v2%3A2PACX-1vQ0Z4wD57GylzOlWllKd5gJMt14m5984ko3HoVs0CokFmkZnpR2QmD7QCHhUlQgrBN3evTZanaFhZz-"
    "&font=Default&lang=en&initial_zoom=2&width=100%25&height=650"
)


def _google_trends_srcdoc(start_date: str, end_date: str) -> str:
    time_range = f"{start_date} {end_date}"
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          html, body {{ margin: 0; padding: 0; }}
          .trends-widget {{ width: 100%; }}
        </style>
      </head>
      <body>
        <div class="trends-widget"></div>
        <script type="text/javascript" src="{GOOGLE_TRENDS_EMBED_LOADER}"></script>
        <script type="text/javascript">
          trends.embed.renderExploreWidgetTo(
            document.querySelector(".trends-widget"),
            "TIMESERIES",
            {{
              "comparisonItem": [{{"keyword": "{GOOGLE_TRENDS_KEYWORD}", "geo": "", "time": "{time_range}"}}],
              "category": 0,
              "property": ""
            }},
            {{
              "guestPath": "https://trends.google.com:443/trends/embed/"
            }}
          );
        </script>
      </body>
    </html>
    """


def _empty_fig(message: str) -> go.Figure:
    return go.Figure().update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20),
        annotations=[{
            "text": message,
            "showarrow": False,
            "font": {"size": 13, "color": "#999"},
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5,
        }],
    )

def layout():
    return dbc.Container([
        dcc.Store(id="film-tmdb-store"),
        dcc.Store(id="film-sentiment-store"),

        # Header
        dbc.Row(dbc.Col([
            dcc.Link("← Back to Hub", href="/", className="back-link"),
            html.H1("CGI in Film: Rise & Public Perception", className="mt-3 mb-1"),
            html.P(
                "Tracking the growth of computer-generated imagery in cinema (1993–2026) "
                "and how audiences on Letterboxd responded to these films over time.",
                className="text-muted mb-4",
            ),
        ])),

        # Interactive timeline (TimelineJS)
        html.H4("Timeline: CGI in Film", className="mb-1"),
        html.Iframe(
            src=TIMELINE_EMBED_SRC,
            title="Timeline: CGI in Film",
            style={"width": "100%", "height": "650px", "border": "none"},
            allow="fullscreen",
            className="mb-4",
        ),

        # API setup down here
        dbc.Accordion([
            dbc.AccordionItem([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TMDB API Key"),
                        dbc.Input(
                            id="tmdb-key",
                            type="password",
                            placeholder="Optional -- only needed for TMDB-based CGI discovery",
                        ),
                    ], width=5),
                ], className="mb-3"),
                dbc.Button(
                    "Fetch CGI Movie Data", id="fetch-tmdb-btn",
                    color="primary", className="me-2",
                ),
                html.Span(id="fetch-tmdb-status", className="text-muted small align-middle"),
                html.P(
                    "Combines TMDB keyword-tagged CGI films with a manually curated list "
                    "(film_data/manual_movies.py) for titles TMDB misses, then looks up each "
                    "film's Letterboxd rating automatically -- no Letterboxd key needed.",
                    className="text-muted small mt-2 mb-0",
                ),
            ], title="API Configuration"),
        ], start_collapsed=False, className="mb-4"),

        # Static box office revenue trend -- sourced from a Statista export,
        html.H4("CGI & Animated Movie Box Office Revenue", className="mb-1"),
        html.P(
            "Box office revenue of CGI, 3D and animated movies in the United States, "
            "2008–2018 (Statista).",
            className="text-muted small mb-3",
        ),
        dcc.Graph(
            id="cgi-revenue-chart",
            figure=build_cgi_revenue_chart(),
            config={"displayModeBar": False},
            className="mb-4",
        ),

        # Google Trends
        html.H4("Public Search Interest in \"Computer-Generated Imagery\"", className="mb-1"),
        html.P(
            "Google Trends interest over time for the \"Computer-generated imagery\" "
            "topic (worldwide) -- Google's disambiguated entity for CGI, rather than "
            "a bare text search. Values are relative search interest, scaled 0-100 "
            "against the topic's peak popularity in the selected range.",
            className="text-muted small mb-3",
        ),
        dbc.Row([
            dbc.Col([
                dbc.Label("Date Range"),
                dcc.DatePickerRange(
                    id="trends-date-range",
                    min_date_allowed=date(2004, 1, 1),
                    max_date_allowed=date(2026, 1, 1),
                    start_date=date(2004, 1, 1),
                    end_date=date(2026, 1, 1),
                    display_format="YYYY-MM-DD",
                ),
            ], width="auto"),
        ], className="mb-3"),
        dcc.Loading(
            html.Iframe(
                id="google-trends-iframe",
                srcDoc=_google_trends_srcdoc(GOOGLE_TRENDS_START, GOOGLE_TRENDS_END),
                title="Google Trends: search interest for the 'Computer-generated imagery' topic",
                style={"width": "100%", "height": "420px", "border": "none"},
            ),
            type="circle",
        ),

        html.Hr(className="mt-4"),
        html.H4("CGI Prevalence in Cinema", className="mb-1"),
        html.P(
            "Movies identified via TMDB CGI-related keywords plus a manually curated "
            "list. Volume (left) indicates how many notable CGI films were released "
            "each year; average rating (right) is each year's Letterboxd rating, "
            "weighted by rating count, drawing on Letterboxd's much larger audience "
            "sample than TMDB alone.",
            className="text-muted small mb-3",
        ),

        dbc.Row([
            dbc.Col([
                html.H5("Notable CGI Films per Year", className="mb-2"),
                dcc.Loading(
                    dcc.Graph(
                        id="cgi-volume-chart",
                        config={"displayModeBar": False},
                    ),
                    type="circle",
                ),
            ], width=6),
            dbc.Col([
                html.H5("Average Letterboxd Rating of CGI Films", className="mb-2"),
                dcc.Loading(
                    dcc.Graph(
                        id="cgi-rating-chart",
                        config={"displayModeBar": False},
                    ),
                    type="circle",
                ),
            ], width=6),
        ], className="mb-3"),

        # Config settings for the CGI prevalence/rating charts above
        html.Div([
            html.H6("Chart Settings", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Filter by Release Year"),
                    dcc.RangeSlider(
                        id="cgi-year-slider",
                        min=1993, max=2026, step=1,
                        value=[1993, 2026],
                        marks={y: str(y) for y in range(1993, 2027, 5)},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ], width=6),
            ]),
        ], className="mb-5 p-3", style={"backgroundColor": "#f8f9fa", "borderRadius": "8px"}),

        # Rotten Tomatoes critical reception over time
        html.Hr(className="mt-4"),
        html.H4("Critical Reception Over Time", className="mb-1"),
        html.P(
            "Pick one or more films to see their % Fresh critic reviews "
            "(Rotten Tomatoes) by year.",
            className="text-muted small mb-3",
        ),
        dbc.Row([
            dbc.Col([
                dbc.Label("Films to Compare"),
                dcc.Dropdown(
                    id="rt-movie-select",
                    options=get_movie_options(),
                    multi=True,
                    placeholder="Search for a film by name",
                ),
                html.P(
                    f"Only films with reviews spanning multiple years are listed. "
                    f"Comparisons are capped at {MAX_SELECTED_FILMS} films.",
                    className="text-muted small mt-2 mb-0",
                ),
            ], width=8),
        ], className="mb-3"),
        dcc.Loading(
            dcc.Graph(
                id="rt-freshness-chart",
                config={"displayModeBar": False},
            ),
            type="circle",
        ),

        # Sentiment
        html.Hr(),
        html.H4("Audience Sentiment", className="mt-4 mb-1"),
        html.P(
            "Select detected notable CGI films from the list below after running the API, "
            "then fetch their TMDB member reviews. VADER sentiment scores range from "
            "−1 (very negative) to +1 (very positive). ",
            className="text-muted small mb-3",
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Films to Analyze"),
                dcc.Dropdown(
                    id="film-movie-select",
                    multi=True,
                    placeholder="Fetch TMDB data first, then select films here…",
                ),
            ], width=7),
            dbc.Col([
                dbc.Label("Filter by Release Year"),
                dcc.RangeSlider(
                    id="film-year-slider",
                    min=1993, max=2026, step=1,
                    value=[1993, 2026],
                    marks={y: str(y) for y in range(1993, 2027, 5)},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], width=5, className="align-self-end pb-2"),
        ], className="mb-3"),

        dbc.Row(dbc.Col([
            dbc.Button(
                "Fetch TMDB Reviews", id="fetch-sentiment-film-btn",
                color="secondary", className="me-3",
            ),
            html.Span(id="fetch-sentiment-film-status", className="text-muted small align-middle"),
        ])),

        dcc.Loading(
            dcc.Graph(
                id="film-sentiment-chart",
                className="mt-4",
                config={"displayModeBar": False},
            ),
            type="circle",
        ),

        dcc.Loading(
            dcc.Graph(
                id="film-stars-chart",
                className="mt-3",
                config={"displayModeBar": False},
            ),
            type="circle",
        ),

        # AI in Film
        html.Hr(className="mt-4"),
        html.H4("AI in Film: Audience Acceptance", className="mb-1"),
        html.P(
            "Consumer perception of the use of generative AI in film and TV "
            "production in the United States, by aspect of production "
            "(December 2025, Statista).",
            className="text-muted small mb-3",
        ),
        dcc.Graph(
            id="ai-acceptance-chart",
            figure=build_ai_acceptance_chart(),
            config={"displayModeBar": False},
            className="mb-4",
        ),

    ], fluid=True, className="page-container py-4")

# Callback section

def register_callbacks(app):

    @app.callback(
        Output("google-trends-iframe", "srcDoc"),
        Input("trends-date-range", "start_date"),
        Input("trends-date-range", "end_date"),
    )
    def update_trends_iframe(start_date, end_date):
        start_date = start_date or GOOGLE_TRENDS_START
        end_date = end_date or GOOGLE_TRENDS_END
        return _google_trends_srcdoc(start_date, end_date)

# Fetch TMDB CGI movie data
    @app.callback(
        Output("film-tmdb-store", "data"),
        Output("fetch-tmdb-status", "children"),
        Output("film-movie-select", "options"),
        Input("fetch-tmdb-btn", "n_clicks"),
        State("tmdb-key", "value"),
        prevent_initial_call=True,
    )

    def fetch_tmdb(_, api_key):
        df_tmdb = pd.DataFrame()
        if api_key:
            df_tmdb = fetch_cgi_movies(api_key)
        if not df_tmdb.empty:
            df_tmdb["source"] = "tmdb"

        df_manual = get_manual_movies_df()
        if not df_tmdb.empty:
            existing = set(zip(df_tmdb["title"].str.lower(), df_tmdb["year"]))
            df_manual = df_manual[
                ~df_manual.apply(lambda r: (r["title"].lower(), r["year"]) in existing, axis=1)
            ]

        df = pd.concat([df_tmdb, df_manual], ignore_index=True)
        if df.empty:
            return (
                None,
                "No data found. Check your TMDB API key, or add titles to "
                "film_data/manual_movies.py.",
                [],
            )

        n_found = len(df)
        df = fetch_letterboxd_ratings(df, max_films=MAX_LETTERBOXD_FILMS)
        n_capped = n_found - len(df)

        options = [
            {"label": f"{row['title']} ({int(row['year'])})", "value": row["title"]}
            for _, row in df.sort_values(["year", "title"]).iterrows()
        ]
        n_manual = int((df["source"] == "manual").sum())
        n_tmdb = len(df) - n_manual
        n_matched = int(df["lb_matched"].sum())
        msg = (
            f"Loaded {len(df)} CGI films ({n_tmdb} TMDB + {n_manual} manual) across "
            f"{df['year'].nunique()} years. Matched Letterboxd ratings for {n_matched}/{len(df)}."
        )
        if n_capped:
            msg += (
                f" Capped Letterboxd lookups at {MAX_LETTERBOXD_FILMS} "
                f"({n_capped} lower-priority TMDB titles skipped)."
            )
        return df.to_json(orient="records", date_format="iso"), msg, options

# Major CGI volume/use chart
    @app.callback(
        Output("cgi-volume-chart", "figure"),
        Output("cgi-rating-chart", "figure"),
        Input("film-tmdb-store", "data"),
        Input("cgi-year-slider", "value"),
    )
    def update_cgi_charts(json_data, year_range):
        waiting = _empty_fig("Please fetch CGI movie data first to see this chart")
        if not json_data:
            return waiting, waiting

        df = pd.read_json(StringIO(json_data), orient="records")
        df["year"] = df["year"].astype(int)

        if year_range:
            df = df[df["year"].between(year_range[0], year_range[1])]

        if df.empty:
            empty = _empty_fig("No films in the selected year range")
            return empty, empty

        def _year_stats(g: pd.DataFrame) -> pd.Series:
            matched = g[g["lb_matched"] == True]  # noqa: E712
            weights = matched["lb_rating_count"]
            if matched.empty or weights.sum() == 0:
                avg_rating = np.nan
            else:
                avg_rating = np.average(matched["lb_rating"], weights=weights)
            return pd.Series({"count": len(g), "avg_rating": avg_rating})

        by_year = df.groupby("year").apply(_year_stats).reset_index()

        # Volume bar chart
        fig_vol = go.Figure(go.Bar(
            x=by_year["year"],
            y=by_year["count"],
            marker_color="#3498db",
            hovertemplate="<b>%{x}</b><br>Films: %{y}<extra></extra>",
        ))
        fig_vol.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Year", dtick=3),
            yaxis=dict(title="Number of Films"),
            margin=dict(t=10, b=10),
        )

        # Average review score line chart
        fig_rat = go.Figure(go.Scatter(
            x=by_year["year"],
            y=by_year["avg_rating"].round(2),
            mode="lines+markers",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Avg Rating: %{y:.2f} / 5<extra></extra>",
        ))
        fig_rat.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Year", dtick=3),
            yaxis=dict(title="Avg Letterboxd Rating (0.5-5)", range=[0, 5]),
            margin=dict(t=10, b=10),
        )

        return fig_vol, fig_rat

# Rotten Tomatoes freshness-over-time chart
    @app.callback(
        Output("rt-freshness-chart", "figure"),
        Input("rt-movie-select", "value"),
    )
    def update_rt_freshness_chart(selected_links):
        return build_freshness_chart(selected_links or [])

#Fetch TMDB reviews
    @app.callback(
        Output("film-sentiment-store", "data"),
        Output("fetch-sentiment-film-status", "children"),
        Input("fetch-sentiment-film-btn", "n_clicks"),
        State("film-movie-select", "value"),
        State("film-tmdb-store", "data"),
        State("tmdb-key", "value"),
        prevent_initial_call=True,
    )
    def fetch_sentiment(_, selected_titles, tmdb_json, api_key):
        if not selected_titles:
            return None, "Please select at least one film first."
        if not api_key:
            return None, "Please enter your TMDB API key above."
        if not tmdb_json:
            return None, "Please fetch CGI movie data first."

        df_tmdb = pd.read_json(StringIO(tmdb_json), orient="records")
        pairs = []
        skipped = 0
        for title in selected_titles:
            row = df_tmdb[df_tmdb["title"] == title]
            if not row.empty and pd.notna(row.iloc[0]["id"]):
                pairs.append((title, int(row.iloc[0]["id"]), int(row.iloc[0]["year"])))
            else:
                skipped += 1

        if not pairs:
            return None, "None of the selected films have a TMDB ID (manual-only entries can't fetch reviews)."

        df = fetch_tmdb_reviews(api_key, pairs)
        if df.empty:
            return None, "No reviews found for the selected films."
        msg = f"Analyzed {len(df)} reviews across {df['title'].nunique()} film(s)."
        if skipped:
            msg += f" Skipped {skipped} film(s) with no TMDB ID."
        return df.to_json(orient="records", date_format="iso"), msg

    # Sentiment analysis charts
    @app.callback(
        Output("film-sentiment-chart", "figure"),
        Output("film-stars-chart", "figure"),
        Input("film-sentiment-store", "data"),
        Input("film-movie-select", "value"),
        Input("film-year-slider", "value"),
        Input("film-tmdb-store", "data"),
    )
    def update_sentiment_charts(sentiment_json, selected_titles, year_range, tmdb_json):
        waiting = _empty_fig("Please select films and fetch TMDB reviews to see this chart")
        if not sentiment_json:
            return waiting, waiting

        df = pd.read_json(StringIO(sentiment_json), orient="records")

        # Apply year filter using TMDB release year
        if tmdb_json and year_range:
            df_tmdb = pd.read_json(StringIO(tmdb_json), orient="records")
            in_range = df_tmdb[
                df_tmdb["year"].between(year_range[0], year_range[1])
            ]["title"].unique()
            df = df[df["title"].isin(in_range)]

        if selected_titles:
            df = df[df["title"].isin(selected_titles)]

        if df.empty:
            return (
                _empty_fig("No data for the current filters"),
                _empty_fig("No data for the current filters"),
            )

        # Aggregate per film
        agg = (
            df.groupby("title")
            .agg(
                avg_compound=("compound", "mean"),
                review_count=("compound", "count"),
                avg_tmdb_rating=("tmdb_rating", "mean"),
            )
            .reset_index()
            .sort_values("avg_compound")
        )

        agg["bar_color"] = agg["avg_compound"].apply(
            lambda s: "#27ae60" if s >= 0.05 else ("#e74c3c" if s <= -0.05 else "#f39c12")
        )
        agg["hover_text"] = agg.apply(
            lambda r: (
                f"Reviews: {r['review_count']}<br>"
                f"Avg TMDB rating: {r['avg_tmdb_rating']:.1f} / 10"
                if pd.notna(r["avg_tmdb_rating"])
                else f"Reviews: {r['review_count']}<br>Avg TMDB rating: N/A"
            ),
            axis=1,
        )

        # VADER sentiment bar chart
        fig_sent = go.Figure(go.Bar(
            x=agg["avg_compound"].round(3),
            y=agg["title"],
            orientation="h",
            marker_color=agg["bar_color"],
            hovertext=agg["hover_text"],
            hoverinfo="text+x",
            text=agg["avg_compound"].round(2),
            textposition="outside",
        ))
        fig_sent.add_vline(x=0, line_width=1, line_dash="dot", line_color="#777")
        fig_sent.update_layout(
            title="VADER Sentiment Score by Film",
            xaxis=dict(
                title="Avg VADER Compound Score  (−1 = Very Negative → +1 = Very Positive)",
                range=[-1, 1],
                zeroline=False,
            ),
            yaxis_title="",
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=70, t=40, b=40),
            height=max(300, len(agg) * 50),
        )

        # TMDB author rating bar chart
        agg_rated = agg[agg["avg_tmdb_rating"].notna()].sort_values("avg_tmdb_rating")
        if agg_rated.empty:
            fig_stars = _empty_fig("No numeric ratings attached to the fetched TMDB reviews")
        else:
            fig_stars = go.Figure(go.Bar(
                x=agg_rated["avg_tmdb_rating"].round(2),
                y=agg_rated["title"],
                orientation="h",
                marker_color="#9b59b6",
                hovertemplate="%{y}: %{x:.1f} / 10<extra></extra>",
                text=agg_rated["avg_tmdb_rating"].round(1),
                textposition="outside",
            ))
            fig_stars.update_layout(
                title="Average TMDB User Rating by Film",
                xaxis=dict(title="Avg Rating (out of 10)", range=[0, 11]),
                yaxis_title="",
                plot_bgcolor="#ffffff",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=70, t=40, b=40),
                height=max(300, len(agg_rated) * 50),
            )

        return fig_sent, fig_stars
    
# This block here is necessary to be able to run this file individually,
# without the app_tech_disruptions hub page.
# If you'd like to be able to run your files without needing the hub page,
# you can just copy and paste this block exactly how it is into your code.
if __name__ == "__main__":
    import os
    import dash

    # Point at the shared assets/ folder at the project root so standalone
    # runs still pick up the same CSS as the hub app.
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.LITERA],
        assets_folder=os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
    )
    app.layout = layout()
    register_callbacks(app)
    app.run(debug=True)
