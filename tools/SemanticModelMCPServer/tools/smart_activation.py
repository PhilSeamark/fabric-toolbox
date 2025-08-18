"""
Smart Tool Activation System for Semantic Model MCP Server
Automatically activates required tool categories based on user requests
"""

import json
import logging
from typing import Dict, List, Set

class SmartActivationManager:
    """Manages automatic tool activation based on user context and requests"""
    
    def __init__(self):
        self.activated_tools: Set[str] = set()
        self.tool_mappings = self._initialize_tool_mappings()
        
    def _initialize_tool_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize the mapping of keywords to tool categories"""
        return {
            "bpa": {
                "category": "powerbi_analysis_tools",
                "keywords": ["bpa", "best practice", "analyze", "violations", "rules", "analysis"],
                "tools": [
                    "analyze_model_bpa",
                    "analyze_tmsl_bpa", 
                    "generate_bpa_report",
                    "get_bpa_violations_by_severity",
                    "get_bpa_violations_by_category",
                    "get_bpa_rules_summary",
                    "get_bpa_categories"
                ]
            },
            "charts": {
                "category": "powerbi_dashboard_creation",
                "keywords": ["chart", "dashboard", "visualization", "graph", "plot", "dash"],
                "tools": [
                    "generate_chart_from_dax_results",
                    "analyze_dax_results_for_charts",
                    "execute_dax_with_visualization",
                    "create_comprehensive_dashboard",
                    "list_active_dashboards",
                    "stop_dashboard"
                ]
            },
            "powerbi_service": {
                "category": "powerbi_and_lakehouse_tools",
                "keywords": ["workspace", "dataset", "powerbi service", "cloud", "fabric"],
                "tools": [
                    "list_powerbi_workspaces",
                    "list_powerbi_datasets",
                    "execute_dax_query",
                    "get_powerbi_workspace_id",
                    "list_fabric_lakehouses",
                    "list_fabric_delta_tables"
                ]
            },
            "local_powerbi": {
                "category": "powerbi_local_development", 
                "keywords": ["local", "desktop", "powerbi desktop", "detect", "local powerbi"],
                "tools": [
                    "detect_local_powerbi_desktop",
                    "explore_local_powerbi_tables",
                    "explore_local_powerbi_columns",
                    "explore_local_powerbi_measures",
                    "execute_local_powerbi_dax"
                ]
            },
            "tom": {
                "category": "powerbi_tom_management",
                "keywords": ["tom", "tabular object model", "add measure", "create table", "relationships"],
                "tools": [
                    "tom_add_measure_to_powerbi_service",
                    "tom_add_table_to_semantic_model",
                    "tom_add_relationship_to_semantic_model",
                    "tom_create_empty_model_with_auth",
                    "tom_refresh_powerbi_service_model"
                ]
            },
            "tmsl": {
                "category": "powerbi_tmsl_management",
                "keywords": ["tmsl", "tabular model scripting", "model definition", "directlake"],
                "tools": [
                    "update_model_using_tmsl",
                    "generate_directlake_tmsl_template",
                    "get_model_definition",
                    "get_local_powerbi_tmsl_definition"
                ]
            },
            "lakehouse": {
                "category": "powerbi_lakehouse_management",
                "keywords": ["lakehouse", "delta table", "sql endpoint", "fabric lakehouse"],
                "tools": [
                    "list_fabric_lakehouses",
                    "list_fabric_delta_tables",
                    "query_lakehouse_sql_endpoint",
                    "get_lakehouse_sql_connection_string"
                ]
            }
        }
    
    def detect_required_activation(self, user_input: str) -> List[str]:
        """Detect which tool categories should be activated based on user input"""
        user_input_lower = user_input.lower()
        required_categories = []
        
        for category_key, config in self.tool_mappings.items():
            for keyword in config["keywords"]:
                if keyword in user_input_lower:
                    category = config["category"]
                    if category not in required_categories:
                        required_categories.append(category)
                    break
        
        return required_categories
    
    def generate_activation_command(self, categories: List[str]) -> str:
        """Generate the appropriate activation command"""
        if not categories:
            return ""
        
        if len(categories) == 1:
            return f"activate_{categories[0]}"
        else:
            # Multiple categories - suggest the most comprehensive one
            if "powerbi_and_lakehouse_tools" in categories:
                return "activate_powerbi_and_lakehouse_tools"
            else:
                return f"activate_{categories[0]}"
    
    def get_helpful_message(self, user_input: str) -> str:
        """Generate a helpful message with activation suggestions"""
        required_categories = self.detect_required_activation(user_input)
        
        if not required_categories:
            return """
🔧 **Tool Activation Helper**

It looks like you're trying to use semantic model tools. Here are the main activation commands:

**For BPA Analysis**: `activate_powerbi_analysis_tools`
**For Charts/Dashboards**: `activate_powerbi_dashboard_creation` 
**For Power BI Service**: `activate_powerbi_and_lakehouse_tools`
**For Local Power BI**: `activate_powerbi_local_development`
**For Model Creation (TOM)**: `activate_powerbi_tom_management`
**For TMSL Operations**: `activate_powerbi_tmsl_management`

Use the activation command first, then try your request again!
"""
        
        activation_cmd = self.generate_activation_command(required_categories)
        tool_list = []
        
        for category in required_categories:
            for config in self.tool_mappings.values():
                if config["category"] == category:
                    tool_list.extend(config["tools"][:3])  # Show first 3 tools
                    break
        
        return f"""
🚨 **Tools Need Activation!**

Based on your request, you need to activate: **{activation_cmd}**

**Detected categories**: {', '.join(required_categories)}
**Available tools after activation**: {', '.join(tool_list)}{'...' if len(tool_list) >= 3 else ''}

**Quick fix**: Run this command first:
```
{activation_cmd}
```

Then try your original request again!
"""

# Global instance
smart_activation = SmartActivationManager()

def create_smart_activation_tool():
    """Create a smart activation tool that can auto-detect and activate based on context"""
    
    def smart_activate_tools(user_request: str = "", auto_detect: bool = True) -> str:
        """
        Smart tool activation based on user request context.
        
        Args:
            user_request: The user's request to analyze for required tools
            auto_detect: Whether to auto-detect required categories
        
        Returns:
            JSON response with activation results and suggestions
        """
        
        if not user_request and not auto_detect:
            return json.dumps({
                "status": "info",
                "message": "Please provide a user request for context-based activation",
                "available_activations": [
                    "activate_powerbi_analysis_tools (BPA)",
                    "activate_powerbi_dashboard_creation (Charts)", 
                    "activate_powerbi_and_lakehouse_tools (Power BI Service)",
                    "activate_powerbi_local_development (Local Power BI)",
                    "activate_powerbi_tom_management (Model Creation)",
                    "activate_powerbi_tmsl_management (TMSL Operations)",
                    "activate_powerbi_lakehouse_management (Lakehouses)"
                ]
            }, indent=2)
        
        if auto_detect and user_request:
            required_categories = smart_activation.detect_required_activation(user_request)
            
            if required_categories:
                activation_cmd = smart_activation.generate_activation_command(required_categories)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Auto-detected required tool activation: {activation_cmd}",
                    "detected_categories": required_categories,
                    "recommended_command": activation_cmd,
                    "next_step": f"Run '{activation_cmd}' then retry your original request"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "info", 
                    "message": "No specific tool category detected from your request",
                    "suggestion": "Try being more specific about what you want to do (BPA analysis, charts, Power BI, etc.)"
                }, indent=2)
        
        return json.dumps({
            "status": "info",
            "message": "Smart activation ready",
            "usage": "Provide your request text for automatic tool detection and activation suggestions"
        }, indent=2)
    
    return smart_activate_tools

def generate_enhanced_error_message(tool_name: str, original_error: str) -> str:
    """Generate enhanced error messages with activation hints"""
    
    # Map common tool names to activation commands
    activation_map = {
        "analyze_model_bpa": "activate_powerbi_analysis_tools",
        "analyze_tmsl_bpa": "activate_powerbi_analysis_tools", 
        "generate_bpa_report": "activate_powerbi_analysis_tools",
        "generate_chart_from_dax_results": "activate_powerbi_dashboard_creation",
        "execute_dax_with_visualization": "activate_powerbi_dashboard_creation",
        "list_powerbi_workspaces": "activate_powerbi_and_lakehouse_tools",
        "execute_dax_query": "activate_powerbi_and_lakehouse_tools",
        "detect_local_powerbi_desktop": "activate_powerbi_local_development",
        "tom_add_measure": "activate_powerbi_tom_management",
        "update_model_using_tmsl": "activate_powerbi_tmsl_management"
    }
    
    # Find matching activation command
    activation_cmd = None
    for tool_pattern, cmd in activation_map.items():
        if tool_pattern in tool_name:
            activation_cmd = cmd
            break
    
    if activation_cmd:
        return f"""
🚨 **Tool Activation Required!**

**Error**: {original_error}

**Quick Fix**: The tool '{tool_name}' requires activation. Run this command first:

```
{activation_cmd}
```

Then try your original request again!

**Why this happens**: The Semantic Model MCP Server uses modular tool activation for better performance and organization.
"""
    else:
        return f"""
🚨 **Tool Not Available**

**Error**: {original_error}

**Suggestion**: Try activating the appropriate tool category first:
- For BPA: `activate_powerbi_analysis_tools`
- For Charts: `activate_powerbi_dashboard_creation`  
- For Power BI Service: `activate_powerbi_and_lakehouse_tools`
- For Local Power BI: `activate_powerbi_local_development`
- For Model Operations: `activate_powerbi_tom_management`
- For TMSL: `activate_powerbi_tmsl_management`
"""
