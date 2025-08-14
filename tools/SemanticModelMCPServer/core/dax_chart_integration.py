"""
DAX Query Executor with Chart Generation Integration
Handles DAX query execution and integrates with chart generation
"""

import json
from typing import Dict, Any
import sys
import os

# Add the tools directory to the path for chart generator import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

try:
    from chart_generator import generate_chart_from_dax_results
except ImportError:
    # Fallback if chart generator is not available
    def generate_chart_from_dax_results(*args, **kwargs):
        return {"success": False, "error": "Chart generator not available"}


def execute_dax_query_with_charts(dax_results: Dict, chart_type: str = "auto",
                                 output_dir: str = "output", **kwargs) -> Dict[str, Any]:
    """
    Execute DAX query and generate charts from results
    
    Args:
        dax_results: Results from DAX query execution
        chart_type: Type of chart to generate
        output_dir: Output directory for charts
        **kwargs: Additional chart parameters
    
    Returns:
        Combined results with charts
    """
    
    try:
        if not dax_results.get('success', False):
            return {
                "success": False,
                "error": "DAX query execution failed",
                "dax_results": dax_results
            }
        
        # Generate charts from the DAX results
        chart_results = generate_chart_from_dax_results(
            dax_results, chart_type, output_dir, **kwargs
        )
        
        return {
            "success": True,
            "dax_results": dax_results,
            "chart_results": chart_results,
            "output_directory": output_dir
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "dax_results": dax_results
        }


def analyze_query_results_for_charts(dax_results: Dict) -> Dict[str, Any]:
    """
    Analyze DAX query results to suggest appropriate chart types
    
    Args:
        dax_results: Results from DAX query execution
    
    Returns:
        Analysis and chart suggestions
    """
    
    try:
        if not dax_results.get('success', False):
            return {
                "success": False,
                "error": "Invalid DAX results provided"
            }
        
        columns = dax_results.get('columns', [])
        rows = dax_results.get('rows', [])
        
        analysis = {
            "success": True,
            "data_summary": {
                "total_rows": len(rows),
                "total_columns": len(columns),
                "column_names": [col['name'].split('[')[-1].rstrip(']') for col in columns]
            },
            "chart_suggestions": []
        }
        
        # Analyze column types and suggest charts
        numeric_columns = []
        text_columns = []
        date_columns = []
        
        # Sample first few rows to determine data types
        if rows:
            sample_row = rows[0]
            for col in columns:
                col_name = col['name']
                value = sample_row.get(col_name)
                
                clean_name = col_name.split('[')[-1].rstrip(']')
                
                if value is not None:
                    try:
                        # Try to convert to float
                        float(str(value).replace(',', ''))
                        numeric_columns.append(clean_name)
                    except (ValueError, TypeError):
                        # Check if it looks like a date
                        if any(date_keyword in str(value).lower() for date_keyword in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', '2024', '2025', '/']):
                            date_columns.append(clean_name)
                        else:
                            text_columns.append(clean_name)
        
        analysis["data_summary"]["numeric_columns"] = numeric_columns
        analysis["data_summary"]["text_columns"] = text_columns
        analysis["data_summary"]["date_columns"] = date_columns
        
        # Suggest chart types based on data characteristics
        if len(date_columns) > 0 and len(numeric_columns) > 0:
            analysis["chart_suggestions"].append({
                "type": "line",
                "reason": "Time series data detected",
                "x_column": date_columns[0],
                "y_column": numeric_columns[0],
                "priority": "high"
            })
        
        if len(text_columns) > 0 and len(numeric_columns) > 0:
            analysis["chart_suggestions"].append({
                "type": "bar",
                "reason": "Categorical data with numeric values",
                "x_column": text_columns[0],
                "y_column": numeric_columns[0],
                "priority": "high"
            })
            
            # Suggest pie chart if few categories
            unique_categories = len(set(row.get(columns[0]['name']) for row in rows[:100]))
            if unique_categories <= 10:
                analysis["chart_suggestions"].append({
                    "type": "pie",
                    "reason": f"Few categories ({unique_categories}) suitable for pie chart",
                    "label_column": text_columns[0],
                    "value_column": numeric_columns[0],
                    "priority": "medium"
                })
        
        if len(numeric_columns) >= 2:
            analysis["chart_suggestions"].append({
                "type": "scatter",
                "reason": "Multiple numeric columns for correlation analysis",
                "x_column": numeric_columns[0],
                "y_column": numeric_columns[1],
                "priority": "medium"
            })
        
        if len(columns) >= 3:
            analysis["chart_suggestions"].append({
                "type": "dashboard",
                "reason": "Multiple columns suitable for comprehensive dashboard",
                "priority": "high"
            })
        
        return analysis
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_chart_report(chart_results: Dict, title: str = "Chart Generation Report") -> str:
    """
    Create a markdown report for generated charts
    
    Args:
        chart_results: Results from chart generation
        title: Report title
    
    Returns:
        Markdown report content
    """
    
    report = f"""# {title}
**Generated on:** {chart_results.get('timestamp', 'Unknown')}

## Chart Generation Summary

"""
    
    if chart_results.get('success', False):
        report += "✅ **Status:** Successful\n\n"
        
        if 'suggestions' in chart_results:
            suggestions = chart_results['suggestions']
            report += f"### Data Summary\n"
            report += f"- **Total Rows:** {suggestions['data_summary']['total_rows']}\n"
            report += f"- **Total Columns:** {suggestions['data_summary']['total_columns']}\n"
            report += f"- **Numeric Columns:** {len(suggestions['data_summary']['numeric_columns'])}\n"
            report += f"- **Categorical Columns:** {len(suggestions['data_summary']['categorical_columns'])}\n"
            report += f"- **DateTime Columns:** {len(suggestions['data_summary']['datetime_columns'])}\n\n"
            
            report += "### Recommended Charts\n"
            for i, chart in enumerate(suggestions['recommended_charts'], 1):
                report += f"{i}. **{chart['type'].title().replace('_', ' ')}** - {chart['reason']} (Priority: {chart['priority']})\n"
            report += "\n"
        
        if 'generated_charts' in chart_results:
            report += "### Generated Charts\n"
            for chart in chart_results['generated_charts']:
                if 'filepath' in chart:
                    report += f"- **{chart['type'].title().replace('_', ' ')}:** `{chart['filepath']}`\n"
                    report += f"  - Reason: {chart.get('reason', 'N/A')}\n"
                elif 'error' in chart:
                    report += f"- **{chart['type'].title().replace('_', ' ')}:** ❌ Error - {chart['error']}\n"
            report += "\n"
        
        if 'generated_chart' in chart_results:
            chart = chart_results['generated_chart']
            report += f"### Generated Chart\n"
            report += f"- **Type:** {chart['type'].title()}\n"
            report += f"- **File:** `{chart['filepath']}`\n\n"
    
    else:
        report += f"❌ **Status:** Failed\n"
        report += f"**Error:** {chart_results.get('error', 'Unknown error')}\n\n"
    
    report += "---\n*Generated by Semantic Model MCP Server Chart Generator*"
    
    return report
