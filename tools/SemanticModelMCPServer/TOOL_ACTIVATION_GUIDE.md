# 🚀 Semantic Model MCP Server - Tool Activation Guide

## 🚨 **CRITICAL**: Always Activate Required Tools First

**MANDATORY RULE**: When using #semantic_model_mcp_server, ALWAYS activate the required tool categories BEFORE attempting to use any tools. Never assume tools are "disabled" - instead, proactively activate them.

## 🤖 **NEW: Smart Activation (Recommended)**

### Quick & Easy: Auto-Detection
```
smart_activate_tools("I want to run BPA analysis on my model")
smart_activate_tools("Create charts from my DAX query results") 
smart_activate_tools("Analyze my local Power BI Desktop model")
```

### One-Command Solution: Activate Everything
```
activate_all_powerbi_tools
```
This activates ALL tool categories at once. Use when you're not sure what you need.

## 📋 **Specific Tool Activation Commands**

### 🔍 **BPA Analysis Tools**
```
activate_powerbi_analysis_tools
```
**Use for**: Best Practice Analyzer, model validation, rule violations
**Tools unlocked**: analyze_model_bpa, analyze_tmsl_bpa, generate_bpa_report

### 📊 **Dashboard & Chart Tools** 
```
activate_powerbi_dashboard_creation
```
**Use for**: Creating charts, dashboards, visualizations from DAX results
**Tools unlocked**: generate_chart_from_dax_results, execute_dax_with_visualization

### ☁️ **Power BI Service & Lakehouse Tools**
```
activate_powerbi_and_lakehouse_tools
```
**Use for**: Cloud workspaces, datasets, DAX queries, Fabric lakehouses
**Tools unlocked**: list_powerbi_workspaces, execute_dax_query, list_fabric_lakehouses

### 💻 **Local Power BI Desktop Tools**
```
activate_powerbi_local_development
```
**Use for**: Local .pbix files, Power BI Desktop detection, local DAX queries
**Tools unlocked**: detect_local_powerbi_desktop, execute_local_powerbi_dax

### 🔧 **Model Creation Tools (TOM)**
```
activate_powerbi_tom_management
```
**Use for**: Creating measures, tables, relationships programmatically
**Tools unlocked**: tom_add_measure_to_powerbi_service, tom_create_empty_model_with_auth

### 📝 **TMSL & Model Definition Tools**
```
activate_powerbi_tmsl_management
```
**Use for**: Model definitions, TMSL operations, DirectLake models
**Tools unlocked**: update_model_using_tmsl, generate_directlake_tmsl_template

### 🏗️ **Lakehouse Management Tools**
```
activate_powerbi_lakehouse_management
```
**Use for**: Delta tables, SQL endpoints, lakehouse exploration
**Tools unlocked**: list_fabric_delta_tables, query_lakehouse_sql_endpoint

## 🔄 **Recommended Workflow**

### Method 1: Smart Detection (Easiest)
1. Use `smart_activate_tools("your request here")` to get specific activation advice
2. Run the suggested activation command
3. Execute your original request

### Method 2: Activate Everything (Fastest)
1. Run `activate_all_powerbi_tools` once at the start of your session
2. Use any tool without additional activation

### Method 3: Specific Activation (Most Efficient)
1. Identify what you want to do from the categories above
2. Run the specific activation command
3. Use the tools in that category

## 🚨 **Common Issues & Solutions**

### ❌ "Tools are disabled" Error
**Problem**: Tool category not activated
**Solution**: Run the appropriate activation command first

### ❌ "Tool not found" Error  
**Problem**: Wrong activation command or tool name
**Solution**: Use `smart_activate_tools("describe what you want to do")`

### ❌ "Cannot import module" Error
**Problem**: Dependencies not installed or paths incorrect
**Solution**: Check installation and restart MCP server

## 💡 **Pro Tips**

1. **Start every new chat session** with `activate_all_powerbi_tools` to avoid activation issues
2. **Use smart_activate_tools** when you're unsure which category you need
3. **Activation persists** within a session - you only need to activate once per category
4. **Multiple activations are safe** - you can run activation commands multiple times
5. **Check activation status** by trying to use a tool - if it works, it's activated

## 🎯 **Examples by Use Case**

### BPA Analysis
```
# Step 1: Activate
activate_powerbi_analysis_tools

# Step 2: Use
analyze_model_bpa("MyWorkspace", "MyDataset")
```

### Create Charts
```
# Step 1: Activate  
activate_powerbi_dashboard_creation

# Step 2: Use
execute_dax_with_visualization("MyWorkspace", "MyDataset", "EVALUATE Sales")
```

### Local Power BI
```
# Step 1: Activate
activate_powerbi_local_development  

# Step 2: Use
detect_local_powerbi_desktop()
```

### Model Creation
```
# Step 1: Activate
activate_powerbi_tom_management

# Step 2: Use  
tom_create_empty_model_with_auth("MyWorkspace", "NewModel")
```

## 📚 **Quick Reference**

| What you want to do | Activation Command | Key Tools |
|---------------------|-------------------|-----------|
| Analyze model quality | `activate_powerbi_analysis_tools` | analyze_model_bpa |
| Create charts/dashboards | `activate_powerbi_dashboard_creation` | execute_dax_with_visualization |
| Work with Power BI Service | `activate_powerbi_and_lakehouse_tools` | list_powerbi_workspaces |
| Use local Power BI Desktop | `activate_powerbi_local_development` | detect_local_powerbi_desktop |
| Create models/measures | `activate_powerbi_tom_management` | tom_add_measure_to_powerbi_service |
| Work with TMSL | `activate_powerbi_tmsl_management` | update_model_using_tmsl |
| Explore lakehouses | `activate_powerbi_lakehouse_management` | list_fabric_delta_tables |
| Everything at once | `activate_all_powerbi_tools` | All tools |
| Smart detection | `smart_activate_tools("your request")` | Auto-suggests activation |

Remember: **Activation first, then action!** 🚀
