"""
Dash Dashboard Tools for MCP Server
MCP server tool definitions for interactive Dash dashboards
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the tools directory to the path
sys.path.append(os.path.dirname(__file__))

try:
    from dash_dashboard_generator import (
        create_weight_dashboard,
        create_dax_dashboard, 
        list_active_dashboards,
        stop_dashboard,
        dashboard_manager
    )
except ImportError as e:
    print(f"Warning: Could not import dash dashboard generator: {e}")
    # Fallback functions
    def create_weight_dashboard(data, **kwargs):
        return {"success": False, "error": "Dash not available"}
    def create_dax_dashboard(data, **kwargs):
        return {"success": False, "error": "Dash not available"}
    def list_active_dashboards():
        return []
    def stop_dashboard(dashboard_id):
        return False

def register_dash_tools(mcp):
    """Register all Dash dashboard tools with the MCP server"""
    
    @mcp.tool("create_interactive_weight_dashboard")
    def create_interactive_weight_dashboard_tool(
        dax_results: str,
        title: str = "Weight Tracking Dashboard",
        theme: str = "default"
    ) -> str:
        """
        Creates an interactive Dash web application for weight tracking visualization.
        
        This tool creates a comprehensive, interactive dashboard featuring:
        - Interactive line charts with zoom/pan capabilities
        - Summary statistics cards (starting weight, current weight, total loss, average daily loss)
        - Date range filtering
        - Daily weight change bar chart
        - Cumulative weight loss visualization
        - Data table with recent readings
        - Trend line analysis
        - Professional styling and responsive design
        
        The dashboard runs as a live web application accessible via browser.
        
        Args:
            dax_results: JSON string containing DAX query results with weight data
            title: Custom title for the dashboard
            theme: Dashboard theme ('default', 'dark', 'light')
        
        Returns:
            JSON string with dashboard creation status, URL, and access information
        """
        try:
            # Parse DAX results
            if isinstance(dax_results, str):
                data = json.loads(dax_results)
            else:
                data = dax_results
            
            # Create the dashboard
            result = create_weight_dashboard(
                data, 
                title=title,
                theme=theme
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to create weight tracking dashboard"
            }, indent=2)
    
    @mcp.tool("launch_dax_analysis_dashboard")
    def launch_dax_analysis_dashboard_tool(
        dax_results: str,
        chart_types: List[str] = ["line", "bar"],
        title: str = "DAX Analysis Dashboard"
    ) -> str:
        """
        Creates an interactive Dash dashboard for general DAX query analysis and visualization.
        
        Features:
        - Multiple chart types (line, bar, scatter, heatmap, pie)
        - Dynamic data filtering and sorting
        - Export capabilities (PNG, PDF, CSV)
        - Real-time data refresh options
        - Drill-down analytics
        - Statistical summaries
        
        Args:
            dax_results: JSON string containing DAX query results
            chart_types: List of chart types to include ["line", "bar", "scatter", "pie", "heatmap"]
            title: Custom title for the dashboard
        
        Returns:
            JSON string with dashboard launch information
        """
        try:
            if isinstance(dax_results, str):
                data = json.loads(dax_results)
            else:
                data = dax_results
            
            result = create_dax_dashboard(
                data,
                chart_types=chart_types,
                title=title
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to create DAX analysis dashboard"
            }, indent=2)
    
    @mcp.tool("execute_dax_with_dashboard")
    def execute_dax_with_dashboard_tool(
        connection_string: str,
        dax_query: str,
        dashboard_type: str = "weight_tracking",
        auto_launch: bool = True,
        dashboard_title: str = "Power BI Data Dashboard"
    ) -> str:
        """
        Executes a DAX query against a Power BI model and immediately creates an interactive dashboard.
        
        This tool combines DAX execution with dashboard creation for seamless data-to-visualization workflow.
        Perfect for rapid prototyping and data exploration.
        
        Args:
            connection_string: Connection string to Power BI Desktop or Service
            dax_query: DAX query to execute
            dashboard_type: Type of dashboard ("weight_tracking", "dax_analysis", "multi_chart", "business_intelligence")
            auto_launch: Whether to automatically open dashboard in browser
            dashboard_title: Custom title for the dashboard
        
        Returns:
            JSON string with DAX execution results and dashboard information
        """
        try:
            # Import the DAX execution function
            from local_powerbi_explorer import execute_local_dax_query
            
            # Execute DAX query
            dax_result = execute_local_dax_query(connection_string, dax_query)
            
            if not dax_result.get("success"):
                return json.dumps({
                    "success": False,
                    "error": "DAX query failed",
                    "dax_error": dax_result.get("error", "Unknown error"),
                    "message": "Could not execute DAX query"
                }, indent=2)
            
            # Create appropriate dashboard
            if dashboard_type == "weight_tracking":
                dashboard_result = create_weight_dashboard(dax_result, title=dashboard_title)
            else:
                dashboard_result = create_dax_dashboard(dax_result, title=dashboard_title)
            
            # Combine results
            combined_result = {
                "success": True,
                "dax_execution": {
                    "query": dax_query,
                    "rows_returned": dax_result.get("total_rows", 0),
                    "columns": dax_result.get("columns", [])
                },
                "dashboard": dashboard_result,
                "message": f"DAX query executed and {dashboard_type} dashboard created successfully"
            }
            
            return json.dumps(combined_result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to execute DAX query with dashboard creation"
            }, indent=2)
    
    @mcp.tool("list_active_dashboards")
    def list_active_dashboards_tool() -> str:
        """
        Lists all currently running Dash dashboards.
        
        Returns information about:
        - Dashboard IDs and types
        - URLs and port numbers
        - Creation timestamps
        - Running time
        - Resource usage
        
        Returns:
            JSON string with list of active dashboards
        """
        try:
            dashboards = list_active_dashboards()
            
            return json.dumps({
                "success": True,
                "active_dashboards": dashboards,
                "total_count": len(dashboards),
                "message": f"Found {len(dashboards)} active dashboard(s)"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to list active dashboards"
            }, indent=2)
    
    @mcp.tool("stop_dashboard")
    def stop_dashboard_tool(dashboard_id: str) -> str:
        """
        Stops a specific running dashboard by ID.
        
        Args:
            dashboard_id: The ID of the dashboard to stop (from list_active_dashboards)
        
        Returns:
            JSON string with stop operation status
        """
        try:
            success = stop_dashboard(dashboard_id)
            
            if success:
                return json.dumps({
                    "success": True,
                    "message": f"Dashboard {dashboard_id} stopped successfully"
                })
            else:
                return json.dumps({
                    "success": False,
                    "message": f"Dashboard {dashboard_id} not found or could not be stopped"
                })
                
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to stop dashboard {dashboard_id}"
            }, indent=2)
    
    @mcp.tool("create_comprehensive_bi_dashboard")
    def create_comprehensive_bi_dashboard_tool(
        workspace_name: str,
        dataset_name: str,
        dashboard_config: str = '{"charts": ["overview", "trends", "details"], "refresh_interval": 300}',
        title: str = "Business Intelligence Dashboard"
    ) -> str:
        """
        Creates a comprehensive Business Intelligence dashboard with multiple data sources and visualizations.
        
        Features:
        - Multiple chart types and KPI cards
        - Real-time data refresh from Power BI
        - Drill-down capabilities
        - Export functionality
        - Mobile-responsive design
        - Custom filtering and date ranges
        - Performance metrics and alerts
        
        Args:
            workspace_name: Power BI workspace name
            dataset_name: Power BI dataset name
            dashboard_config: JSON configuration for dashboard layout and features
            title: Dashboard title
        
        Returns:
            JSON string with comprehensive dashboard creation status
        """
        try:
            # This would integrate with the semantic model MCP tools
            config = json.loads(dashboard_config) if isinstance(dashboard_config, str) else dashboard_config
            
            result = dashboard_manager.create_dashboard(
                "business_intelligence",
                {
                    "workspace_name": workspace_name,
                    "dataset_name": dataset_name,
                    "config": config
                },
                title=title
            )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to create comprehensive BI dashboard"
            }, indent=2)

def get_dash_tools_info() -> Dict[str, Any]:
    """Get information about all available Dash tools"""
    return {
        "dash_tools": {
            "create_interactive_weight_dashboard": {
                "description": "Creates interactive weight tracking dashboard with advanced analytics",
                "features": ["Interactive charts", "Date filtering", "Statistics", "Trend analysis"],
                "suitable_for": ["Weight loss tracking", "Health monitoring", "Progress visualization"]
            },
            "launch_dax_analysis_dashboard": {
                "description": "General-purpose DAX analysis dashboard with multiple chart types",
                "features": ["Multiple chart types", "Data filtering", "Export capabilities", "Statistical analysis"],
                "suitable_for": ["Data exploration", "Business analytics", "Report generation"]
            },
            "execute_dax_with_dashboard": {
                "description": "Combined DAX execution and dashboard creation",
                "features": ["Seamless workflow", "Auto-launch", "Multiple dashboard types"],
                "suitable_for": ["Rapid prototyping", "Data exploration", "Quick visualizations"]
            },
            "create_comprehensive_bi_dashboard": {
                "description": "Enterprise-grade BI dashboard with real-time data",
                "features": ["Real-time refresh", "Multiple data sources", "KPI monitoring", "Mobile responsive"],
                "suitable_for": ["Business intelligence", "Executive dashboards", "Operational monitoring"]
            }
        },
        "advantages_over_static_charts": [
            "Real-time interactivity",
            "Live data refresh",
            "User-controlled filtering",
            "Drill-down capabilities",
            "Professional web application interface",
            "Mobile responsiveness",
            "Export and sharing capabilities",
            "Multi-user access"
        ]
    }
