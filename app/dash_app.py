import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import pandas as pd
from .models import SurveyResponse

def init_dashboard(server):
    dash_app = dash.Dash(__name__, server=server, url_base_pathname="/dashboard/",
                         suppress_callback_exceptions=True)

    dash_app.layout = html.Div([
        html.H2("PCOS Analytics Dashboard"),
        html.P("Interactive visualization for health survey metrics."),
        dcc.Dropdown(
            id="metric-select",
            options=[
                {"label": "Fatigue", "value": "fatigue"},
                {"label": "Mood Swings", "value": "mood_swings"},
                {"label": "Perceived Academic Stress", "value": "perceived_academic_stress"}
            ],
            value="fatigue"
        ),
        dcc.Graph(id="time-series"),
        html.Br(),
        html.A("Back to Home", href="/")
    ])

    @dash_app.callback(Output("time-series", "figure"), Input("metric-select", "value"))
    def update_time_series(metric):
        responses = SurveyResponse.query.all()

        if not responses:
            df = pd.DataFrame({"date": [], "value": []})
            fig = px.line(df, x="date", y="value", title="No Data Yet")
            return fig
        
        df = pd.DataFrame([{
            "date": r.date,
            "fatigue": r.fatigue,
            "mood_swings": r.mood_swings,
            "perceived_academic_stress": r.perceived_academic_stress
        } for r in responses])

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')
        # df = df.groupby("date").mean().reset_index()
        df.rename(columns={"date": "Date", metric: "Value"}, inplace=True)

        fig = px.line(df, x="Date", y="Value", title=f"{metric.replace('_', ' ').title()} Over Time")
        return fig

    return dash_app