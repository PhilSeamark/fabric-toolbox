"""
Enhanced DAX Query Tool with Chart Generation
Combines DAX querying with automatic chart generation capabilities
"""

import json
from typing import Dict, List, Any, Optional
from .chart_generator import generate_chart_from_dax_results


def execute_dax_with_charts(connection_string: str, dax_query: str, 
                           chart_types: List[str] = None, auto_charts: bool = True,
                           output_dir: str = "output", **chart_kwargs) -> Dict[str, Any]:
    """
    Execute DAX query and automatically generate charts from the results
    
    Args:
        connection_string: Power BI connection string
        dax_query: DAX query to execute
        chart_types: List of specific chart types to generate
        auto_charts: Whether to auto-generate recommended charts
        output_dir: Output directory for charts
        **chart_kwargs: Additional chart generation parameters
    
    Returns:
        Combined results with query data and chart information
    """
    
    # Import here to avoid circular imports
    from ..core.dax_executor import execute_dax_query_local
    
    try:
        # Execute DAX query
        dax_results = execute_dax_query_local(connection_string, dax_query)
        
        if not dax_results.get('success', False):
            return {
                "success": False,
                "error": f"DAX query failed: {dax_results.get('error', 'Unknown error')}",
                "dax_results": dax_results
            }
        
        result = {
            "success": True,
            "dax_results": dax_results,
            "charts": {}
        }
        
        # Generate charts if requested
        if auto_charts or chart_types:
            if auto_charts:
                # Auto-generate recommended charts
                chart_result = generate_chart_from_dax_results(
                    dax_results, "auto", output_dir, **chart_kwargs
                )
                result["charts"]["auto_generated"] = chart_result
            
            if chart_types:
                # Generate specific chart types
                result["charts"]["requested"] = {}
                for chart_type in chart_types:
                    chart_result = generate_chart_from_dax_results(
                        dax_results, chart_type, output_dir, **chart_kwargs
                    )
                    result["charts"]["requested"][chart_type] = chart_result
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_model_with_charts(connection_string: str, table_name: str = None,
                             output_dir: str = "output") -> Dict[str, Any]:
    """
    Analyze a Power BI model and generate comprehensive charts
    
    Args:
        connection_string: Power BI connection string
        table_name: Specific table to analyze (optional)
        output_dir: Output directory for charts
    
    Returns:
        Analysis results with generated charts
    """
    
    try:
        result = {
            "success": True,
            "analysis": {},
            "charts": {}
        }
        
        # Get model structure
        from ..tools.local_powerbi_explorer import explore_model_structure
        structure = explore_model_structure(connection_string)
        result["analysis"]["model_structure"] = structure
        
        # If specific table, analyze it
        if table_name:
            # Get table data sample
            sample_query = f"EVALUATE TOPN(1000, '{table_name}')"
            chart_result = execute_dax_with_charts(
                connection_string, sample_query, 
                chart_types=["dashboard"], auto_charts=True,
                output_dir=output_dir,
                title=f"{table_name} Analysis Dashboard"
            )
            result["charts"][table_name] = chart_result
            
        else:
            # Analyze all tables
            if structure.get("success") and "tables" in structure:
                for table in structure["tables"][:5]:  # Limit to first 5 tables
                    table_name = table["name"]
                    try:
                        sample_query = f"EVALUATE TOPN(100, '{table_name}')"
                        chart_result = execute_dax_with_charts(
                            connection_string, sample_query,
                            chart_types=["auto"], auto_charts=True,
                            output_dir=output_dir,
                            title=f"{table_name} Analysis"
                        )
                        result["charts"][table_name] = chart_result
                    except Exception as e:
                        result["charts"][table_name] = {
                            "success": False,
                            "error": str(e)
                        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_custom_dashboard(connection_string: str, queries: Dict[str, str],
                           output_dir: str = "output", dashboard_title: str = "Custom Dashboard") -> Dict[str, Any]:
    """
    Create a custom dashboard with multiple DAX queries
    
    Args:
        connection_string: Power BI connection string
        queries: Dictionary of query_name: dax_query pairs
        output_dir: Output directory for dashboard
        dashboard_title: Title for the dashboard
    
    Returns:
        Dashboard creation results
    """
    
    try:
        result = {
            "success": True,
            "dashboard_title": dashboard_title,
            "queries": {},
            "summary": {
                "total_queries": len(queries),
                "successful_queries": 0,
                "failed_queries": 0,
                "generated_charts": 0
            }
        }
        
        for query_name, dax_query in queries.items():
            try:
                query_result = execute_dax_with_charts(
                    connection_string, dax_query,
                    auto_charts=True,
                    output_dir=output_dir,
                    title=f"{dashboard_title} - {query_name}"
                )
                
                result["queries"][query_name] = query_result
                
                if query_result.get("success"):
                    result["summary"]["successful_queries"] += 1
                    if "charts" in query_result:
                        result["summary"]["generated_charts"] += len(query_result["charts"])
                else:
                    result["summary"]["failed_queries"] += 1
                    
            except Exception as e:
                result["queries"][query_name] = {
                    "success": False,
                    "error": str(e)
                }
                result["summary"]["failed_queries"] += 1
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Predefined useful DAX queries for common analyses
COMMON_DAX_QUERIES = {
    "sales_trends": {
        "description": "Analyze sales trends over time",
        "query_template": "EVALUATE SUMMARIZE({table}, {date_column}, \"Total Sales\", SUM({amount_column}))",
        "chart_suggestions": ["line", "bar"]
    },
    
    "top_categories": {
        "description": "Find top performing categories",
        "query_template": "EVALUATE TOPN(10, SUMMARIZE({table}, {category_column}, \"Total\", SUM({amount_column})), [Total], DESC)",
        "chart_suggestions": ["bar", "pie"]
    },
    
    "monthly_summary": {
        "description": "Monthly performance summary",
        "query_template": "EVALUATE SUMMARIZE({table}, FORMAT({date_column}, \"YYYY-MM\"), \"Total\", SUM({amount_column}))",
        "chart_suggestions": ["line", "bar"]
    },
    
    "distribution_analysis": {
        "description": "Analyze value distribution",
        "query_template": "EVALUATE SUMMARIZE({table}, {group_column}, \"Count\", COUNTROWS({table}), \"Average\", AVERAGE({value_column}))",
        "chart_suggestions": ["scatter", "bar"]
    }
}


def suggest_dax_queries(table_structure: Dict) -> Dict[str, Any]:
    """
    Suggest useful DAX queries based on table structure
    
    Args:
        table_structure: Structure information of the table
    
    Returns:
        Dictionary of suggested queries
    """
    
    suggestions = {
        "success": True,
        "suggested_queries": [],
        "query_templates": COMMON_DAX_QUERIES
    }
    
    # This would analyze the table structure and suggest appropriate queries
    # For now, return the common templates
    
    return suggestions
