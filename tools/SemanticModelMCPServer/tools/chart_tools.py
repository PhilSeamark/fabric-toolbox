"""
Chart Generation Tools for Semantic Model MCP Server
Provides tools for generating charts and visualizations from DAX query results
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional

# Add the tools directory to the path
sys.path.append(os.path.dirname(__file__))

try:
    from tools.dash_chart_generator import generate_chart_from_dax_results, DashChartGenerator
    from chart_generator import ChartGenerator  # Backward compatibility
    CHART_GENERATOR_AVAILABLE = True
except ImportError as e:
    CHART_GENERATOR_AVAILABLE = False
    print(f"Warning: Chart generator not available: {e}. Some features may be limited.")

from core.dax_chart_integration import (
    execute_dax_query_with_charts,
    analyze_query_results_for_charts,
    create_chart_report
)


def register_chart_tools(mcp):
    """Register chart generation tools with the MCP server"""
    
    @mcp.tool(
        name="generate_chart_from_dax_results",
        description="""
        Generate charts and visualizations from DAX query results.
        
        This tool takes DAX query results and automatically generates appropriate charts.
        Supports multiple chart types including line charts, bar charts, pie charts, scatter plots, heatmaps, and comprehensive dashboards.
        
        Args:
            dax_results: Results from a DAX query execution (JSON object)
            chart_type: Type of chart to generate ('auto', 'line', 'bar', 'pie', 'scatter', 'heatmap', 'dashboard')
            output_filename: Optional custom filename for the generated chart
            chart_title: Custom title for the chart
            interactive: Whether to generate interactive (HTML) or static (PNG) charts
            x_column: Specific column to use for X-axis (for specific chart types)
            y_column: Specific column to use for Y-axis (for specific chart types)
        
        Returns:
            JSON object with chart generation results including file paths and suggestions
        """
    )
    def generate_chart_from_dax_results_tool(
        dax_results: Dict[str, Any],
        chart_type: str = "auto",
        output_filename: Optional[str] = None,
        chart_title: Optional[str] = None,
        interactive: bool = True,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        title: Optional[str] = None  # Add backward compatibility for MCP framework
    ) -> Dict[str, Any]:
        """Generate charts from DAX query results"""
        
        if not CHART_GENERATOR_AVAILABLE:
            return {
                "success": False,
                "error": "Chart generator module not available. Please install required dependencies: pip install dash plotly pandas numpy"
            }
        
        try:
            # Handle both parameter names for title
            final_title = chart_title or title
            
            # Ensure output directory exists
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Build chart parameters
            chart_kwargs = {
                "interactive": interactive
            }
            
            if output_filename:
                chart_kwargs["output_filename"] = output_filename
            if final_title:
                chart_kwargs["chart_title"] = final_title
            if x_column:
                chart_kwargs["x_column"] = x_column
            if y_column:
                chart_kwargs["y_column"] = y_column
            
            # Generate chart
            result = generate_chart_from_dax_results(
                dax_results, chart_type, **chart_kwargs
            )
            
            # Create a summary report
            if result.get("success"):
                report_content = create_chart_report(result, chart_title or "Chart Generation Report")
                report_path = os.path.join(output_dir, f"chart_report_{chart_type}.md")
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                result["report_path"] = report_path
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool(
        name="analyze_dax_results_for_charts",
        description="""
        Analyze DAX query results to suggest appropriate chart types.
        
        This tool examines the structure and content of DAX query results to recommend
        the most suitable chart types for visualization.
        
        Args:
            dax_results: Results from a DAX query execution (JSON object)
        
        Returns:
            Analysis results with chart type suggestions and data characteristics
        """
    )
    def analyze_dax_results_for_charts_tool(dax_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DAX results and suggest chart types"""
        
        try:
            return analyze_query_results_for_charts(dax_results)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool(
        name="execute_dax_with_visualization",
        description="""
        Execute a DAX query against a Power BI model and automatically generate visualizations.
        
        This is a combined tool that executes a DAX query and immediately generates charts
        from the results. Perfect for quick data exploration and analysis.
        
        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to query
            dax_query: The DAX query to execute
            chart_types: List of chart types to generate (optional, uses auto-suggestion if not provided)
            auto_charts: Whether to automatically generate recommended charts
            chart_title: Custom title for the charts
            interactive: Whether to generate interactive charts
        
        Returns:
            Combined results with query data and generated charts
        """
    )
    def execute_dax_with_visualization_tool(
        workspace_name: str,
        dataset_name: str,
        dax_query: str,
        chart_types: Optional[List[str]] = None,
        auto_charts: bool = True,
        chart_title: Optional[str] = None,
        interactive: bool = True
    ) -> Dict[str, Any]:
        """Execute DAX query and generate visualizations"""
        
        try:
            # Import DAX execution function
            from tools.improved_dax_explorer import execute_dax_query
            
            # Execute DAX query first
            dax_results = execute_dax_query(workspace_name, dataset_name, dax_query)
            
            if not dax_results.get("success"):
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
            
            # Ensure output directory exists
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate charts if requested
            if auto_charts or chart_types:
                if auto_charts:
                    # Auto-generate recommended charts
                    chart_result = generate_chart_from_dax_results_tool(
                        dax_results, "auto", 
                        chart_title=chart_title or f"{dataset_name} Analysis",
                        interactive=interactive
                    )
                    result["charts"]["auto_generated"] = chart_result
                
                if chart_types:
                    # Generate specific chart types
                    result["charts"]["requested"] = {}
                    for chart_type in chart_types:
                        chart_result = generate_chart_from_dax_results_tool(
                            dax_results, chart_type,
                            chart_title=chart_title or f"{dataset_name} - {chart_type.title()} Chart",
                            interactive=interactive
                        )
                        result["charts"]["requested"][chart_type] = chart_result
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool(
        name="execute_local_dax_with_visualization", 
        description="""
        Execute a DAX query against a local Power BI Desktop instance and generate visualizations.
        
        This tool connects to a local Power BI Desktop instance, executes a DAX query,
        and automatically generates appropriate charts from the results.
        
        Args:
            connection_string: The connection string to the local Power BI Desktop instance (e.g., "Data Source=localhost:65304")
            dax_query: The DAX query to execute
            chart_types: List of specific chart types to generate (optional)
            auto_charts: Whether to automatically generate recommended charts
            chart_title: Custom title for the charts
            interactive: Whether to generate interactive charts
        
        Returns:
            Combined results with query data and generated charts
        """
    )
    def execute_local_dax_with_visualization_tool(
        connection_string: str,
        dax_query: str,
        chart_types: Optional[List[str]] = None,
        auto_charts: bool = True,
        chart_title: Optional[str] = None,
        interactive: bool = True
    ) -> Dict[str, Any]:
        """Execute DAX query against local Power BI and generate visualizations"""
        
        try:
            # Import local DAX execution function
            from tools.improved_dax_explorer import execute_dax_query_local
            
            # Execute DAX query first
            dax_results = execute_dax_query_local(connection_string, dax_query)
            
            if not dax_results.get("success"):
                return {
                    "success": False,
                    "error": f"Local DAX query failed: {dax_results.get('error', 'Unknown error')}",
                    "dax_results": dax_results
                }
            
            result = {
                "success": True,
                "connection_string": connection_string,
                "dax_results": dax_results,
                "charts": {}
            }
            
            # Ensure output directory exists
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate charts if requested
            if auto_charts or chart_types:
                if auto_charts:
                    # Auto-generate recommended charts
                    chart_result = generate_chart_from_dax_results_tool(
                        dax_results, "auto",
                        chart_title=chart_title or "Local Power BI Analysis",
                        interactive=interactive
                    )
                    result["charts"]["auto_generated"] = chart_result
                
                if chart_types:
                    # Generate specific chart types
                    result["charts"]["requested"] = {}
                    for chart_type in chart_types:
                        chart_result = generate_chart_from_dax_results_tool(
                            dax_results, chart_type,
                            chart_title=chart_title or f"Local Power BI - {chart_type.title()} Chart",
                            interactive=interactive
                        )
                        result["charts"]["requested"][chart_type] = chart_result
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool(
        name="create_comprehensive_dashboard",
        description="""
        Create a comprehensive dashboard with multiple visualizations from table data.
        
        This tool analyzes a table in the Power BI model and creates a multi-chart dashboard
        with various visualizations to provide comprehensive insights.
        
        Args:
            workspace_name: The Power BI workspace name (for cloud models)
            dataset_name: The dataset/model name
            table_name: The table to analyze
            connection_string: Connection string for local Power BI Desktop (optional, for local models)
            max_rows: Maximum number of rows to analyze (default: 1000)
            dashboard_title: Custom title for the dashboard
        
        Returns:
            Dashboard creation results with multiple chart files
        """
    )
    def create_comprehensive_dashboard_tool(
        table_name: str,
        workspace_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        max_rows: int = 1000,
        dashboard_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create comprehensive dashboard for a table"""
        
        try:
            # Determine if using local or cloud connection
            if connection_string:
                # Local Power BI Desktop
                from tools.improved_dax_explorer import execute_dax_query_local
                dax_query = f"EVALUATE TOPN({max_rows}, '{table_name}')"
                dax_results = execute_dax_query_local(connection_string, dax_query)
                source_info = f"Local Power BI Desktop ({connection_string})"
            
            elif workspace_name and dataset_name:
                # Power BI Service
                from tools.improved_dax_explorer import execute_dax_query
                dax_query = f"EVALUATE TOPN({max_rows}, '{table_name}')"
                dax_results = execute_dax_query(workspace_name, dataset_name, dax_query)
                source_info = f"Power BI Service ({workspace_name}/{dataset_name})"
            
            else:
                return {
                    "success": False,
                    "error": "Either connection_string (for local) or both workspace_name and dataset_name (for cloud) must be provided"
                }
            
            if not dax_results.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to query table {table_name}: {dax_results.get('error', 'Unknown error')}",
                    "dax_results": dax_results
                }
            
            # Generate comprehensive dashboard
            title = dashboard_title or f"{table_name} Comprehensive Dashboard"
            
            dashboard_result = generate_chart_from_dax_results_tool(
                dax_results, "dashboard",
                chart_title=title,
                interactive=True
            )
            
            # Also generate individual chart recommendations
            auto_result = generate_chart_from_dax_results_tool(
                dax_results, "auto",
                chart_title=f"{table_name} Auto-Generated Charts",
                interactive=True
            )
            
            return {
                "success": True,
                "table_name": table_name,
                "source_info": source_info,
                "rows_analyzed": len(dax_results.get("rows", [])),
                "dashboard": dashboard_result,
                "additional_charts": auto_result,
                "dax_query": dax_query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Helper function to install required dependencies
def install_chart_dependencies():
    """Install required packages for chart generation"""
    try:
        import subprocess
        import sys
        
        packages = ["dash", "plotly", "pandas", "numpy"]
        
        for package in packages:
            try:
                __import__(package)
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        return True
        
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        return False
