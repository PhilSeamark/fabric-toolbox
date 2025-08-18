"""
Dash-Only Chart Generator for Semantic Model MCP Server
Generates all visualizations using Dash and Plotly only
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import threading
import time
import webbrowser
import socket
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashChartGenerator:
    """Generate all charts using Dash and Plotly only"""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize chart generator with output directory"""
        self.output_dir = output_dir
        self.ensure_output_dir()
        self.running_charts = {}
        self.port_range_start = 8050
        self.port_range_end = 8100
        
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def find_available_port(self) -> int:
        """Find an available port for a new chart dashboard"""
        for port in range(self.port_range_start, self.port_range_end):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', port))
                sock.close()
                return port
            except OSError:
                continue
        raise RuntimeError("No available ports found in range")
    
    def process_dax_results(self, results: Dict) -> pd.DataFrame:
        """Convert DAX query results to pandas DataFrame"""
        if isinstance(results, dict):
            if not results.get('success', False):
                raise ValueError(f"DAX query failed: {results.get('error', 'Unknown error')}")
            
            # Extract data from results
            rows = results.get('rows', [])
            columns = results.get('columns', [])
            
            if not rows or not columns:
                raise ValueError("No data returned from DAX query")
            
            # Handle different data formats
            if isinstance(rows[0], dict):
                # Data is already in dict format
                df = pd.DataFrame(rows)
            else:
                # Data needs to be converted from column format
                data = []
                for row in rows:
                    row_data = {}
                    for i, col in enumerate(columns):
                        col_name = col['name'] if isinstance(col, dict) else col
                        col_name = col_name.split('[')[-1].rstrip(']')  # Clean column names
                        row_data[col_name] = row[i] if isinstance(row, list) else row.get(col_name)
                    data.append(row_data)
                df = pd.DataFrame(data)
        else:
            # Assume it's already a DataFrame or list of dicts
            df = pd.DataFrame(results)
        
        # Auto-detect and convert data types
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
                
                # Try to convert to datetime
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_datetime(df[col], errors='ignore')
                    except:
                        pass
        
        return df
    
    def create_bar_chart_dashboard(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                 title: str = "Bar Chart", chart_id: str = None,
                                 auto_open: bool = True) -> Dict[str, Any]:
        """Create an interactive bar chart dashboard using Dash"""
        
        if chart_id is None:
            chart_id = f"bar_chart_{x_col}_{y_col}_{int(time.time())}"
        
        port = self.find_available_port()
        
        # Create Dash app
        app = dash.Dash(__name__, url_base_pathname=f"/{chart_id}/")
        
        # Create bar chart
        fig = px.bar(df, x=x_col, y=y_col, title=title,
                     labels={x_col: x_col.title(), y_col: y_col.title()},
                     color=y_col, color_continuous_scale='viridis')
        
        fig.update_layout(
            title_font_size=20,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            showlegend=False,
            height=600,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Layout
        app.layout = html.Div([
            html.H1(title, style={'textAlign': 'center', 'marginBottom': 30}),
            
            html.Div([
                html.Label("Chart Type:", style={'fontWeight': 'bold', 'marginRight': 10}),
                dcc.Dropdown(
                    id='chart-type',
                    options=[
                        {'label': 'Bar Chart', 'value': 'bar'},
                        {'label': 'Line Chart', 'value': 'line'},
                        {'label': 'Scatter Plot', 'value': 'scatter'},
                        {'label': 'Pie Chart', 'value': 'pie'}
                    ],
                    value='bar',
                    style={'width': '200px', 'display': 'inline-block'}
                )
            ], style={'marginBottom': 20, 'textAlign': 'center'}),
            
            dcc.Graph(id='main-chart', figure=fig),
            
            html.Hr(),
            
            html.Div([
                html.H3("Data Summary", style={'textAlign': 'center'}),
                html.Div(id='data-summary')
            ], style={'marginTop': 30})
        ], style={'padding': 20})
        
        # Callbacks
        @app.callback(
            Output('main-chart', 'figure'),
            Input('chart-type', 'value')
        )
        def update_chart(chart_type):
            if chart_type == 'bar':
                return px.bar(df, x=x_col, y=y_col, title=title, color=y_col)
            elif chart_type == 'line':
                return px.line(df, x=x_col, y=y_col, title=title, markers=True)
            elif chart_type == 'scatter':
                return px.scatter(df, x=x_col, y=y_col, title=title, size=y_col)
            elif chart_type == 'pie':
                return px.pie(df, values=y_col, names=x_col, title=title)
            return px.bar(df, x=x_col, y=y_col, title=title)
        
        @app.callback(
            Output('data-summary', 'children'),
            Input('chart-type', 'value')
        )
        def update_summary(chart_type):
            total = df[y_col].sum()
            avg = df[y_col].mean()
            max_val = df[y_col].max()
            min_val = df[y_col].min()
            
            return html.Div([
                html.P(f"Total {y_col}: {total:,.2f}"),
                html.P(f"Average {y_col}: {avg:,.2f}"),
                html.P(f"Maximum {y_col}: {max_val:,.2f}"),
                html.P(f"Minimum {y_col}: {min_val:,.2f}"),
                html.P(f"Number of {x_col} categories: {len(df)}")
            ], style={'textAlign': 'center'})
        
        # Start server in background thread
        def run_server():
            app.run(host='localhost', port=port, debug=False)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Store chart info
        url = f"http://localhost:{port}/{chart_id}/"
        self.running_charts[chart_id] = {
            'app': app,
            'thread': thread,
            'port': port,
            'url': url,
            'type': 'bar_chart',
            'created_at': datetime.now(),
            'title': title
        }
        
        # Auto-open browser
        if auto_open:
            webbrowser.open(url)
        
        return {
            'success': True,
            'chart_id': chart_id,
            'url': url,
            'port': port,
            'type': 'bar_chart',
            'message': f"Bar chart dashboard launched at {url}"
        }
    
    def create_line_chart_dashboard(self, df: pd.DataFrame, x_col: str, y_col: str, 
                                  title: str = "Line Chart", chart_id: str = None,
                                  auto_open: bool = True) -> Dict[str, Any]:
        """Create an interactive line chart dashboard using Dash"""
        
        if chart_id is None:
            chart_id = f"line_chart_{x_col}_{y_col}_{int(time.time())}"
        
        port = self.find_available_port()
        
        # Create Dash app
        app = dash.Dash(__name__, url_base_pathname=f"/{chart_id}/")
        
        # Create line chart
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True,
                      labels={x_col: x_col.title(), y_col: y_col.title()})
        
        fig.update_layout(
            title_font_size=20,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            height=600,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Layout with trend analysis
        app.layout = html.Div([
            html.H1(title, style={'textAlign': 'center', 'marginBottom': 30}),
            
            html.Div([
                html.Label("Show Trend Line:", style={'fontWeight': 'bold', 'marginRight': 10}),
                dcc.Checklist(
                    id='trend-line',
                    options=[{'label': 'Linear Trend', 'value': 'linear'}],
                    value=[],
                    inline=True
                )
            ], style={'marginBottom': 20, 'textAlign': 'center'}),
            
            dcc.Graph(id='main-chart', figure=fig),
            
            html.Hr(),
            
            html.Div([
                html.H3("Trend Analysis", style={'textAlign': 'center'}),
                html.Div(id='trend-analysis')
            ], style={'marginTop': 30})
        ], style={'padding': 20})
        
        # Callbacks
        @app.callback(
            [Output('main-chart', 'figure'), Output('trend-analysis', 'children')],
            Input('trend-line', 'value')
        )
        def update_chart(show_trend):
            fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
            
            if 'linear' in show_trend:
                # Add trend line
                fig = px.scatter(df, x=x_col, y=y_col, title=title, trendline="ols")
            
            fig.update_layout(
                title_font_size=20,
                xaxis_title_font_size=14,
                yaxis_title_font_size=14,
                height=600
            )
            
            # Calculate trend analysis
            if len(df) > 1:
                trend_direction = "↗️ Increasing" if df[y_col].iloc[-1] > df[y_col].iloc[0] else "↘️ Decreasing"
                volatility = df[y_col].std()
                
                analysis = html.Div([
                    html.P(f"Overall Trend: {trend_direction}"),
                    html.P(f"Volatility (Std Dev): {volatility:,.2f}"),
                    html.P(f"Data Points: {len(df)}")
                ], style={'textAlign': 'center'})
            else:
                analysis = html.P("Insufficient data for trend analysis")
            
            return fig, analysis
        
        # Start server
        def run_server():
            app.run(host='localhost', port=port, debug=False)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(2)
        
        url = f"http://localhost:{port}/{chart_id}/"
        self.running_charts[chart_id] = {
            'app': app,
            'thread': thread,
            'port': port,
            'url': url,
            'type': 'line_chart',
            'created_at': datetime.now(),
            'title': title
        }
        
        if auto_open:
            webbrowser.open(url)
        
        return {
            'success': True,
            'chart_id': chart_id,
            'url': url,
            'port': port,
            'type': 'line_chart',
            'message': f"Line chart dashboard launched at {url}"
        }
    
    def create_comprehensive_dashboard(self, df: pd.DataFrame, title: str = "Data Analysis Dashboard",
                                     chart_id: str = None, auto_open: bool = True) -> Dict[str, Any]:
        """Create a comprehensive multi-chart dashboard"""
        
        if chart_id is None:
            chart_id = f"comprehensive_{int(time.time())}"
        
        port = self.find_available_port()
        
        # Create Dash app
        app = dash.Dash(__name__, url_base_pathname=f"/{chart_id}/")
        
        # Analyze columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Layout
        app.layout = html.Div([
            html.H1(title, style={'textAlign': 'center', 'marginBottom': 30}),
            
            # Controls
            html.Div([
                html.Div([
                    html.Label("X-Axis:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='x-column',
                        options=[{'label': col, 'value': col} for col in df.columns],
                        value=df.columns[0] if len(df.columns) > 0 else None
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Y-Axis:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='y-column',
                        options=[{'label': col, 'value': col} for col in numeric_cols],
                        value=numeric_cols[0] if len(numeric_cols) > 0 else None
                    )
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
            ], style={'marginBottom': 30}),
            
            # Charts
            html.Div([
                html.Div([
                    dcc.Graph(id='bar-chart')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='line-chart')
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            html.Div([
                html.Div([
                    dcc.Graph(id='pie-chart')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='scatter-chart')
                ], style={'width': '50%', 'display': 'inline-block'})
            ], style={'marginTop': 20}),
            
            # Summary
            html.Hr(),
            html.Div([
                html.H3("Data Summary", style={'textAlign': 'center'}),
                html.Div(id='data-summary')
            ], style={'marginTop': 30})
        ], style={'padding': 20})
        
        # Callbacks
        @app.callback(
            [Output('bar-chart', 'figure'),
             Output('line-chart', 'figure'),
             Output('pie-chart', 'figure'),
             Output('scatter-chart', 'figure'),
             Output('data-summary', 'children')],
            [Input('x-column', 'value'),
             Input('y-column', 'value')]
        )
        def update_charts(x_col, y_col):
            if not x_col or not y_col:
                empty_fig = go.Figure()
                empty_fig.add_annotation(text="Please select columns", showarrow=False)
                return empty_fig, empty_fig, empty_fig, empty_fig, html.P("Please select columns")
            
            # Bar chart
            bar_fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            
            # Line chart
            line_fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} Trend", markers=True)
            
            # Pie chart (if reasonable number of categories)
            if len(df[x_col].unique()) <= 10:
                pie_data = df.groupby(x_col)[y_col].sum().reset_index()
                pie_fig = px.pie(pie_data, values=y_col, names=x_col, title=f"{y_col} Distribution")
            else:
                pie_fig = go.Figure()
                pie_fig.add_annotation(text="Too many categories for pie chart", showarrow=False)
            
            # Scatter chart
            scatter_fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
            
            # Summary
            summary = html.Div([
                html.P(f"Total {y_col}: {df[y_col].sum():,.2f}"),
                html.P(f"Average {y_col}: {df[y_col].mean():,.2f}"),
                html.P(f"Data Points: {len(df)}"),
                html.P(f"Unique {x_col}: {df[x_col].nunique()}")
            ], style={'textAlign': 'center'})
            
            return bar_fig, line_fig, pie_fig, scatter_fig, summary
        
        # Start server
        def run_server():
            app.run(host='localhost', port=port, debug=False)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(2)
        
        url = f"http://localhost:{port}/{chart_id}/"
        self.running_charts[chart_id] = {
            'app': app,
            'thread': thread,
            'port': port,
            'url': url,
            'type': 'comprehensive',
            'created_at': datetime.now(),
            'title': title
        }
        
        if auto_open:
            webbrowser.open(url)
        
        return {
            'success': True,
            'chart_id': chart_id,
            'url': url,
            'port': port,
            'type': 'comprehensive',
            'message': f"Comprehensive dashboard launched at {url}"
        }
    
    def list_active_charts(self) -> Dict[str, Any]:
        """List all active chart dashboards"""
        active_charts = []
        for chart_id, info in self.running_charts.items():
            active_charts.append({
                'chart_id': chart_id,
                'url': info['url'],
                'port': info['port'],
                'type': info['type'],
                'title': info['title'],
                'created_at': info['created_at'].isoformat(),
                'running_time': str(datetime.now() - info['created_at'])
            })
        
        return {
            'success': True,
            'active_charts': active_charts,
            'total_count': len(active_charts)
        }
    
    def stop_chart(self, chart_id: str) -> Dict[str, Any]:
        """Stop a specific chart dashboard"""
        if chart_id in self.running_charts:
            # Note: Dash apps can't be easily stopped, they'll terminate when process ends
            chart_info = self.running_charts.pop(chart_id)
            return {
                'success': True,
                'message': f"Chart {chart_id} removed from active list",
                'chart_id': chart_id
            }
        else:
            return {
                'success': False,
                'error': f"Chart {chart_id} not found"
            }

# Convenience functions for backward compatibility
def generate_chart_from_dax_results(dax_results: Dict, chart_type: str = "auto", 
                                   output_filename: str = None, chart_title: str = None,
                                   interactive: bool = True, x_column: str = None, 
                                   y_column: str = None, title: str = None) -> Dict[str, Any]:
    """Generate chart from DAX results using Dash (backward compatibility)"""
    
    try:
        # Handle both parameter names for title
        final_title = chart_title or title
        
        generator = DashChartGenerator()
        df = generator.process_dax_results(dax_results)
        
        # Auto-detect columns if not specified
        if not x_column:
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            x_column = categorical_cols[0] if categorical_cols else df.columns[0]
        
        if not y_column:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            y_column = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        title = final_title or f"{y_column} by {x_column}"
        chart_id = output_filename or f"chart_{int(time.time())}"
        
        if chart_type in ["bar", "auto"]:
            return generator.create_bar_chart_dashboard(df, x_column, y_column, title, chart_id, interactive)
        elif chart_type == "line":
            return generator.create_line_chart_dashboard(df, x_column, y_column, title, chart_id, interactive)
        elif chart_type == "dashboard":
            return generator.create_comprehensive_dashboard(df, title, chart_id, interactive)
        else:
            # Default to bar chart
            return generator.create_bar_chart_dashboard(df, x_column, y_column, title, chart_id, interactive)
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to generate {chart_type} chart"
        }

def analyze_dax_results_for_charts(dax_results: Dict) -> Dict[str, Any]:
    """Analyze DAX results and suggest chart types (backward compatibility)"""
    
    try:
        generator = DashChartGenerator()
        df = generator.process_dax_results(dax_results)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        recommendations = []
        
        if categorical_cols and numeric_cols:
            recommendations.append("bar")
            recommendations.append("pie")
            
        if datetime_cols and numeric_cols:
            recommendations.append("line")
            
        if len(numeric_cols) >= 2:
            recommendations.append("scatter")
            
        recommendations.append("dashboard")  # Always available
        
        return {
            'success': True,
            'recommended_charts': recommendations,
            'data_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'numeric_columns': len(numeric_cols),
                'categorical_columns': len(categorical_cols),
                'datetime_columns': len(datetime_cols)
            },
            'suggested_x_column': categorical_cols[0] if categorical_cols else datetime_cols[0] if datetime_cols else df.columns[0],
            'suggested_y_column': numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': "Failed to analyze DAX results"
        }
