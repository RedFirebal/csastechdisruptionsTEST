import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from pages.film import film
from pages.gaming import gaming
from pages.music import music
# We'll import the other pages here in the page directory when they're ready if you want.

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA],
    suppress_callback_exceptions=True,
)

server = app.server

# Register callbacks
film.register_callbacks(app)
gaming.register_callbacks(app)
music.register_callbacks(app)


# Home page
# We can change this stuff later if you want, it's just placeholders

def topic_section(industry, heading, description, href, bg_color, cta_label):
    return html.Div([
        html.Div(className="topic-section-bg", style={"backgroundColor": bg_color}),
        html.Div(className="topic-section-overlay"),
        html.Div([
            html.Span(industry, className="topic-section-eyebrow"),
            html.H2(heading, className="topic-section-heading"),
            html.P(description, className="topic-section-description"),
            dcc.Link(html.Div(cta_label, className="topic-section-btn"), href=href),
        ], className="topic-section-content"),
    ], className="topic-section")

hub_layout = html.Div([
    html.Div([
        html.Div([
            html.H1("Technological Disruptions", className="site-header-title"),
            
        ], className="site-header-inner"),
    ], id="site-header", className="site-header"),

    html.Button([
        html.Span(className="nav-toggle-bar"),
        html.Span(className="nav-toggle-bar"),
        html.Span(className="nav-toggle-bar"),
    ], id="nav-toggle-btn", className="nav-toggle-btn", n_clicks=0),

    html.Div([
        html.Div("Menu", className="nav-sidebar-title"),
        dcc.Link("Home", href="/app_tech_disruptions", className="nav-sidebar-link"),
        dcc.Link("Music", href="/music", className="nav-sidebar-link"),
        dcc.Link("Gaming", href="/gaming", className="nav-sidebar-link"),
        dcc.Link("Film", href="/film", className="nav-sidebar-link"),
    ], id="nav-sidebar", className="nav-sidebar"),

    html.Div([
        topic_section(
            "Music", "CD to Vinyl",
            "Comparing the Compact Disc to Vinyl using Sales Data and Sentiment Analysis",
            "/music", "#3a2e6b", "See Music Data",
        ),
        topic_section(
            "Gaming", "Player Perceptions of AI",
            "Sentiment analysis of real Reddit discussions on AI in game development.",
            "/gaming", "#1f5c4a", "Explore Gaming",
        ),
        topic_section(
            "Film", "The Evolution of CGI",
            "Discussing Trends and Recption of CGI as well as AI in Film",
            "/film", "#7a3b1a", "Explore Film",
        ),
    ], className="topic-sections"),

], id="hub-page", className="hub-container")

# Placeholder page for those that aren't done yet
def placeholder_page(title):
    return html.Div([
        html.H1(title),
        html.P("Nothing yet"),
        dcc.Link("← Back to Hub", href="/", className="back-link"),
    ], className="page-container")

music_layout = placeholder_page("Music Industry Disruptions")
gaming_layout = placeholder_page("Gaming Industry Disruptions")

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/music":
        return music.layout()
    if pathname == "/gaming":
        return gaming.layout()
    if pathname == "/film":
        return film.layout()
    return hub_layout


if __name__ == "__main__":
    app.run(debug=True)
