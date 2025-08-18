"""
Simple Test Dashboard - Debugging Version
Following DASH_DASHBOARD_GUIDE.md patterns
"""

import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import json
import socket

class SimpleTestDashboard:
    """
    Simple test dashboard to debug blank page issues
    """
    
    def __init__(self, dax_results):
        self.data = self.process_dax_data(dax_results)
        self.app = dash.Dash(__name__)
        print(f"Data loaded: {len(self.data)} rows")
        print(f"Columns: {list(self.data.columns)}")
        
    def process_dax_data(self, dax_results):
        """Convert DAX results to Pandas DataFrame"""
        if isinstance(dax_results, str):
            dax_results = json.loads(dax_results)
        
        if 'data' in dax_results:
            df = pd.DataFrame(dax_results['data'])
        else:
            df = pd.DataFrame(dax_results)
            
        # Convert numeric columns
        try:
            df['adw_FactInternetSales[SalesAmount]'] = pd.to_numeric(df['adw_FactInternetSales[SalesAmount]'], errors='coerce')
            df['adw_FactInternetSales[OrderQuantity]'] = pd.to_numeric(df['adw_FactInternetSales[OrderQuantity]'], errors='coerce')
        except Exception as e:
            print(f"Warning: Could not convert numeric columns: {e}")
                
        return df
        
    def create_simple_chart(self):
        """Create a simple bar chart"""
        try:
            # Group by ProductKey and sum SalesAmount
            chart_data = self.data.groupby('adw_FactInternetSales[ProductKey]')['adw_FactInternetSales[SalesAmount]'].sum().reset_index()
            chart_data = chart_data.head(10)  # Top 10
            
            fig = px.bar(
                chart_data,
                x='adw_FactInternetSales[ProductKey]',
                y='adw_FactInternetSales[SalesAmount]',
                title="Sales by Product Key",
                template="plotly_white"
            )
            fig.update_layout(height=400)
            return fig
        except Exception as e:
            print(f"Error creating chart: {e}")
            # Return empty figure
            fig = px.bar(x=[1, 2, 3], y=[1, 2, 3], title="Error: Could not create chart")
            return fig
        
    def create_dashboard(self):
        """Create simple dashboard layout"""
        try:
            total_sales = self.data['adw_FactInternetSales[SalesAmount]'].sum()
            total_orders = len(self.data)
            
            self.app.layout = html.Div([
                html.Div([
                    html.H1("🚀 Simple Test Dashboard", 
                           style={'text-align': 'center', 'color': '#2c3e50', 'margin-bottom': '20px'})
                ]),
                
                html.Div([
                    html.Div([
                        html.H2(f"${total_sales:,.2f}", style={'color': '#1f77b4', 'margin': '0'}),
                        html.P("Total Sales", style={'margin': '5px 0'})
                    ], style={'text-align': 'center', 'background': '#f8f9fa', 'padding': '20px', 'border-radius': '8px', 'margin': '20px'}),
                    
                    html.Div([
                        html.H2(f"{total_orders}", style={'color': '#ff7f0e', 'margin': '0'}),
                        html.P("Total Orders", style={'margin': '5px 0'})
                    ], style={'text-align': 'center', 'background': '#f8f9fa', 'padding': '20px', 'border-radius': '8px', 'margin': '20px'})
                ], style={'display': 'flex', 'justify-content': 'space-around'}),
                
                html.Div([
                    dcc.Graph(figure=self.create_simple_chart())
                ], style={'margin': '20px'}),
                
                html.Div([
                    html.H3("Debug Info:"),
                    html.P(f"Rows loaded: {len(self.data)}"),
                    html.P(f"First few product keys: {list(self.data['adw_FactInternetSales[ProductKey]'].head())}")
                ], style={'margin': '20px', 'background': '#e9ecef', 'padding': '15px', 'border-radius': '5px'})
                
            ], style={'margin': '20px', 'font-family': 'Arial, sans-serif'})
            
        except Exception as e:
            print(f"Error creating layout: {e}")
            self.app.layout = html.Div([
                html.H1("Error Loading Dashboard"),
                html.P(f"Error: {str(e)}")
            ])
        
    def find_available_port(self, start_port=8052):
        """Find an available port"""
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except socket.error:
                continue
        return start_port
        
    def run(self, port=8052):
        """Launch dashboard"""
        try:
            self.create_dashboard()
            available_port = self.find_available_port(port)
            print(f"🎯 Simple dashboard running at: http://127.0.0.1:{available_port}")
            self.app.run(debug=True, port=available_port, host='127.0.0.1')
        except Exception as e:
            print(f"Error running dashboard: {e}")

if __name__ == "__main__":
    # Test data
    test_data = {
        "data": [
            {"adw_FactInternetSales[ProductKey]": "237", "adw_FactInternetSales[SalesAmount]": 49.99, "adw_FactInternetSales[OrderQuantity]": "1"},
            {"adw_FactInternetSales[ProductKey]": "310", "adw_FactInternetSales[SalesAmount]": 2869.72, "adw_FactInternetSales[OrderQuantity]": "2"},
            {"adw_FactInternetSales[ProductKey]": "345", "adw_FactInternetSales[SalesAmount]": 2384.07, "adw_FactInternetSales[OrderQuantity]": "1"},
            {"adw_FactInternetSales[ProductKey]": "529", "adw_FactInternetSales[SalesAmount]": 419.46, "adw_FactInternetSales[OrderQuantity]": "1"}
        ]
    }
    
    dashboard = SimpleTestDashboard(test_data)
    dashboard.run()
