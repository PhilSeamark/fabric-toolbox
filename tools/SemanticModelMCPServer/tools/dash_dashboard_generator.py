"""
Dash Dashboard Generator for Semantic Model MCP Server
Advanced interactive dashboard generation using Dash and Plotly
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import threading
import time
import webbrowser
from datetime import datetime, timedelta
import socket
import json
import os
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardManager:
    """Manages multiple Dash dashboard instances"""
    
    def __init__(self):
        self.running_dashboards = {}
        self.port_range_start = 8050
        self.port_range_end = 8100
        
    def find_available_port(self) -> int:
        """Find an available port for a new dashboard"""
        for port in range(self.port_range_start, self.port_range_end):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', port))
                sock.close()
                return port
            except OSError:
                continue
        raise RuntimeError("No available ports found in range")
    
    def create_dashboard(self, dashboard_type: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create and launch a new dashboard"""
        try:
            port = self.find_available_port()
            
            if dashboard_type == "weight_tracking":
                dashboard = WeightTrackingDashboard(data, port, **kwargs)
            elif dashboard_type == "dax_analysis":
                dashboard = DAXAnalysisDashboard(data, port, **kwargs)
            elif dashboard_type == "multi_chart":
                dashboard = MultiChartDashboard(data, port, **kwargs)
            elif dashboard_type == "business_intelligence":
                dashboard = BusinessIntelligenceDashboard(data, port, **kwargs)
            else:
                raise ValueError(f"Unknown dashboard type: {dashboard_type}")
            
            # Start dashboard in separate thread
            thread = threading.Thread(target=dashboard.run, daemon=True)
            thread.start()
            
            # Wait a moment for server to start
            time.sleep(2)
            
            dashboard_id = f"{dashboard_type}_{port}"
            self.running_dashboards[dashboard_id] = {
                'dashboard': dashboard,
                'thread': thread,
                'port': port,
                'type': dashboard_type,
                'url': f"http://localhost:{port}",
                'created_at': datetime.now()
            }
            
            # Open browser
            webbrowser.open(f"http://localhost:{port}")
            
            return {
                'success': True,
                'dashboard_id': dashboard_id,
                'url': f"http://localhost:{port}",
                'port': port,
                'type': dashboard_type,
                'message': f"Dashboard launched successfully at http://localhost:{port}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create dashboard: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to create {dashboard_type} dashboard"
            }
    
    def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all running dashboards"""
        return [
            {
                'id': dashboard_id,
                'type': info['type'],
                'url': info['url'],
                'port': info['port'],
                'created_at': info['created_at'].isoformat(),
                'running_time': str(datetime.now() - info['created_at'])
            }
            for dashboard_id, info in self.running_dashboards.items()
        ]
    
    def stop_dashboard(self, dashboard_id: str) -> bool:
        """Stop a specific dashboard"""
        if dashboard_id in self.running_dashboards:
            # Note: Stopping Dash apps cleanly is complex, for now we just remove from tracking
            del self.running_dashboards[dashboard_id]
            return True
        return False

class BaseDashboard:
    """Base class for all dashboard types"""
    
    def __init__(self, data: Dict[str, Any], port: int, title: str = "Analytics Dashboard"):
        self.data = data
        self.port = port
        self.title = title
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup the dashboard layout - to be implemented by subclasses"""
        raise NotImplementedError
    
    def setup_callbacks(self):
        """Setup dashboard callbacks - to be implemented by subclasses"""
        pass
    
    def run(self):
        """Run the dashboard server"""
        try:
            self.app.run_server(
                debug=False,
                host='localhost',
                port=self.port,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Dashboard server error: {str(e)}")

class WeightTrackingDashboard(BaseDashboard):
    """Specialized dashboard for weight tracking data"""
    
    def __init__(self, data: Dict[str, Any], port: int, **kwargs):
        self.weight_data = self.process_weight_data(data)
        super().__init__(data, port, "Weight Tracking Dashboard")
    
    def process_weight_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert DAX results to pandas DataFrame"""
        if 'rows' in data:
            rows = []
            for row in data['rows']:
                # Handle different possible column names
                date_col = None
                weight_col = None
                day_col = None
                
                for key in row.keys():
                    if 'Date' in key:
                        date_col = key
                    elif 'Weight (kg)' in key or 'weight_kg' in key.lower():
                        weight_col = key
                    elif 'Column' in key or 'day' in key.lower():
                        day_col = key
                
                if date_col and weight_col:
                    try:
                        # Parse date
                        date_str = row[date_col]
                        if 'am' in date_str or 'pm' in date_str:
                            date_part = date_str.split(' ')[0]
                            parsed_date = datetime.strptime(date_part, '%d/%m/%Y')
                        else:
                            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        rows.append({
                            'date': parsed_date,
                            'weight_kg': float(row[weight_col]),
                            'day_of_week': row.get(day_col, ''),
                            'date_str': parsed_date.strftime('%B %d, %Y')
                        })
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping row due to parsing error: {e}")
                        continue
            
            df = pd.DataFrame(rows)
            df = df.sort_values('date')
            
            # Calculate additional metrics
            df['weight_change'] = df['weight_kg'].diff()
            df['cumulative_loss'] = df['weight_kg'].iloc[0] - df['weight_kg']
            df['days_from_start'] = (df['date'] - df['date'].iloc[0]).dt.days
            
            return df
        
        return pd.DataFrame()
    
    def setup_layout(self):
        """Setup the weight tracking dashboard layout"""
        
        if self.weight_data.empty:
            self.app.layout = html.Div([
                html.H1("Weight Tracking Dashboard"),
                html.P("No data available to display.")
            ])
            return
        
        # Calculate summary statistics
        start_weight = self.weight_data['weight_kg'].iloc[0]
        current_weight = self.weight_data['weight_kg'].iloc[-1]
        total_loss = start_weight - current_weight
        days_tracked = len(self.weight_data)
        avg_daily_loss = total_loss / days_tracked if days_tracked > 0 else 0
        
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🏃‍♂️ Weight Tracking Dashboard", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
                html.Hr()
            ]),
            
            # Summary Cards
            html.Div([
                html.Div([
                    html.H3(f"{start_weight:.1f} kg", style={'color': '#3498db', 'margin': '0'}),
                    html.P("Starting Weight", style={'margin': '5px 0'})
                ], className='summary-card', style={
                    'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px',
                    'textAlign': 'center', 'margin': '10px', 'flex': '1'
                }),
                
                html.Div([
                    html.H3(f"{current_weight:.1f} kg", style={'color': '#27ae60', 'margin': '0'}),
                    html.P("Current Weight", style={'margin': '5px 0'})
                ], className='summary-card', style={
                    'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px',
                    'textAlign': 'center', 'margin': '10px', 'flex': '1'
                }),
                
                html.Div([
                    html.H3(f"{total_loss:.1f} kg", style={'color': '#e74c3c', 'margin': '0'}),
                    html.P("Total Loss", style={'margin': '5px 0'})
                ], className='summary-card', style={
                    'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px',
                    'textAlign': 'center', 'margin': '10px', 'flex': '1'
                }),
                
                html.Div([
                    html.H3(f"{avg_daily_loss:.3f} kg", style={'color': '#9b59b6', 'margin': '0'}),
                    html.P("Avg Daily Loss", style={'margin': '5px 0'})
                ], className='summary-card', style={
                    'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px',
                    'textAlign': 'center', 'margin': '10px', 'flex': '1'
                })
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '30px'}),
            
            # Date Range Selector
            html.Div([
                html.Label("Select Date Range:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.DatePickerRange(
                    id='date-range-picker',
                    start_date=self.weight_data['date'].min(),
                    end_date=self.weight_data['date'].max(),
                    display_format='YYYY-MM-DD',
                    style={'marginBottom': '20px'}
                )
            ], style={'marginBottom': '30px'}),
            
            # Main Chart
            html.Div([
                dcc.Graph(id='weight-trend-chart')
            ], style={'marginBottom': '30px'}),
            
            # Secondary Charts
            html.Div([
                html.Div([
                    dcc.Graph(id='daily-change-chart')
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='cumulative-loss-chart')
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
            ], style={'marginBottom': '30px'}),
            
            # Data Table
            html.Div([
                html.H3("📊 Recent Readings", style={'color': '#2c3e50'}),
                html.Div(id='data-table')
            ])
            
        ], style={'margin': '20px', 'fontFamily': 'Arial, sans-serif'})
    
    def setup_callbacks(self):
        """Setup callbacks for interactive features"""
        
        @self.app.callback(
            [Output('weight-trend-chart', 'figure'),
             Output('daily-change-chart', 'figure'),
             Output('cumulative-loss-chart', 'figure'),
             Output('data-table', 'children')],
            [Input('date-range-picker', 'start_date'),
             Input('date-range-picker', 'end_date')]
        )
        def update_charts(start_date, end_date):
            # Filter data based on date range
            filtered_df = self.weight_data[
                (self.weight_data['date'] >= start_date) & 
                (self.weight_data['date'] <= end_date)
            ]
            
            # Main weight trend chart
            weight_fig = go.Figure()
            weight_fig.add_trace(go.Scatter(
                x=filtered_df['date'],
                y=filtered_df['weight_kg'],
                mode='lines+markers',
                name='Weight',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8, color='#2980b9'),
                hovertemplate='<b>%{x}</b><br>Weight: %{y:.1f} kg<extra></extra>'
            ))
            
            # Add trend line
            z = np.polyfit(filtered_df['days_from_start'], filtered_df['weight_kg'], 1)
            p = np.poly1d(z)
            weight_fig.add_trace(go.Scatter(
                x=filtered_df['date'],
                y=p(filtered_df['days_from_start']),
                mode='lines',
                name='Trend',
                line=dict(color='#e74c3c', width=2, dash='dash'),
                hovertemplate='Trend: %{y:.1f} kg<extra></extra>'
            ))
            
            weight_fig.update_layout(
                title='Weight Progress Over Time',
                xaxis_title='Date',
                yaxis_title='Weight (kg)',
                template='plotly_white',
                height=400
            )
            
            # Daily change chart
            change_fig = go.Figure()
            colors = ['#27ae60' if x < 0 else '#e74c3c' for x in filtered_df['weight_change'].fillna(0)]
            change_fig.add_trace(go.Bar(
                x=filtered_df['date'],
                y=filtered_df['weight_change'].fillna(0),
                marker_color=colors,
                name='Daily Change',
                hovertemplate='<b>%{x}</b><br>Change: %{y:.2f} kg<extra></extra>'
            ))
            
            change_fig.update_layout(
                title='Daily Weight Changes',
                xaxis_title='Date',
                yaxis_title='Weight Change (kg)',
                template='plotly_white',
                height=300
            )
            
            # Cumulative loss chart
            loss_fig = go.Figure()
            loss_fig.add_trace(go.Scatter(
                x=filtered_df['date'],
                y=filtered_df['cumulative_loss'],
                mode='lines+markers',
                fill='tonexty',
                name='Cumulative Loss',
                line=dict(color='#27ae60', width=3),
                marker=dict(size=6, color='#229954'),
                hovertemplate='<b>%{x}</b><br>Total Loss: %{y:.1f} kg<extra></extra>'
            ))
            
            loss_fig.update_layout(
                title='Cumulative Weight Loss',
                xaxis_title='Date',
                yaxis_title='Weight Lost (kg)',
                template='plotly_white',
                height=300
            )
            
            # Data table
            recent_data = filtered_df.tail(10)[['date_str', 'weight_kg', 'weight_change', 'cumulative_loss']].copy()
            table_rows = []
            for _, row in recent_data.iterrows():
                table_rows.append(html.Tr([
                    html.Td(row['date_str']),
                    html.Td(f"{row['weight_kg']:.1f} kg"),
                    html.Td(f"{row['weight_change']:.2f} kg" if pd.notna(row['weight_change']) else "-"),
                    html.Td(f"{row['cumulative_loss']:.1f} kg")
                ]))
            
            table = html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Date"),
                        html.Th("Weight"),
                        html.Th("Daily Change"),
                        html.Th("Total Loss")
                    ])
                ]),
                html.Tbody(table_rows)
            ], style={
                'width': '100%',
                'textAlign': 'center',
                'border': '1px solid #ddd',
                'borderCollapse': 'collapse'
            })
            
            return weight_fig, change_fig, loss_fig, table

class DAXAnalysisDashboard(BaseDashboard):
    """Dashboard for general DAX query analysis"""
    
    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("DAX Analysis Dashboard"),
            html.P("Advanced DAX query visualization and analysis tools coming soon...")
        ])

class MultiChartDashboard(BaseDashboard):
    """Dashboard with multiple chart types"""
    
    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Multi-Chart Dashboard"),
            html.P("Comprehensive multi-chart visualization platform coming soon...")
        ])

class BusinessIntelligenceDashboard(BaseDashboard):
    """Full business intelligence dashboard"""
    
    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Business Intelligence Dashboard"),
            html.P("Enterprise-grade BI dashboard with Power BI integration coming soon...")
        ])

# Add required numpy import
import numpy as np

# Global dashboard manager instance
dashboard_manager = DashboardManager()

def create_weight_dashboard(dax_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Create a weight tracking dashboard from DAX results"""
    return dashboard_manager.create_dashboard("weight_tracking", dax_results, **kwargs)

def create_dax_dashboard(dax_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Create a general DAX analysis dashboard"""
    return dashboard_manager.create_dashboard("dax_analysis", dax_results, **kwargs)

def list_active_dashboards() -> List[Dict[str, Any]]:
    """List all currently running dashboards"""
    return dashboard_manager.list_dashboards()

def stop_dashboard(dashboard_id: str) -> bool:
    """Stop a specific dashboard"""
    return dashboard_manager.stop_dashboard(dashboard_id)

if __name__ == "__main__":
    # Test with sample data
    sample_weight_data = {
        "rows": [
            {"Weight Readings[Date]": "2/07/2025 12:00:00 am", "Weight Readings[Weight (kg)]": "83.4", "Weight Readings[Column]": "Wed"},
            {"Weight Readings[Date]": "3/07/2025 12:00:00 am", "Weight Readings[Weight (kg)]": "81.7", "Weight Readings[Column]": "Thu"},
            {"Weight Readings[Date]": "15/08/2025 12:00:00 am", "Weight Readings[Weight (kg)]": "75.6", "Weight Readings[Column]": "Fri"}
        ]
    }
    
    result = create_weight_dashboard(sample_weight_data)
    print(f"Dashboard created: {result}")
