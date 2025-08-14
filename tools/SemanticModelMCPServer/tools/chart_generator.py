"""
Chart and Diagram Generator for Semantic Model MCP Server
Generates various types of visualizations from DAX query results and model data
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Any, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# Configure Altair to save charts as HTML files
alt.data_transformers.enable('json')

class ChartGenerator:
    """Generate charts and diagrams from Power BI data"""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize chart generator with output directory"""
        self.output_dir = output_dir
        self.ensure_output_dir()
        
        # Set style preferences
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_dax_results(self, results: Dict) -> pd.DataFrame:
        """Convert DAX query results to pandas DataFrame"""
        if not results.get('success', False):
            raise ValueError(f"DAX query failed: {results.get('error', 'Unknown error')}")
        
        # Extract data from results
        rows = results.get('rows', [])
        columns = results.get('columns', [])
        
        if not rows or not columns:
            raise ValueError("No data returned from DAX query")
        
        # Create DataFrame
        data = []
        for row in rows:
            row_data = {}
            for col in columns:
                col_name = col['name'].split('[')[-1].rstrip(']')  # Clean column names
                row_data[col_name] = row.get(col['name'], None)
            data.append(row_data)
        
        df = pd.DataFrame(data)
        
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
    
    def generate_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                          title: str = "Line Chart", filename: str = None, 
                          interactive: bool = True) -> str:
        """Generate a line chart from DataFrame"""
        
        if interactive:
            # Vega-Lite interactive chart
            chart = alt.Chart(df).mark_line(point=True).add_selection(
                alt.selection_interval(bind='scales')
            ).encode(
                x=alt.X(f'{x_col}:T' if df[x_col].dtype.name.startswith('datetime') else f'{x_col}:O', 
                       title=x_col.title()),
                y=alt.Y(f'{y_col}:Q', title=y_col.title()),
                tooltip=[x_col, y_col]
            ).properties(
                title=title,
                width=600,
                height=400
            ).interactive()
            
            if not filename:
                filename = f"line_chart_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            filepath = os.path.join(self.output_dir, filename)
            chart.save(filepath)
            
        else:
            # Matplotlib static chart
            plt.figure(figsize=(12, 6))
            plt.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=4)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_col.title(), fontsize=12)
            plt.ylabel(y_col.title(), fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if not filename:
                filename = f"line_chart_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
        
        return filepath
    
    def generate_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                          title: str = "Bar Chart", filename: str = None,
                          horizontal: bool = False, interactive: bool = True) -> str:
        """Generate a bar chart from DataFrame"""
        
        if interactive:
            # Vega-Lite interactive chart
            if horizontal:
                chart = alt.Chart(df).mark_bar().add_selection(
                    alt.selection_interval()
                ).encode(
                    x=alt.X(f'{y_col}:Q', title=y_col.title()),
                    y=alt.Y(f'{x_col}:O', title=x_col.title(), sort='-x'),
                    tooltip=[x_col, y_col],
                    color=alt.Color(f'{x_col}:N', legend=None)
                ).properties(
                    title=title,
                    width=600,
                    height=400
                )
            else:
                chart = alt.Chart(df).mark_bar().add_selection(
                    alt.selection_interval()
                ).encode(
                    x=alt.X(f'{x_col}:O', title=x_col.title()),
                    y=alt.Y(f'{y_col}:Q', title=y_col.title()),
                    tooltip=[x_col, y_col],
                    color=alt.Color(f'{x_col}:N', legend=None)
                ).properties(
                    title=title,
                    width=600,
                    height=400
                )
            
            if not filename:
                filename = f"bar_chart_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            filepath = os.path.join(self.output_dir, filename)
            chart.save(filepath)
            
        else:
            # Matplotlib static chart
            plt.figure(figsize=(12, 6))
            if horizontal:
                plt.barh(df[x_col], df[y_col])
                plt.xlabel(y_col.title())
                plt.ylabel(x_col.title())
            else:
                plt.bar(df[x_col], df[y_col])
                plt.xlabel(x_col.title())
                plt.ylabel(y_col.title())
                plt.xticks(rotation=45)
            
            plt.title(title, fontsize=16, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='y' if not horizontal else 'x')
            plt.tight_layout()
            
            if not filename:
                filename = f"bar_chart_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
        
        return filepath
    
    def generate_pie_chart(self, df: pd.DataFrame, label_col: str, value_col: str,
                          title: str = "Pie Chart", filename: str = None,
                          interactive: bool = True) -> str:
        """Generate a pie chart from DataFrame"""
        
        if interactive:
            # Vega-Lite interactive pie chart (using arc marks)
            chart = alt.Chart(df).mark_arc(innerRadius=0).encode(
                theta=alt.Theta(f'{value_col}:Q', title=value_col.title()),
                color=alt.Color(f'{label_col}:N', title=label_col.title()),
                tooltip=[label_col, value_col, alt.Tooltip('theta:Q', format='.1%')]
            ).properties(
                title=title,
                width=400,
                height=400
            ).resolve_scale(
                color='independent'
            )
            
            if not filename:
                filename = f"pie_chart_{label_col}_{value_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            filepath = os.path.join(self.output_dir, filename)
            chart.save(filepath)
            
        else:
            # Matplotlib static chart
            plt.figure(figsize=(10, 8))
            plt.pie(df[value_col], labels=df[label_col], autopct='%1.1f%%', startangle=90)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            if not filename:
                filename = f"pie_chart_{label_col}_{value_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
        
        return filepath
    
    def generate_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str,
                             title: str = "Scatter Plot", filename: str = None,
                             color_col: str = None, size_col: str = None,
                             interactive: bool = True) -> str:
        """Generate a scatter plot from DataFrame"""
        
        if interactive:
            # Vega-Lite interactive scatter plot
            encoding = {
                'x': alt.X(f'{x_col}:Q', title=x_col.title()),
                'y': alt.Y(f'{y_col}:Q', title=y_col.title()),
                'tooltip': [x_col, y_col]
            }
            
            if color_col and color_col in df.columns:
                encoding['color'] = alt.Color(f'{color_col}:N', title=color_col.title())
                encoding['tooltip'].append(color_col)
            
            if size_col and size_col in df.columns:
                encoding['size'] = alt.Size(f'{size_col}:Q', title=size_col.title())
                encoding['tooltip'].append(size_col)
            
            chart = alt.Chart(df).mark_circle(opacity=0.7).add_selection(
                alt.selection_interval(bind='scales')
            ).encode(**encoding).properties(
                title=title,
                width=600,
                height=400
            ).interactive()
            
            if not filename:
                filename = f"scatter_plot_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            filepath = os.path.join(self.output_dir, filename)
            chart.save(filepath)
            
        else:
            # Matplotlib static chart
            plt.figure(figsize=(10, 6))
            
            if color_col and color_col in df.columns:
                scatter = plt.scatter(df[x_col], df[y_col], c=df[color_col], 
                                    s=df[size_col] if size_col and size_col in df.columns else 50,
                                    alpha=0.7, cmap='viridis')
                plt.colorbar(scatter, label=color_col.title())
            else:
                plt.scatter(df[x_col], df[y_col], alpha=0.7)
            
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_col.title(), fontsize=12)
            plt.ylabel(y_col.title(), fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if not filename:
                filename = f"scatter_plot_{x_col}_{y_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
        
        return filepath
    
    def generate_heatmap(self, df: pd.DataFrame, title: str = "Heatmap",
                        filename: str = None, interactive: bool = True) -> str:
        """Generate a heatmap from DataFrame correlation matrix"""
        
        # Calculate correlation matrix for numeric columns only
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            raise ValueError("Need at least 2 numeric columns for heatmap")
        
        corr_matrix = df[numeric_cols].corr()
        
        if interactive:
            # Vega-Lite interactive heatmap
            # Convert correlation matrix to long format for Vega-Lite
            corr_long = corr_matrix.reset_index().melt(id_vars='index')
            corr_long.columns = ['Variable1', 'Variable2', 'Correlation']
            
            chart = alt.Chart(corr_long).mark_rect().encode(
                x=alt.X('Variable1:O', title=''),
                y=alt.Y('Variable2:O', title=''),
                color=alt.Color('Correlation:Q', 
                              scale=alt.Scale(scheme='redblue', domain=[-1, 1]),
                              title='Correlation'),
                tooltip=['Variable1', 'Variable2', alt.Tooltip('Correlation:Q', format='.3f')]
            ).properties(
                title=title,
                width=400,
                height=400
            )
            
            if not filename:
                filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            filepath = os.path.join(self.output_dir, filename)
            chart.save(filepath)
            
        else:
            # Matplotlib static heatmap
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0,
                       square=True, linewidths=0.5)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            if not filename:
                filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
        
        return filepath
    
    def generate_dashboard(self, df: pd.DataFrame, title: str = "Dashboard",
                          filename: str = None) -> str:
        """Generate a comprehensive dashboard with multiple charts"""
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        charts = []
        
        # Summary statistics as text
        if len(numeric_cols) > 0:
            summary_stats = df[numeric_cols].describe()
            stats_text = f"Dataset Summary: {len(df)} rows, {len(df.columns)} columns"
            
        # Distribution histogram
        if len(numeric_cols) > 0:
            hist_chart = alt.Chart(df).mark_bar().encode(
                x=alt.X(f'{numeric_cols[0]}:Q', bin=True, title=numeric_cols[0].title()),
                y=alt.Y('count()', title='Count'),
                tooltip=['count()']
            ).properties(
                title=f"Distribution of {numeric_cols[0]}",
                width=280,
                height=200
            )
            charts.append(hist_chart)
        
        # Correlation heatmap (simplified)
        if len(numeric_cols) > 1:
            # Select top 5 numeric columns for heatmap to avoid overcrowding
            top_numeric = list(numeric_cols[:5])
            corr_subset = df[top_numeric].corr()
            corr_long = corr_subset.reset_index().melt(id_vars='index')
            corr_long.columns = ['Variable1', 'Variable2', 'Correlation']
            
            heatmap_chart = alt.Chart(corr_long).mark_rect().encode(
                x=alt.X('Variable1:O', title=''),
                y=alt.Y('Variable2:O', title=''),
                color=alt.Color('Correlation:Q', 
                              scale=alt.Scale(scheme='redblue', domain=[-1, 1]),
                              title='Correlation'),
                tooltip=['Variable1', 'Variable2', alt.Tooltip('Correlation:Q', format='.2f')]
            ).properties(
                title="Correlation Matrix",
                width=280,
                height=200
            )
            charts.append(heatmap_chart)
        
        # Time series or scatter plot
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            # Time series
            time_chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X(f'{datetime_cols[0]}:T', title=datetime_cols[0].title()),
                y=alt.Y(f'{numeric_cols[0]}:Q', title=numeric_cols[0].title()),
                tooltip=[datetime_cols[0], numeric_cols[0]]
            ).properties(
                title="Time Series",
                width=280,
                height=200
            )
            charts.append(time_chart)
        elif len(numeric_cols) >= 2:
            # Scatter plot
            scatter_chart = alt.Chart(df).mark_circle().encode(
                x=alt.X(f'{numeric_cols[0]}:Q', title=numeric_cols[0].title()),
                y=alt.Y(f'{numeric_cols[1]}:Q', title=numeric_cols[1].title()),
                tooltip=[numeric_cols[0], numeric_cols[1]]
            ).properties(
                title="Scatter Plot",
                width=280,
                height=200
            )
            charts.append(scatter_chart)
        
        # Categorical analysis
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            # Limit categories to top 10 to avoid overcrowding
            top_categories = df[categorical_cols[0]].value_counts().head(10).index
            df_subset = df[df[categorical_cols[0]].isin(top_categories)]
            
            cat_chart = alt.Chart(df_subset).mark_bar().encode(
                x=alt.X(f'{categorical_cols[0]}:O', title=categorical_cols[0].title()),
                y=alt.Y(f'mean({numeric_cols[0]}):Q', title=f'Avg {numeric_cols[0]}'),
                tooltip=[categorical_cols[0], f'mean({numeric_cols[0]}):Q']
            ).properties(
                title=f"Average {numeric_cols[0]} by {categorical_cols[0]}",
                width=280,
                height=200
            )
            charts.append(cat_chart)
        
        # Combine charts into dashboard
        if len(charts) >= 4:
            # 2x2 grid
            dashboard = alt.vconcat(
                alt.hconcat(charts[0], charts[1]),
                alt.hconcat(charts[2], charts[3])
            ).resolve_scale(
                color='independent'
            ).properties(
                title=title
            )
        elif len(charts) >= 2:
            # 1x2 or 2x1 grid
            dashboard = alt.hconcat(*charts[:2]).resolve_scale(
                color='independent'
            ).properties(
                title=title
            )
        elif len(charts) == 1:
            dashboard = charts[0].properties(title=title)
        else:
            # Create a simple text chart if no data suitable for visualization
            dashboard = alt.Chart(pd.DataFrame({'text': ['No suitable data for visualization']})).mark_text(
                align='center',
                baseline='middle',
                fontSize=16
            ).encode(
                text='text:N'
            ).properties(
                title=title,
                width=400,
                height=300
            )
        
        if not filename:
            filename = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        filepath = os.path.join(self.output_dir, filename)
        dashboard.save(filepath)
        
        return filepath
    
    def auto_chart_suggestion(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Automatically suggest the best chart types based on data characteristics"""
        
        suggestions = {
            "data_summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
                "categorical_columns": list(df.select_dtypes(include=['object']).columns),
                "datetime_columns": list(df.select_dtypes(include=['datetime64']).columns)
            },
            "recommended_charts": []
        }
        
        numeric_cols = suggestions["data_summary"]["numeric_columns"]
        categorical_cols = suggestions["data_summary"]["categorical_columns"]
        datetime_cols = suggestions["data_summary"]["datetime_columns"]
        
        # Time series analysis
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            suggestions["recommended_charts"].append({
                "type": "line_chart",
                "reason": "Time series data detected",
                "x_column": datetime_cols[0],
                "y_column": numeric_cols[0],
                "priority": "high"
            })
        
        # Categorical analysis
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            suggestions["recommended_charts"].append({
                "type": "bar_chart",
                "reason": "Categorical data with numeric values",
                "x_column": categorical_cols[0],
                "y_column": numeric_cols[0],
                "priority": "high"
            })
            
            # Pie chart for proportions
            if len(df[categorical_cols[0]].unique()) <= 10:
                suggestions["recommended_charts"].append({
                    "type": "pie_chart",
                    "reason": "Few categories suitable for pie chart",
                    "label_column": categorical_cols[0],
                    "value_column": numeric_cols[0],
                    "priority": "medium"
                })
        
        # Correlation analysis
        if len(numeric_cols) >= 2:
            suggestions["recommended_charts"].append({
                "type": "scatter_plot",
                "reason": "Multiple numeric columns for correlation analysis",
                "x_column": numeric_cols[0],
                "y_column": numeric_cols[1],
                "priority": "medium"
            })
            
            suggestions["recommended_charts"].append({
                "type": "heatmap",
                "reason": "Correlation matrix visualization",
                "priority": "medium"
            })
        
        # Dashboard for comprehensive analysis
        if len(df.columns) >= 3:
            suggestions["recommended_charts"].append({
                "type": "dashboard",
                "reason": "Multiple columns suitable for comprehensive dashboard",
                "priority": "high"
            })
        
        return suggestions


def generate_chart_from_dax_results(dax_results: Dict, chart_type: str, 
                                   output_dir: str = "output", **kwargs) -> Dict[str, Any]:
    """
    Main function to generate charts from DAX query results
    
    Args:
        dax_results: Results from DAX query execution
        chart_type: Type of chart ('line', 'bar', 'pie', 'scatter', 'heatmap', 'dashboard', 'auto')
        output_dir: Output directory for generated charts
        **kwargs: Additional parameters for chart generation
    
    Returns:
        Dictionary with chart generation results
    """
    
    try:
        generator = ChartGenerator(output_dir)
        df = generator.process_dax_results(dax_results)
        
        result = {
            "success": True,
            "data_summary": {
                "rows": len(df),
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict()
            }
        }
        
        if chart_type == "auto":
            # Auto-suggest and generate recommended charts
            suggestions = generator.auto_chart_suggestion(df)
            result["suggestions"] = suggestions
            
            generated_charts = []
            for suggestion in suggestions["recommended_charts"][:3]:  # Generate top 3 suggestions
                try:
                    if suggestion["type"] == "line_chart":
                        filepath = generator.generate_line_chart(
                            df, suggestion["x_column"], suggestion["y_column"],
                            title=f"Auto-generated {suggestion['type'].title()}",
                            **kwargs
                        )
                    elif suggestion["type"] == "bar_chart":
                        filepath = generator.generate_bar_chart(
                            df, suggestion["x_column"], suggestion["y_column"],
                            title=f"Auto-generated {suggestion['type'].title()}",
                            **kwargs
                        )
                    elif suggestion["type"] == "pie_chart":
                        filepath = generator.generate_pie_chart(
                            df, suggestion["label_column"], suggestion["value_column"],
                            title=f"Auto-generated {suggestion['type'].title()}",
                            **kwargs
                        )
                    elif suggestion["type"] == "scatter_plot":
                        filepath = generator.generate_scatter_plot(
                            df, suggestion["x_column"], suggestion["y_column"],
                            title=f"Auto-generated {suggestion['type'].title()}",
                            **kwargs
                        )
                    elif suggestion["type"] == "heatmap":
                        filepath = generator.generate_heatmap(
                            df, title=f"Auto-generated {suggestion['type'].title()}",
                            **kwargs
                        )
                    elif suggestion["type"] == "dashboard":
                        # Dashboard method has specific parameters
                        dashboard_kwargs = {"title": f"Auto-generated {suggestion['type'].title()}"}
                        if "filename" in kwargs:
                            dashboard_kwargs["filename"] = kwargs["filename"]
                        filepath = generator.generate_dashboard(df, **dashboard_kwargs)
                    
                    generated_charts.append({
                        "type": suggestion["type"],
                        "filepath": filepath,
                        "reason": suggestion["reason"]
                    })
                    
                except Exception as e:
                    generated_charts.append({
                        "type": suggestion["type"],
                        "error": str(e),
                        "reason": suggestion["reason"]
                    })
            
            result["generated_charts"] = generated_charts
            
        else:
            # Generate specific chart type
            if chart_type == "line":
                x_col = kwargs.get("x_column") or df.columns[0]
                y_col = kwargs.get("y_column") or df.columns[1]
                filepath = generator.generate_line_chart(df, x_col, y_col, **kwargs)
                
            elif chart_type == "bar":
                x_col = kwargs.get("x_column") or df.columns[0]
                y_col = kwargs.get("y_column") or df.columns[1]
                filepath = generator.generate_bar_chart(df, x_col, y_col, **kwargs)
                
            elif chart_type == "pie":
                label_col = kwargs.get("label_column") or df.columns[0]
                value_col = kwargs.get("value_column") or df.columns[1]
                filepath = generator.generate_pie_chart(df, label_col, value_col, **kwargs)
                
            elif chart_type == "scatter":
                x_col = kwargs.get("x_column") or df.columns[0]
                y_col = kwargs.get("y_column") or df.columns[1]
                filepath = generator.generate_scatter_plot(df, x_col, y_col, **kwargs)
                
            elif chart_type == "heatmap":
                filepath = generator.generate_heatmap(df, **kwargs)
                
            elif chart_type == "dashboard":
                # Dashboard method has specific parameters
                dashboard_kwargs = {}
                if "title" in kwargs:
                    dashboard_kwargs["title"] = kwargs["title"]
                if "filename" in kwargs:
                    dashboard_kwargs["filename"] = kwargs["filename"]
                filepath = generator.generate_dashboard(df, **dashboard_kwargs)
                
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            result["generated_chart"] = {
                "type": chart_type,
                "filepath": filepath
            }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test with sample data
    sample_data = {
        "success": True,
        "columns": [
            {"name": "Date", "index": 0},
            {"name": "Sales", "index": 1},
            {"name": "Category", "index": 2}
        ],
        "rows": [
            {"Date": "2024-01-01", "Sales": 1000, "Category": "A"},
            {"Date": "2024-01-02", "Sales": 1200, "Category": "B"},
            {"Date": "2024-01-03", "Sales": 800, "Category": "A"},
        ]
    }
    
    result = generate_chart_from_dax_results(sample_data, "auto")
    print(json.dumps(result, indent=2, default=str))
