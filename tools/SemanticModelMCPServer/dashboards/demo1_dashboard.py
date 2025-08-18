import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime
import socket

class Demo1Dashboard:
    """
    Adventure Works Demo Dashboard following DASH_DASHBOARD_GUIDE.md patterns
    """
    
    def __init__(self, dax_results):
        self.data = self.process_dax_data(dax_results)
        self.app = dash.Dash(__name__)
        
    def process_dax_data(self, dax_results):
        """Convert DAX results to Pandas DataFrame"""
        if isinstance(dax_results, str):
            dax_results = json.loads(dax_results)
        
        if 'data' in dax_results:
            df = pd.DataFrame(dax_results['data'])
        else:
            df = pd.DataFrame(dax_results)
            
        # Process date columns
        if 'adw_FactInternetSales[OrderDate]' in df.columns:
            df['OrderDate'] = pd.to_datetime(df['adw_FactInternetSales[OrderDate]'])
            df['Year'] = df['OrderDate'].dt.year
            df['Month'] = df['OrderDate'].dt.month
            df['YearMonth'] = df['OrderDate'].dt.to_period('M')
            
        # Process numeric columns
        numeric_cols = ['adw_FactInternetSales[SalesAmount]', 'adw_FactInternetSales[OrderQuantity]', 
                       'adw_FactInternetSales[UnitPrice]', 'adw_FactInternetSales[TotalLineAmount]']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
        
    def create_kpi_cards(self):
        """Create KPI cards with business metrics"""
        total_sales = self.data['adw_FactInternetSales[SalesAmount]'].sum()
        total_orders = len(self.data)
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        total_quantity = self.data['adw_FactInternetSales[OrderQuantity]'].sum()
        
        return html.Div([
            html.Div([
                html.H3(f"${total_sales:,.2f}", style={'color': '#1f77b4', 'margin': '0'}),
                html.P("Total Sales", style={'margin': '5px 0', 'color': '#666'})
            ], style={'background': '#f8f9fa', 'padding': '20px', 'border-radius': '8px', 'text-align': 'center', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '0 10px'}),
            
            html.Div([
                html.H3(f"{total_orders:,}", style={'color': '#ff7f0e', 'margin': '0'}),
                html.P("Total Orders", style={'margin': '5px 0', 'color': '#666'})
            ], style={'background': '#f8f9fa', 'padding': '20px', 'border-radius': '8px', 'text-align': 'center', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '0 10px'}),
            
            html.Div([
                html.H3(f"${avg_order_value:.2f}", style={'color': '#2ca02c', 'margin': '0'}),
                html.P("Avg Order Value", style={'margin': '5px 0', 'color': '#666'})
            ], style={'background': '#f8f9fa', 'padding': '20px', 'border-radius': '8px', 'text-align': 'center', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '0 10px'}),
            
            html.Div([
                html.H3(f"{total_quantity:,}", style={'color': '#d62728', 'margin': '0'}),
                html.P("Total Quantity", style={'margin': '5px 0', 'color': '#666'})
            ], style={'background': '#f8f9fa', 'padding': '20px', 'border-radius': '8px', 'text-align': 'center', 'box-shadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '0 10px'})
        ], style={'display': 'flex', 'justify-content': 'space-around', 'margin-bottom': '30px', 'gap': '20px'})
        
    def create_sales_trend_chart(self):
        """Create sales trend line chart"""
        if 'YearMonth' in self.data.columns:
            trend_data = self.data.groupby('YearMonth')['adw_FactInternetSales[SalesAmount]'].sum().reset_index()
            trend_data['YearMonth'] = trend_data['YearMonth'].astype(str)
            
            fig = px.line(
                trend_data, 
                x='YearMonth', 
                y='adw_FactInternetSales[SalesAmount]',
                title="Sales Trend Over Time",
                template="plotly_white"
            )
            fig.update_layout(
                height=400,
                showlegend=True,
                hovermode='x unified',
                xaxis_title="Time Period",
                yaxis_title="Sales Amount ($)"
            )
            return fig
        else:
            # Fallback chart if no date data
            return px.bar(
                self.data.head(10), 
                x='adw_FactInternetSales[SalesID]', 
                y='adw_FactInternetSales[SalesAmount]',
                title="Sales by Order ID (Top 10)"
            )
        
    def create_product_performance_chart(self):
        """Create product performance bar chart"""
        product_data = self.data.groupby('adw_FactInternetSales[ProductKey]')['adw_FactInternetSales[SalesAmount]'].sum().reset_index()
        product_data = product_data.sort_values('adw_FactInternetSales[SalesAmount]', ascending=False).head(10)
        
        fig = px.bar(
            product_data,
            x='adw_FactInternetSales[ProductKey]',
            y='adw_FactInternetSales[SalesAmount]',
            title="Top Products by Sales Amount",
            template="plotly_white"
        )
        fig.update_layout(
            height=400,
            xaxis_title="Product Key",
            yaxis_title="Sales Amount ($)"
        )
        return fig
        
    def create_margin_analysis_chart(self):
        """Create scatter plot for margin analysis"""
        self.data['Margin'] = self.data['adw_FactInternetSales[SalesAmount]'] - self.data['adw_FactInternetSales[TotalProductCost]']
        
        fig = px.scatter(
            self.data,
            x='adw_FactInternetSales[SalesAmount]',
            y='Margin',
            size='adw_FactInternetSales[OrderQuantity]',
            title="Sales vs Margin Analysis",
            template="plotly_white"
        )
        fig.update_layout(
            height=400,
            xaxis_title="Sales Amount ($)",
            yaxis_title="Margin ($)"
        )
        return fig
        
    def create_customer_insights_chart(self):
        """Create pie chart for customer distribution"""
        customer_data = self.data.groupby('adw_FactInternetSales[CustomerKey]')['adw_FactInternetSales[SalesAmount]'].sum().reset_index()
        customer_data = customer_data.sort_values('adw_FactInternetSales[SalesAmount]', ascending=False).head(5)
        
        fig = px.pie(
            customer_data,
            values='adw_FactInternetSales[SalesAmount]',
            names='adw_FactInternetSales[CustomerKey]',
            title="Top 5 Customers by Sales",
            template="plotly_white"
        )
        fig.update_layout(height=400)
        return fig
        
    def create_dashboard(self):
        """Create 4-chart business intelligence layout"""
        self.app.layout = html.Div([
            html.Div([
                html.H1("Adventure Works Sales Analysis Dashboard", 
                       style={'text-align': 'center', 'margin-bottom': '30px', 'color': '#2c3e50', 'font-family': 'Arial, sans-serif'})
            ]),
            
            # KPI Cards Section
            html.Div([
                self.create_kpi_cards()
            ]),
            
            # Charts Section  
            html.Div([
                html.Div([
                    dcc.Graph(figure=self.create_sales_trend_chart())
                ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),
                
                html.Div([
                    dcc.Graph(figure=self.create_product_performance_chart())
                ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),
                
                html.Div([
                    dcc.Graph(figure=self.create_margin_analysis_chart())
                ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),
                
                html.Div([
                    dcc.Graph(figure=self.create_customer_insights_chart())
                ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
            ], style={'margin-top': '20px'}),
            
            # Data Summary Section
            html.Div([
                html.H3("Data Summary", style={'margin-top': '30px', 'color': '#2c3e50'}),
                html.P(f"Showing {len(self.data)} sales transactions from Adventure Works FactInternetSales table.", 
                       style={'margin': '10px 0', 'color': '#666'}),
                html.P(f"Date range: {self.data['adw_FactInternetSales[OrderDate]'].min()} to {self.data['adw_FactInternetSales[OrderDate]'].max()}", 
                       style={'margin': '10px 0', 'color': '#666'})
            ])
        ], style={'margin': '20px', 'font-family': 'Arial, sans-serif'})
        
    def find_available_port(self, start_port=8050):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except socket.error:
                continue
        return start_port  # Return default if none found
        
    def run(self, port=8050):
        """Launch dashboard with auto port detection"""
        self.create_dashboard()
        available_port = self.find_available_port(port)
        print(f"Dashboard running at: http://127.0.0.1:{available_port}")
        self.app.run(debug=True, port=available_port)
