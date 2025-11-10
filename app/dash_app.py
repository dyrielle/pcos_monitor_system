import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .models import SurveyResponse

def init_dashboard(server):
    dash_app = dash.Dash(__name__, server=server, url_base_pathname="/dashboard/",
                         suppress_callback_exceptions=True)

    # Define the color palette matching the website theme
    NAVY = '#0B1D39'
    NAVY_600 = '#11294F'
    SILVER = '#D6D9DF'
    LIGHT_BG = '#F6F7FA'
    TEXT = '#1C1F26'
    MUTED = '#6B7280'
    PILL_BLUE = '#0d6efd'
    PILL_GREEN = '#198754'
    PILL_YELLOW = '#f6c744'
    PILL_RED = '#dc3545'

    dash_app.layout = html.Div([
        # Header Section
        html.Div([
            html.Div([
                html.H1("PCOS Analytics Dashboard", 
                       style={
                           'color': NAVY,
                           'marginBottom': '0.5rem',
                           'fontWeight': '700',
                           'fontSize': '2rem'
                       }),
                html.P("Interactive visualization for health survey metrics.",
                      style={
                          'color': MUTED,
                          'fontSize': '1.1rem',
                          'marginBottom': '0'
                      })
            ], style={
                'maxWidth': '1420px',
                'margin': '0 auto',
                'padding': '2rem 3rem'
            })
        ], style={
            'background': '#ffffff',
            'borderBottom': f'1px solid {SILVER}',
            'marginBottom': '2rem'
        }),

        # Main Content Container
        html.Div([
            # Metric Selection Card
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="bi bi-bar-chart-line-fill", 
                               style={'fontSize': '1.5rem', 'color': PILL_BLUE, 'marginRight': '0.75rem'}),
                        html.Strong("Select Health Metric", 
                                   style={'fontSize': '1.1rem', 'color': NAVY})
                    ], style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'marginBottom': '1rem'
                    }),
                    
                    dcc.Dropdown(
                        id="metric-select",
                        options=[
                            {"label": "📊 Fatigue", "value": "fatigue"},
                            {"label": "🎭 Mood Swings", "value": "mood_swings"},
                            {"label": "📚 Perceived Academic Stress", "value": "perceived_academic_stress"}
                        ],
                        value="fatigue",
                        style={
                            'borderRadius': '8px',
                            'border': f'1px solid {SILVER}',
                            'fontSize': '1rem'
                        }
                    )
                ], style={
                    'background': '#ffffff',
                    'padding': '1.5rem',
                    'borderRadius': '14px',
                    'border': f'1px solid #e5e7eb',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'marginBottom': '1.5rem'
                })
            ]),

            # Chart Card
            html.Div([
                dcc.Graph(
                    id="time-series",
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                    },
                    style={'height': '500px'}
                )
            ], style={
                'background': '#ffffff',
                'padding': '1.5rem',
                'borderRadius': '14px',
                'border': f'1px solid #e5e7eb',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                'marginBottom': '2rem'
            }),

            # Back Button
            html.Div([
                html.A([
                    html.I(className="bi bi-arrow-left", style={'marginRight': '0.5rem'}),
                    "Back to Home"
                ], 
                href="/",
                style={
                    'display': 'inline-block',
                    'padding': '0.6rem 1.2rem',
                    'background': NAVY,
                    'color': '#ffffff',
                    'borderRadius': '999px',
                    'textDecoration': 'none',
                    'fontWeight': '600',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                    'transition': 'all 0.3s ease'
                },
                className='back-btn')
            ], style={'textAlign': 'center'})

        ], style={
            'maxWidth': '1420px',
            'margin': '0 auto',
            'padding': '0 3rem 3rem'
        })

    ], style={
        'background': LIGHT_BG,
        'minHeight': '100vh',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    })

    @dash_app.callback(Output("time-series", "figure"), Input("metric-select", "value"))
    def update_time_series(metric):
        responses = SurveyResponse.query.all()

        if not responses:
            # Create empty figure with custom styling
            fig = go.Figure()
            fig.add_annotation(
                text="No data available yet. Submit your first survey response!",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color=MUTED)
            )
            fig.update_layout(
                title={
                    'text': "No Data Yet",
                    'font': {'size': 20, 'color': NAVY, 'family': 'inherit'},
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis={'visible': False},
                yaxis={'visible': False},
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=500
            )
            return fig
        
        df = pd.DataFrame([{
            "date": r.date,
            "fatigue": r.fatigue,
            "mood_swings": r.mood_swings,
            "perceived_academic_stress": r.perceived_academic_stress
        } for r in responses])

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')
        df.rename(columns={"date": "Date", metric: "Value"}, inplace=True)

        # Determine color based on metric
        metric_colors = {
            'fatigue': PILL_RED,
            'mood_swings': PILL_YELLOW,
            'perceived_academic_stress': PILL_BLUE
        }
        line_color = metric_colors.get(metric, PILL_BLUE)

        # Create enhanced line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Value'],
            mode='lines+markers',
            name=metric.replace('_', ' ').title(),
            line=dict(color=line_color, width=3),
            marker=dict(size=8, color=line_color, line=dict(color='white', width=2)),
            fill='tozeroy',
            fillcolor=f'rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.1)'
        ))

        fig.update_layout(
            title={
                'text': f"{metric.replace('_', ' ').title()} Over Time",
                'font': {'size': 22, 'color': NAVY, 'family': 'inherit'},
                'x': 0,
                'xanchor': 'left'
            },
            xaxis={
                'title': {
                    'text': 'Date',
                    'font': {'size': 14, 'color': TEXT}
                },
                'gridcolor': '#f0f0f0',
                'showgrid': True,
                'zeroline': False
            },
            yaxis={
                'title': {
                    'text': 'Value',
                    'font': {'size': 14, 'color': TEXT}
                },
                'gridcolor': '#f0f0f0',
                'showgrid': True,
                'zeroline': False
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor=NAVY,
                font_size=13,
                font_family='inherit'
            ),
            margin=dict(l=60, r=30, t=60, b=60),
            height=500
        )

        return fig

    # Add custom CSS for hover effects
    dash_app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
            <style>
                .back-btn:hover {
                    background-color: #11294F !important;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                }
                .Select-control {
                    border-radius: 8px !important;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''

    return dash_app