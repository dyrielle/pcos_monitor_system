import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from flask_login import current_user
from .models import SurveyResponse, StudentProfile

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
                html.H1(id="dashboard-title", 
                       style={
                           'color': NAVY,
                           'marginBottom': '0.5rem',
                           'fontWeight': '700',
                           'fontSize': '2rem'
                       }),
                html.P(id="dashboard-subtitle",
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
            # Stats Cards Row (for regular users)
            html.Div(id='stats-cards', style={'marginBottom': '1.5rem'}),
            
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

    # Callback to update title based on user type
    @dash_app.callback(
        [Output("dashboard-title", "children"),
         Output("dashboard-subtitle", "children")],
        Input("metric-select", "value")
    )
    def update_header(metric):
        if current_user.is_authenticated and not current_user.is_admin:
            title = "My Health Dashboard"
            subtitle = "Track your personal health metrics and progress over time."
        else:
            title = "PCOS Analytics Dashboard"
            subtitle = "Interactive visualization for health survey metrics."
        return title, subtitle

    # Callback to show stats cards for regular users
    @dash_app.callback(
        Output("stats-cards", "children"),
        Input("metric-select", "value")
    )
    def update_stats_cards(metric):
        if not current_user.is_authenticated or current_user.is_admin:
            return html.Div()  # No stats cards for admin
        
        profile = current_user.profile
        if not profile:
            return html.Div()
        
        responses = SurveyResponse.query.filter_by(profile_id=profile.id).all()
        
        if not responses:
            return html.Div([
                html.Div([
                    html.I(className="bi bi-info-circle", style={'fontSize': '3rem', 'color': MUTED}),
                    html.P("No data yet. Submit your first health entry to see your statistics!", 
                           style={'marginTop': '1rem', 'color': MUTED, 'fontSize': '1.1rem'})
                ], style={
                    'background': '#ffffff',
                    'padding': '3rem',
                    'borderRadius': '14px',
                    'border': f'1px solid #e5e7eb',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'textAlign': 'center'
                })
            ])
        
        # Calculate averages
        df = pd.DataFrame([{
            "fatigue": r.fatigue,
            "mood_swings": r.mood_swings,
            "perceived_academic_stress": r.perceived_academic_stress,
            "sleep_quality": r.sleep_quality
        } for r in responses])
        
        avg_fatigue = df['fatigue'].mean() if not df['fatigue'].isna().all() else 0
        avg_mood = df['mood_swings'].mean() if not df['mood_swings'].isna().all() else 0
        avg_stress = df['perceived_academic_stress'].mean() if not df['perceived_academic_stress'].isna().all() else 0
        avg_sleep = df['sleep_quality'].mean() if not df['sleep_quality'].isna().all() else 0
        total_entries = len(responses)
        
        # Get latest entry date
        latest_date = max([r.date for r in responses]).strftime("%B %d, %Y") if responses else "N/A"
        
        return html.Div([
            html.Div([
                # Stat Card 1
                html.Div([
                    html.Div([
                        html.I(className="bi bi-battery-charging", 
                               style={'fontSize': '2.5rem', 'color': PILL_RED, 'marginBottom': '0.5rem'}),
                        html.H6("Avg Fatigue", style={'color': MUTED, 'marginBottom': '0.5rem', 'fontSize': '0.9rem'}),
                        html.H3(f"{avg_fatigue:.1f}", style={'color': NAVY, 'margin': '0', 'fontWeight': '700'}),
                        html.Small("out of 5", style={'color': MUTED})
                    ], style={'textAlign': 'center', 'padding': '1.5rem'})
                ], style={
                    'background': '#ffffff',
                    'borderRadius': '12px',
                    'border': f'2px solid {PILL_RED}',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                    'flex': '1'
                }),
                
                # Stat Card 2
                html.Div([
                    html.Div([
                        html.I(className="bi bi-emoji-smile", 
                               style={'fontSize': '2.5rem', 'color': PILL_YELLOW, 'marginBottom': '0.5rem'}),
                        html.H6("Avg Mood", style={'color': MUTED, 'marginBottom': '0.5rem', 'fontSize': '0.9rem'}),
                        html.H3(f"{avg_mood:.1f}", style={'color': NAVY, 'margin': '0', 'fontWeight': '700'}),
                        html.Small("out of 5", style={'color': MUTED})
                    ], style={'textAlign': 'center', 'padding': '1.5rem'})
                ], style={
                    'background': '#ffffff',
                    'borderRadius': '12px',
                    'border': f'2px solid {PILL_YELLOW}',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                    'flex': '1'
                }),
                
                # Stat Card 3
                html.Div([
                    html.Div([
                        html.I(className="bi bi-book", 
                               style={'fontSize': '2.5rem', 'color': PILL_BLUE, 'marginBottom': '0.5rem'}),
                        html.H6("Avg Stress", style={'color': MUTED, 'marginBottom': '0.5rem', 'fontSize': '0.9rem'}),
                        html.H3(f"{avg_stress:.1f}", style={'color': NAVY, 'margin': '0', 'fontWeight': '700'}),
                        html.Small("out of 5", style={'color': MUTED})
                    ], style={'textAlign': 'center', 'padding': '1.5rem'})
                ], style={
                    'background': '#ffffff',
                    'borderRadius': '12px',
                    'border': f'2px solid {PILL_BLUE}',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                    'flex': '1'
                }),
                
                # Stat Card 4
                html.Div([
                    html.Div([
                        html.I(className="bi bi-moon-stars", 
                               style={'fontSize': '2.5rem', 'color': PILL_GREEN, 'marginBottom': '0.5rem'}),
                        html.H6("Avg Sleep", style={'color': MUTED, 'marginBottom': '0.5rem', 'fontSize': '0.9rem'}),
                        html.H3(f"{avg_sleep:.1f}", style={'color': NAVY, 'margin': '0', 'fontWeight': '700'}),
                        html.Small("out of 5", style={'color': MUTED})
                    ], style={'textAlign': 'center', 'padding': '1.5rem'})
                ], style={
                    'background': '#ffffff',
                    'borderRadius': '12px',
                    'border': f'2px solid {PILL_GREEN}',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                    'flex': '1'
                }),
                
                # Stat Card 5
                html.Div([
                    html.Div([
                        html.I(className="bi bi-calendar-check", 
                               style={'fontSize': '2.5rem', 'color': '#8b5cf6', 'marginBottom': '0.5rem'}),
                        html.H6("Total Entries", style={'color': MUTED, 'marginBottom': '0.5rem', 'fontSize': '0.9rem'}),
                        html.H3(f"{total_entries}", style={'color': NAVY, 'margin': '0', 'fontWeight': '700'}),
                        html.Small(f"Latest: {latest_date}", style={'color': MUTED, 'fontSize': '0.75rem'})
                    ], style={'textAlign': 'center', 'padding': '1.5rem'})
                ], style={
                    'background': '#ffffff',
                    'borderRadius': '12px',
                    'border': '2px solid #8b5cf6',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                    'flex': '1'
                })
                
            ], style={
                'display': 'flex',
                'gap': '1rem',
                'flexWrap': 'wrap'
            })
        ])

    @dash_app.callback(Output("time-series", "figure"), Input("metric-select", "value"))
    def update_time_series(metric):
        # Filter data based on user type
        if current_user.is_authenticated and not current_user.is_admin:
            # Regular user: show only their data
            profile = current_user.profile
            if profile:
                responses = SurveyResponse.query.filter_by(profile_id=profile.id).all()
            else:
                responses = []
        else:
            # Admin or anonymous: show all data
            responses = SurveyResponse.query.all()

        if not responses:
            # Create empty figure with custom styling
            is_regular_user = current_user.is_authenticated and not current_user.is_admin
            empty_message = "No data available yet. Submit your first health entry!" if is_regular_user else "No data available yet. Submit your first survey response!"
            
            fig = go.Figure()
            fig.add_annotation(
                text=empty_message,
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

        # Determine if user is regular user or admin
        is_regular_user = current_user.is_authenticated and not current_user.is_admin
        chart_title_prefix = "Your " if is_regular_user else ""

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
                'text': f"{chart_title_prefix}{metric.replace('_', ' ').title()} Over Time",
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