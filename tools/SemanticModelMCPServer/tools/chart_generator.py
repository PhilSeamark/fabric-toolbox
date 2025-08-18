"""
Dash-Only Chart Generator for Semantic Model MCP Server
Replaces Vega-Lite/Altair/Matplotlib with pure Dash/Plotly implementation
"""

import dash
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# Import our new Dash chart generator
from tools.dash_chart_generator import (
    DashChartGenerator, 
    generate_chart_from_dax_results, 
    analyze_dax_results_for_charts
)

class ChartGenerator:
    """
    Chart Generator - Now using Dash/Plotly only
    Maintains backward compatibility while using new Dash-based system
    """
    
    def __init__(self, output_dir: str = "output"):
        """Initialize chart generator with Dash backend"""
        self.output_dir = output_dir
        self.dash_generator = DashChartGenerator(output_dir)
        self.ensure_output_dir()
        
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_dax_results(self, results: Dict) -> pd.DataFrame:
        """Convert DAX query results to pandas DataFrame"""
        return self.dash_generator.process_dax_results(results)
    
    def generate_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                          title: str = "Bar Chart", filename: str = None, 
                          interactive: bool = True, horizontal: bool = False) -> str:
        """
        Generate bar chart using Dash dashboard
        Returns: Dashboard URL instead of file path
        """
        if not filename:
            filename = f"bar_chart_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.dash_generator.create_bar_chart_dashboard(
            df, x_col, y_col, title, filename, auto_open=interactive
        )
        
        if result['success']:
            return result['url']
        else:
            raise ValueError(f"Failed to create bar chart: {result.get('error', 'Unknown error')}")
    
    def generate_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                           title: str = "Line Chart", filename: str = None, 
                           interactive: bool = True) -> str:
        """
        Generate line chart using Dash dashboard  
        Returns: Dashboard URL instead of file path
        """
        if not filename:
            filename = f"line_chart_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.dash_generator.create_line_chart_dashboard(
            df, x_col, y_col, title, filename, auto_open=interactive
        )
        
        if result['success']:
            return result['url']
        else:
            raise ValueError(f"Failed to create line chart: {result.get('error', 'Unknown error')}")
    
    def generate_pie_chart(self, df: pd.DataFrame, values_col: str, names_col: str, 
                          title: str = "Pie Chart", filename: str = None, 
                          interactive: bool = True) -> str:
        """
        Generate pie chart using comprehensive dashboard
        Returns: Dashboard URL
        """
        if not filename:
            filename = f"pie_chart_{values_col}_{names_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.dash_generator.create_comprehensive_dashboard(
            df, title, filename, auto_open=interactive
        )
        
        if result['success']:
            return result['url']
        else:
            raise ValueError(f"Failed to create pie chart: {result.get('error', 'Unknown error')}")
    
    def generate_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                             title: str = "Scatter Plot", filename: str = None, 
                             interactive: bool = True, size_col: str = None) -> str:
        """
        Generate scatter plot using comprehensive dashboard
        Returns: Dashboard URL
        """
        if not filename:
            filename = f"scatter_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.dash_generator.create_comprehensive_dashboard(
            df, title, filename, auto_open=interactive
        )
        
        if result['success']:
            return result['url']
        else:
            raise ValueError(f"Failed to create scatter plot: {result.get('error', 'Unknown error')}")
    
    def generate_heatmap(self, df: pd.DataFrame, title: str = "Heatmap", 
                        filename: str = None, interactive: bool = True) -> str:
        """
        Generate heatmap using comprehensive dashboard
        Returns: Dashboard URL
        """
        if not filename:
            filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.dash_generator.create_comprehensive_dashboard(
            df, title, filename, auto_open=interactive
        )
        
        if result['success']:
            return result['url']
        else:
            raise ValueError(f"Failed to create heatmap: {result.get('error', 'Unknown error')}")
    
    def create_comprehensive_dashboard(self, df: pd.DataFrame, 
                                     title: str = "Comprehensive Dashboard",
                                     filename: str = None) -> str:
        """
        Create comprehensive multi-chart dashboard
        Returns: Dashboard URL
        """
        if not filename:
            filename = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.dash_generator.create_comprehensive_dashboard(
            df, title, filename, auto_open=True
        )
        
        if result['success']:
            return result['url']
        else:
            raise ValueError(f"Failed to create dashboard: {result.get('error', 'Unknown error')}")
    
    def auto_generate_charts(self, df: pd.DataFrame, title_prefix: str = "Auto Chart") -> List[str]:
        """
        Automatically generate appropriate charts based on data characteristics
        Returns: List of dashboard URLs
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        dashboards = []
        
        # Generate bar chart if we have categorical and numeric columns
        if categorical_cols and numeric_cols:
            result = self.dash_generator.create_bar_chart_dashboard(
                df, categorical_cols[0], numeric_cols[0], 
                f"{title_prefix} - Bar Chart", 
                f"auto_bar_{int(datetime.now().timestamp())}"
            )
            if result['success']:
                dashboards.append(result['url'])
        
        # Generate line chart if we have datetime and numeric columns
        if datetime_cols and numeric_cols:
            result = self.dash_generator.create_line_chart_dashboard(
                df, datetime_cols[0], numeric_cols[0], 
                f"{title_prefix} - Time Series", 
                f"auto_line_{int(datetime.now().timestamp())}"
            )
            if result['success']:
                dashboards.append(result['url'])
        
        # Always create comprehensive dashboard
        result = self.dash_generator.create_comprehensive_dashboard(
            df, f"{title_prefix} - Comprehensive Analysis", 
            f"auto_comprehensive_{int(datetime.now().timestamp())}"
        )
        if result['success']:
            dashboards.append(result['url'])
        
        return dashboards
    
    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze DataFrame structure and suggest visualizations"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        suggestions = []
        
        if categorical_cols and numeric_cols:
            suggestions.extend(['bar_chart', 'pie_chart'])
            
        if datetime_cols and numeric_cols:
            suggestions.append('line_chart')
            
        if len(numeric_cols) >= 2:
            suggestions.append('scatter_plot')
            
        if len(numeric_cols) >= 3:
            suggestions.append('heatmap')
            
        suggestions.append('comprehensive_dashboard')
        
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(categorical_cols), 
            'datetime_columns': len(datetime_cols),
            'suggested_charts': suggestions,
            'recommended_x_column': categorical_cols[0] if categorical_cols else datetime_cols[0] if datetime_cols else df.columns[0],
            'recommended_y_column': numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
        }

# Export the backward-compatible functions
def generate_chart(data: Union[Dict, pd.DataFrame], chart_type: str = "auto", 
                  output_filename: str = None, title: str = None, 
                  interactive: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Backward-compatible chart generation function
    Now returns Dash dashboard URLs instead of static files
    """
    return generate_chart_from_dax_results(
        data, chart_type, output_filename=output_filename, 
        chart_title=title, interactive=interactive, **kwargs
    )

def analyze_data_for_charts(data: Union[Dict, pd.DataFrame]) -> Dict[str, Any]:
    """
    Backward-compatible data analysis function  
    """
    return analyze_dax_results_for_charts(data)
