
# Install Dash and Dash Bootstrap Components
import os
from pathlib import Path
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from PIL import Image

# This import should work wherever music.py is run (by itself
# or from app_tech_disruptions.py)
DATA_DIR = Path(__file__).resolve().parent / "music_assets"

# set up dataframes

CD_YearlyCount = pd.read_csv(DATA_DIR / "CD_yearlycount.csv")
CD_YearlySent = pd.read_csv(DATA_DIR / "CD_yearlysent.csv")
LP_YearlyCount = pd.read_csv(DATA_DIR / "LP_yearlycount.csv")
LP_YearlySent = pd.read_csv(DATA_DIR / "LP_yearlysent.csv")
df = pd.read_csv(DATA_DIR / "musicdata.csv")
pil_image = Image.open(DATA_DIR / "source_qr.png")

# Set up subframes for sales

cdFrame = df[(df['format'].isin(['CD', 'CD Single', 'SACD'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
vyFrame = df[(df['format'].isin(['LP/EP', 'Vinyl Single'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
dgFrame = df[(df['format'].isin(['Download Album', 'Other Digital', 'Download Music Video', 'Download Single', 'Ringtones & Ringbacks'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
stFrame = df[(df['format'].isin(['Limited Tier Paid Subscription', 'On-Demand Streaming (Ad-Supported)', 'Other Ad-Supported Streaming', 'Paid Subscription', 'Paid Subscriptions'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
cassFrame = df[(df['format'].isin(['8 - Track', 'Cassette', 'Cassette Single', 'Other Tapes'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
dvdFrame = df[(df['format'].isin(['DVD Audio', 'Music Video (Physical)'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()

# Set up all initial figures

sentcomp_fig = go.Figure(data=[go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines+markers', name='CD'),
                             go.Scatter(x=LP_YearlySent['year'], y=LP_YearlySent['sentiment_score'], mode='lines+markers', name='Vinyl')])
sentcomp_fig.update_layout(title='CD vs Vinyl Sentiment Score (1982-2019)',
                         xaxis_title='Year',
                         yaxis_title='Sentiment Score')


cd_vinyl_sales_fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], mode='lines+markers', name='CD'),
                              go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], mode='lines+markers', name='Vinyl')])
cd_vinyl_sales_fig.update_layout(title='CD Sales vs Vinyl Sales (1973-2019)',
                          xaxis_title='Year',
                          yaxis_title='Estimated Sales (In Billions)')


cd_article_count_fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='CD')])
cd_article_count_fig.update_layout(title='CD Article Count (NYT 1982-2019)',
                          xaxis_title='Year',
                          yaxis_title='Article Count')


cd_sent_fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='Article Count', marker_color='royalblue', opacity=0.8, yaxis='y'),
                              go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines+markers', name='Sentiment Score', marker_color='black', yaxis='y2')])
cd_sent_fig.update_layout(title='CD Article Count vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Article Count'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))


cd_sales_sent_fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], name='Estimated Sales (In Billions)', marker_color='royalblue', opacity=0.8, yaxis='y'),
                              go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines+markers', name='Sentiment Score', marker_color='black', yaxis='y2')])
cd_sales_sent_fig.update_layout(title='CD Sales vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Article Count'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))

def layout():
    return dbc.Container(
        [
            dbc.Row(dbc.Col(
                dcc.Link("← Back to Hub", href="/", className="back-link")
            )),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Music Data (The Compact Disc)", className="card-title"),
                    html.P("This page displays data about the compact disc, viewing it as a technological disruption.", className="card-text"),
                    html.P("The compact disc (shortened as CD), is described in Pohlman, 1992 as 'one of the most successful new electronic products ever introduced.' It was created under a rare collaborative effort by Philips and Sony and released worldwide in 1982. It is directly resposible for the downfall of competing analog music formats and the rise of digital music in earnest.", className="card-text")
                ])
            ], className="mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H4("About the Data", className="card-title"),
                    html.P(
                        "The data used in this page was pulled from the New York Times API and from Kaggle. The NYT API was used to pull articles about CDs and vinyls, which were then analyzed for sentiment. The NYT API is pulled from 1982 to 2019. This is due to the fact that the CD did not release worldwide untill 1982 and so pulling additional data for one technology and not the other didn't seem very reasonable. " \
                        "The Kaggle dataset, posted by user Larxel (andrewmvd), was used for sales data. The dataset contains sales data for various music formats, including CDs, vinyls, digital downloads, streaming, cassettes, and DVDs. The data spans from 1973 to 2019 and includes estimated sales values in billions of dollars.",
                        className="card-text",
                    ),
                ])
            ], className="mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Sales Data", className="card-title"),
                    html.P("One of the easiest indicators to understanding the effect a new technology has on any landscape is sales data. Using the following charts below it is evident that the compact disc did have a major amount of influence in the space."),
                    html.Br(),
                    html.Button('Switch Graph Complexity', id='btn-switch1', n_clicks=0),
                    dcc.Store(id='graph-state1', data=True),
                    dcc.Graph(id='display-graph1', figure=cd_vinyl_sales_fig)

                ])
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Br())
            ]),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Sentiment Analysis", className="card-title"),
                    html.P("By using sentiment analysis, we can roughly determine the level of positive or negative reception in a given source. By pulling articles fron the New York Times using its dedicated API, we can judge the relative feelings on a certain topic for a particular year."),
                    dcc.Graph(figure=sentcomp_fig)
                ])
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Br())
            ]),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Article Count", className="card-title"),
                    html.P("By seeing the number of articles of a given topic, we can judge how big said topic is that year. Since each page of an API pull is, at most, ten articles, a cap of 100 articles per year is a solid cut off to determine how covered the topic is just in the NYT alone."),
                    html.Button('Switch Graph', id='btn-switch2', n_clicks=0),
                    dcc.Store(id='graph-state2', data=True),
                    dcc.Graph(id='display-graph2', figure=cd_article_count_fig)
                ])
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Br())
            ]),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Article Count vs Sentiment Score", className="card-title"),
                    html.P("Using comparison frames, we can see if there is any correlation between two bits of data. In these charts, we determine if there is anything to be gleamed from article count and sentiment score. Oddly enough the charts seem to show a negative correlation in CDs (The more articles, the less the sentiment score) and a positive one for vinyls (The more articles, the higher the sentiment score)."),
                    html.Button('Switch Graph', id='btn-switch3', n_clicks=0),
                    dcc.Store(id='graph-state3', data=True),
                    dcc.Graph(id='display-graph3', figure=cd_sent_fig)
                ])
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Br())
            ]),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Sales vs Sentiment Score", className="card-title"),
                    html.P("Using comparison frames, we can see if there is any correlation between two bits of data. In these charts, we determine if there is anything to be gleamed from sales and sentiment score. For CDs, there seems to be a slight positive correlation, signified by the center of the graph following a similar trend but not the rest. For vinyl, there appears to be little to no correlation."),
                    html.Button('Switch Graph', id='btn-switch4', n_clicks=0),
                    dcc.Store(id='graph-state4', data=True),
                    dcc.Graph(id='display-graph4', figure=cd_sales_sent_fig)
                ])
            ], className="mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Conclusion", className="card-title"),
                    html.P(
                        "Using the information shown in the data, there are some general findings. According to both our scholarship and the concept of creative destruction, the compact disc does follow trends of about what we expect of a technological disruption. It quickly rose in prominance, massively reduced the sales and relevance of competing mediums, then fell off itself as newer and more advanced technologies were released. Despite this, an unexpected change occured with the slow revival of vinyl as a relevant music medium. The vinyl revival opperates inverse to what we expect of creative destruction and may suggest a few things ranging from a want to return to 'simpler times' through entertainment, a genuine belief in superiority of particular technologies even if they may seem technologically inferior, or a craving for physicality in a world that is increasingly digital.",
                        className="card-text",
                    ),
                ])
            ], className="mb-3"),
            dbc.Card([
                dbc.CardBody([  
                    html.H4("Sources", className="card-title"),
                    html.Img(src=pil_image, style={'width': '150px', 'height': '150px'})
        ])
            ], className="mb-3"),
        ],
    )

# Callback section

def register_callbacks(app):

    # GRAPH SWITCHING BUTTON 1
    # Callback to update state and graph upon clicking
    @app.callback(
        [Output('display-graph1', 'figure'),
         Output('graph-state1', 'data')],
        [Input('btn-switch1', 'n_clicks')],
        [State('graph-state1', 'data')]
    )
    def switch_graph1(n_clicks, current_state):
        # Default to Graph 1 if button hasn't been clicked or state is True
        if n_clicks == 0 or current_state:
            # Generate Graph 1
            fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], mode='lines+markers', name='CD'),
                                  go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], mode='lines+markers', name='Vinyl')])
            fig.update_layout(title='CD Sales vs Vinyl Sales (1973-2019)',
                              xaxis_title='Year',
                              yaxis_title='Estimated Sales (In Billions)', transition_duration=500)
            new_state = False # Next click will show Graph 2
        else:
            # Generate Graph 2
            fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], mode='lines+markers', name='CD'),
                                  go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], mode='lines+markers', name='Vinyl'),
                                  go.Scatter(x=dgFrame['year'], y=dgFrame['value_actual'], mode= 'lines+markers', name='Digital'),
                                  go.Scatter(x=stFrame['year'], y=stFrame['value_actual'], mode= 'lines+markers', name='Streaming'),
                                  go.Scatter(x=cassFrame['year'], y=cassFrame['value_actual'], mode= 'lines+markers', name='Cassette'),
                                  go.Scatter(x=dvdFrame['year'], y=dvdFrame['value_actual'], mode= 'lines+markers', name='DVD'),])
            fig.update_layout(title= 'Music Medium Sales (1973-2019)',
                              xaxis_title='Year',
                              yaxis_title='Estimated Sales (In Billions)', transition_duration=500)
            new_state = True  # Next click will show Graph 1

        return fig, new_state

    # GRAPH SWITCHING BUTTON 2
    # Callback to update state and graph upon clicking
    @app.callback(
        [Output('display-graph2', 'figure'),
         Output('graph-state2', 'data')],
        [Input('btn-switch2', 'n_clicks')],
        [State('graph-state2', 'data')]
    )
    def switch_graph2(n_clicks, current_state):
        # Default to Graph 1 if button hasn't been clicked or state is True
        if n_clicks == 0 or current_state:
            # Generate Graph 1
            fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='CD')])
            fig.update_layout(title='CD Article Count (NYT 1982-2019)',
                              xaxis_title='Year',
                              yaxis_title='Article Count', transition_duration=500)
            new_state = False # Next click will show Graph 2
        else:
            # Generate Graph 2
            fig = go.Figure(data=[go.Bar(x=LP_YearlyCount['year'], y=LP_YearlyCount['count'], name='Vinyl', marker_color='red')])
            fig.update_layout(title= 'Vinyl Article Count (NYT 1982-2019)',
                              xaxis_title='Year',
                              yaxis_title='Article Count', transition_duration=500)
            new_state = True  # Next click will show Graph 1

        return fig, new_state

    # GRAPH SWITCHING BUTTON 3
    # Callback to update state and graph upon clicking
    @app.callback(
        [Output('display-graph3', 'figure'),
         Output('graph-state3', 'data')],
        [Input('btn-switch3', 'n_clicks')],
        [State('graph-state3', 'data')]
    )
    def switch_graph3(n_clicks, current_state):
        # Default to Graph 1 if button hasn't been clicked or state is True
        if n_clicks == 0 or current_state:
            # Generate Graph 1
            fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='Article Count', marker_color='royalblue', opacity=0.8, yaxis='y'),
                                  go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines+markers', name='Sentiment Score', marker_color='black', yaxis='y2')])
            fig.update_layout(title='CD Article Count vs Sentiment Score (1973-2019)',
                              xaxis_title='Year',
                              yaxis=dict(title='Article Count'),
                              yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                              legend=dict(x=1.1, y=1), transition_duration=500)
            new_state = False # Next click will show Graph 2
        else:
            # Generate Graph 2
            fig = go.Figure(data=[go.Bar(x=LP_YearlyCount['year'], y=LP_YearlyCount['count'], name='Article Count', marker_color='red', opacity=0.8, yaxis='y'),
                                  go.Scatter(x=LP_YearlySent['year'], y=LP_YearlySent['sentiment_score'], mode='lines+markers', name='Sentiment Score', marker_color='black', yaxis='y2')])
            fig.update_layout(title='Vinyl Article Count vs Sentiment Score (1973-2019)',
                              xaxis_title='Year',
                              yaxis=dict(title='Article Count'),
                              yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                              legend=dict(x=1.1, y=1), transition_duration=500)
            new_state = True  # Next click will show Graph 1

        return fig, new_state

    # GRAPH SWITCHING BUTTON 4
    # Callback to update state and graph upon clicking
    @app.callback(
        [Output('display-graph4', 'figure'),
         Output('graph-state4', 'data')],
        [Input('btn-switch4', 'n_clicks')],
        [State('graph-state4', 'data')]
    )
    def switch_graph4(n_clicks, current_state):
        # Default to Graph 1 if button hasn't been clicked or state is True
        if n_clicks == 0 or current_state:
            # Generate Graph 1
            fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], name='Estimated Sales (In Billions)', marker_color='royalblue', opacity=0.8, yaxis='y'),
                                  go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines+markers', name='Sentiment Score', marker_color='black', yaxis='y2')])
            fig.update_layout(title='CD Sales vs Sentiment Score (1973-2019)',
                              xaxis_title='Year',
                              yaxis=dict(title='Estimated Sales (in Billions)'),
                              yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                              legend=dict(x=1.1, y=1),
                              transition_duration=500)
            new_state = False # Next click will show Graph 2
        else:
            # Generate Graph 2
            fig = go.Figure(data=[go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], name='Estimated Sales (In Billions)', marker_color='red', opacity=0.8, yaxis='y'),
                                  go.Scatter(x=LP_YearlySent['year'], y=LP_YearlySent['sentiment_score'], mode='lines+markers', name='Sentiment Score', marker_color='black', yaxis='y2')])
            fig.update_layout(title='Vinyl Sales vs Sentiment Score (1973-2019)',
                              xaxis_title='Year',
                              yaxis=dict(title='Estimated Sales (in Billions)'),
                              yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                              legend=dict(x=1.1, y=1),
                              transition_duration=500)
            new_state = True  # Next click will show Graph 1

        return fig, new_state

# This block here is necessary to be able to run this file individually,
# without the app_tech_disruptions hub page.
# If you'd like to be able to run your files without needing the hub page,
# you can just copy and paste this block exactly how it is into your code.
if __name__ == "__main__":
    import dash

    # Point at the shared assets/ folder at the project root so standalone
    # runs still pick up the same CSS as the hub app.
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.MINTY],
        assets_folder=os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
    )
    app.layout = layout()
    register_callbacks(app)
    app.run(debug=True)
