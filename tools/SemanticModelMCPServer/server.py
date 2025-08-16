from fastmcp import FastMCP
import logging
import clr
import os
import json
import sys
from typing import List, Optional
from core.auth import get_access_token
from core.bpa_service import BPAService
from tools.fabric_metadata import list_workspaces, list_datasets, get_workspace_id, list_notebooks, list_delta_tables, list_lakehouses, list_lakehouse_files, get_lakehouse_sql_connection_string as fabric_get_lakehouse_sql_connection_string
from tools.bpa_tools import register_bpa_tools
from tools.powerbi_desktop_tools import register_powerbi_desktop_tools
from tools.microsoft_learn_tools import register_microsoft_learn_tools
from tools.chart_tools import register_chart_tools
import urllib.parse
from src.helper import count_nodes_with_name
from src.tmsl_validator import validate_tmsl_structure
import time
from datetime import datetime, timedelta
from prompts import register_prompts
from __version__ import __version__, __description__
import decimal

# Custom JSON encoder to handle .NET types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle .NET types that can't be directly serialized
        if str(type(obj)) == "<class 'System.Decimal'>":
            # Convert to Python Decimal, then to float for JSON compatibility
            return float(decimal.Decimal(str(obj)))
        elif str(type(obj)) == "<class 'System.Int64'>":
            return int(str(obj))
        elif str(type(obj)) == "<class 'System.Int32'>":
            return int(str(obj))
        elif str(type(obj)) == "<class 'System.Double'>":
            return float(str(obj))
        elif str(type(obj)) == "<class 'System.String'>":
            return str(obj)
        elif str(type(obj)) == "<class 'System.Boolean'>":
            return bool(obj)
        elif hasattr(obj, 'isoformat'):  # DateTime objects
            return obj.isoformat()
        # Handle Python decimal.Decimal objects
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)

# Try to import pyodbc - it's needed for SQL Analytics Endpoint queries
try:
    import pyodbc
except ImportError:
    pyodbc = None

mcp = FastMCP(
    name="Semantic Model MCP Server", 
    instructions="""
    A Model Context Protocol server for Microsoft Fabric and Power BI semantic models.
    
    ## Available Tools:
    - List Power BI Workspaces
    - List Power BI Datasets
    - List Power BI Notebooks
    - List Fabric Lakehouses
    - List Fabric Delta Tables
    - List Fabric Data Pipelines
    - Get Power BI Workspace ID
    - Get Model Definition
    - Execute DAX Queries
    - Update Model using TMSL (Enhanced with Validation)
    - Generate DirectLake TMSL Template (NEW)
    - Validate TMSL Structure (Built into update tool)
    - Search Microsoft Learn Content (NEW)
    - Get Microsoft Learn Learning Paths (NEW)
    - Get Microsoft Learn Modules (NEW)
    - Get Microsoft Learn Content by URL (NEW)
    - **🆕 Best Practice Analyzer (BPA) Tools (NEW)**
    - **🆕 Power BI Desktop Detection Tools (NEW)**
    - **🆕 Chart Generation and Visualization Tools (NEW)**
    - **🆕 Tabular Object Model (TOM) Tools (NEW)**

    ## 🆕 Best Practice Analyzer (BPA) Features:
    The server now includes a comprehensive Best Practice Analyzer that evaluates semantic models against industry best practices:
    
    **Available BPA Tools:**
    - `analyze_model_bpa` - Analyze a deployed model by workspace/dataset name
    - `analyze_tmsl_bpa` - Analyze TMSL definition directly (with enhanced JSON formatting and tidying)
    - `generate_bpa_report` - Generate comprehensive BPA reports
    - `get_bpa_violations_by_severity` - Filter violations by severity (INFO/WARNING/ERROR)
    - `get_bpa_violations_by_category` - Filter violations by category
    - `get_bpa_rules_summary` - Get overview of available BPA rules
    - `get_bpa_categories` - List all available categories and severities
    
    **BPA Rule Categories:**
    - **Performance** - Optimization recommendations for better query performance
    - **DAX Expressions** - Best practices for DAX syntax and patterns
    - **Maintenance** - Rules for model maintainability and documentation
    - **Naming Conventions** - Consistent naming standards
    - **Formatting** - Proper formatting and display properties
    
    **BPA Severity Levels:**
    - **ERROR (Level 3)** - Critical issues that should be fixed immediately
    - **WARNING (Level 2)** - Potential issues that should be addressed  
    - **INFO (Level 1)** - Suggestions for improvement
    
    **Example BPA Usage:**
    ```
    # Analyze a deployed model
    result = analyze_model_bpa("MyWorkspace", "MyDataset")
    
    # Generate detailed report
    report = generate_bpa_report("MyWorkspace", "MyDataset", "detailed")
    
    # Get only critical errors
    errors = get_bpa_violations_by_severity("ERROR")
    
    # Get performance-related issues
    perf_issues = get_bpa_violations_by_category("Performance")
    ```

    ## Microsoft Learn Research Capabilities (NEW):
    You now have access to Microsoft Learn documentation and research articles via the new MS Learn functions.
    Use these tools to research and provide authoritative information about:
    - **DAX (Data Analysis Expressions)** - Functions, syntax, best practices, and examples
    - **TMSL (Tabular Model Scripting Language)** - Model definitions, schema updates, and scripting
      **IMPORTANT**: Always refer to https://learn.microsoft.com/en-us/analysis-services/tmsl/tmsl-reference-tabular-objects for authoritative TMSL syntax and schema validation
    - **DirectLake** - Implementation guides, best practices, and troubleshooting
    - **Power BI** - Features, configuration, and advanced techniques

    ## 🎨 Chart Generation and Visualization Tools (NEW):
    The server now includes comprehensive chart generation capabilities that can automatically create visualizations from DAX query results.
    
    **Available Chart Generation Tools:**
    - `generate_chart_from_dax_results` - Generate charts from existing DAX query results
    - `analyze_dax_results_for_charts` - Analyze data structure and suggest optimal chart types
    - `execute_dax_with_visualization` - Execute DAX query and auto-generate charts (Power BI Service)
    - `execute_local_dax_with_visualization` - Execute DAX query and auto-generate charts (Local Power BI Desktop)
    - `create_comprehensive_dashboard` - Create multi-chart dashboards for table analysis
    
    **Supported Chart Types:**
    - **Line Charts** - Perfect for time series and trend analysis
    - **Bar Charts** - Ideal for categorical comparisons (horizontal and vertical)
    - **Pie Charts** - Great for showing proportions and distributions
    - **Scatter Plots** - Excellent for correlation analysis between numeric variables
    - **Heatmaps** - Visualize correlation matrices and relationships
    - **Comprehensive Dashboards** - Multi-chart views with summary statistics
    - **Auto-Generated Charts** - AI-powered chart type selection based on data characteristics
    
    **Chart Generation Features:**
    - **Interactive Charts** - HTML-based interactive visualizations using Vega-Lite
    - **Static Charts** - High-quality PNG charts using Matplotlib
    - **Auto-Detection** - Intelligent chart type suggestions based on data structure
    - **Custom Styling** - Professional themes and color schemes
    - **Multiple Formats** - Support for both web-ready and print-ready outputs
    - **Comprehensive Reports** - Markdown reports with analysis and insights
    
    **Example Chart Generation Usage:**
    ```
    # Execute DAX query and auto-generate visualizations
    result = execute_dax_with_visualization(
        "MyWorkspace", "MyDataset", 
        "EVALUATE SUMMARIZE(Sales, Sales[Category], \"Total\", SUM(Sales[Amount]))",
        auto_charts=True
    )
    
    # Generate specific chart type from existing DAX results
    chart = generate_chart_from_dax_results(
        dax_results, "bar", 
        chart_title="Sales by Category",
        interactive=True
    )
    
    # Create comprehensive dashboard for a table
    dashboard = create_comprehensive_dashboard(
        table_name="Sales",
        workspace_name="MyWorkspace",
        dataset_name="MyDataset",
        dashboard_title="Sales Analysis Dashboard"
    )
    ```
    
    ## 🚀 Tabular Object Model (TOM) Tools (NEW):
    The server now includes advanced TOM-based tools for semantic model manipulation, providing a superior alternative to TMSL for many operations.
    
    **TOM Advantages over TMSL:**
    - **Incremental Changes** - Add/modify individual objects without risk of deleting existing ones
    - **Object-Oriented API** - Work with strongly-typed objects instead of complex JSON
    - **Built-in Validation** - Automatic relationship management and constraint checking
    - **Simpler Syntax** - More intuitive programming model for common operations
    - **Enhanced Safety** - No need to reconstruct entire table definitions
    
    **Available TOM Tools:**
    - `add_measure_using_tom_tool` - Add measures safely without affecting existing objects
    - `test_tom_connection` - Test TOM connectivity and explore model structure
    - **More TOM tools coming soon** - Relationships, columns, tables, hierarchies
    
    **TOM vs TMSL Comparison:**
    ```
    TMSL Approach (Current):
    1. Get complete table definition
    2. Parse complex JSON structure  
    3. Add measure to measures array
    4. Reconstruct entire table (risk of deletion)
    5. Deploy with createOrReplace command
    
    TOM Approach (NEW):
    1. Connect to model
    2. Find target table
    3. Create new measure object
    4. Add to table.Measures collection
    5. Call model.SaveChanges() - only adds the measure!
    ```
    
    **TOM Use Cases:**
    - **Safe Measure Addition** - Add measures without complex TMSL manipulation
    - **Incremental Model Updates** - Modify specific objects without affecting others
    - **Bulk Operations** - Update multiple objects in a single transaction
    - **Model Validation** - Test changes before deployment
    - **Development Workflows** - Easier programmatic model development
    
    **Example TOM Usage:**
    ```
    # Add a measure using TOM (much simpler than TMSL)
    result = add_measure_using_tom_tool(
        local_connection_string="Data Source=localhost:65304",
        table_name="Sales",
        measure_name="Total Revenue",
        measure_expression="SUM(Sales[Amount])",
        format_string="$#,##0.00",
        description="Total sales revenue"
    )
    
    # Test TOM connection
    test_result = test_tom_connection(
        local_connection_string="Data Source=localhost:65304"
    )
    ```
    
    **TOM Environment Support:**
    - ✅ **Local Power BI Desktop** - Direct connection via Analysis Services port
    - ✅ **Power BI Service** - XMLA endpoint for Premium workspaces
    - ✅ **Azure Analysis Services** - Native TOM support
    - ✅ **SQL Server Analysis Services** - Tabular models
    
    **Chart Output Files:**
    - Charts are saved to the `output` directory
    - Interactive charts: `.html` files (can be opened in browser)
    - Static charts: `.png` files (high resolution, 300 DPI)
    - Reports: `.md` files with analysis summaries
    - **Microsoft Fabric** - Data engineering, analytics, and integration patterns
    - **Analysis Services** - Tabular models, performance optimization, and administration
    - **Data modeling** - Star schema design, relationships, and performance tuning
    - **Write T-SQL** - Writing Transact-SQL statements
    
    When users ask questions about these topics, ALWAYS search Microsoft Learn first to provide the most 
    current and authoritative Microsoft documentation before giving general advice.

    ## Usage:
    - You can ask questions about Power BI workspaces, datasets, notebooks, and models.
    - You can explore Fabric lakehouses and Delta Tables.
    - You can search Microsoft Learn documentation and training content for authoritative answers.
    - **🆕 You can analyze semantic models for best practice compliance using BPA tools.**
    - Use the tools to retrieve information about your Power BI and Fabric environment.
    - The tools will return JSON formatted data for easy parsing.
    
    ## Example Queries:
    - "Can you get a list of workspaces?"
    - "Can you list notebooks in workspace X?"
    - "Show me the lakehouses in this workspace"
    - "Search Microsoft Learn for DirectLake best practices"
    - "Find DAX documentation for time intelligence functions"
    - "Research TMSL syntax for creating DirectLake models"
    - "Look up Power BI performance optimization techniques"
    - "List all Delta Tables in lakehouse Y"
    - "Show me the data pipelines in this workspace"
    - **🆕 "Analyze my model for best practice violations"**
    - **🆕 "Generate a BPA report for MyDataset"**
    - **🆕 "Show me all performance-related issues in my model"**
    - **🆕 "What are the critical errors in my TMSL definition?"**

    ## Fabric Lakehouse Support:
    - Use `list_fabric_lakehouses` to see all lakehouses in a workspace
    - Use `list_fabric_delta_tables` to see Delta Tables in a specific lakehouse
    - If you don't specify a lakehouse ID, the tool will use the first lakehouse found
    - Delta Tables are the primary table format used in Fabric lakehouses

    ## Fabric Data Pipeline Support:
    - Use `list_fabric_pipelines` to see all Data Pipelines in a workspace
    - Data Pipelines are ETL/ELT workflows that can orchestrate data movement and transformation
    - The tool returns pipeline information including ID, name, description, and workspace details
    - Useful for discovering available data processing workflows in your Fabric workspace

    ## Note:
    - Ensure you have the necessary permissions to access Power BI and Fabric resources.
    - The tools will return errors if access tokens are not valid or if resources are not found.
    - The tools are designed to work with the Power BI REST API, Fabric REST API, and Microsoft Analysis Services.
    - The model definition tool retrieves a TMSL definition for Analysis Services Models.

    ## TMSL Definitions:
    - TMSL (Tabular Model Scripting Language) is used to define and manage tabular models in Analysis Services.
    - The `get_model_definition` tool retrieves a TMSL definition for the specified model in the given workspace.

    ## Getting Model Definitions:
    - Use the `get_model_definition` tool to retrieve the TMSL definition of a model.
    - You can specify the workspace name and dataset name to get the model definition.
    - The tool will return the TMSL definition as a string, which can be used for further analysis or updates.
    - Do not look at models that have the same name as a lakehouse.  This is likely a Default model so should be ignored.

    ## Running a DAX Query:
    - You can execute DAX queries against the Power BI model using the `execute_dax_query` tool.
    - Make sure you use the correct dataset name, not the dataset ID.
    - Provide the DAX query, the workspace name, and the dataset name to get results.
    - The results will be returned in JSON format for easy consumption.
    - **IMPORTANT**: When returning a single value, use braces {} around the expression as a table constructor:
      - CORRECT: EVALUATE {COUNTROWS(table)}
      - INCORRECT: EVALUATE COUNTROWS(table)
    - Do not use DAX queries to learn about columns in Lakehouse tables.
    - NEVER use DAX queries when the user asks for SQL/T-SQL queries.

    ## Running a T-SQL query against the Lakehouse SQL Analytics Endpoint
    - Use the `query_lakehouse_sql_endpoint` tool to run T-SQL queries against the Lakehouse SQL Analytics Endpoint.
    - This is the ONLY tool to use for SQL queries - never use execute_dax_query for SQL requests.
    - If this fails, do not follow up with a DAX Query.
    - Use this tool to validate table schemas, column names, and data types before creating DirectLake models.
    
    ## SQL Query Schema Considerations ##
    - **Table Naming**: Lakehouse tables can be queried using different naming patterns:
      * **Pattern 1**: `SELECT * FROM table_name` (when lakehouse has no default schema)
      * **Pattern 2**: `SELECT * FROM dbo.table_name` (when lakehouse is schema-enabled with dbo as default)
      * **Pattern 3**: `SELECT * FROM dbo_table_name` (tables prefixed with schema in their actual name)
    - **Schema Detection**: Check lakehouse properties - if `"defaultSchema": "dbo"` exists, use schema-qualified names
    - **Best Practice**: Try the table name as returned by `list_fabric_delta_tables` first, then try with schema prefix if needed
    - **Common Patterns**:
      * Tables named like `dbo_TableName` → Query as `FROM dbo_TableName`
      * Tables in schema-enabled lakehouse → Query as `FROM dbo.TableName` or `FROM schema.TableName`
    - **INFORMATION_SCHEMA queries**: Always work regardless of schema setup:
      * `SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'table_name'`

    ## 🚀 ENHANCED DirectLake Model Creation - NO MORE TRIAL AND ERROR! ##
    
    **🆕 RECOMMENDED APPROACH - Use generate_directlake_tmsl_template first!**
    1. **Step 1**: Use `generate_directlake_tmsl_template` to auto-generate valid TMSL
    2. **Step 2**: Use `update_model_using_tmsl` with `validate_only=True` to pre-validate
    3. **Step 3**: Use `update_model_using_tmsl` with `validate_only=False` to deploy
    
    **Benefits of new approach:**
    - ✅ Automatic schema validation against lakehouse tables
    - ✅ Pre-validated TMSL structure with all required components
    - ✅ Proper data type mapping from SQL to DirectLake
    - ✅ Built-in validation before deployment
    - ✅ Detailed error messages with fix suggestions
    
    ## Enhanced TMSL Validation ##
    The `update_model_using_tmsl` tool now includes comprehensive validation that catches:
    
    **🚨 CRITICAL ERRORS (Prevent Deployment Failures):**
    - ❌ Missing expressions block with DatabaseQuery
    - ❌ Table-level "mode": "directLake" property (BREAKS DEPLOYMENT!)
    - ❌ Missing partitions arrays
    - ❌ Incorrect partition mode placement
    - ❌ Invalid TMSL JSON syntax
    
    **⚠️ WARNINGS (May Cause Issues):**
    - Missing Sql.Database() in DatabaseQuery expression
    - Incorrect expressionSource values
    - Suboptimal TMSL structure
    
    **💡 AUTOMATIC SUGGESTIONS:**
    - Specific fixes for each error type
    - Code examples for corrections
    - References to required TMSL structure
    
    ## Validation-First Workflow ##
    ```
    # 1. Generate template (auto-validates schemas)
    template = generate_directlake_tmsl_template(workspace_id, lakehouse_id, ["table1", "table2"], "MyModel")
    
    # 2. Validate before deployment
    validation = update_model_using_tmsl(workspace, model_name, template, validate_only=True)
    
    # 3. Deploy if validation passes
    result = update_model_using_tmsl(workspace, model_name, template, validate_only=False)
    ```

    ## Updating the model:
    - The MCP Server uses TMSL scripts to update the model.
    - The `get_model_definition` tool retrieves the TMSL definition for a specified model.  Use this to get the current model structure.
    - The `update_model_using_tmsl` tool allows you to update the TMSL definition for a specified dataset in a Power BI workspace.
    - **NEW**: Enhanced with pre-validation and detailed error reporting
    - **NEW**: Use `validate_only=True` to test TMSL without deploying
    - Provide the workspace name, dataset name, and the new TMSL definition as a string.
    - The tool will return a success message or an error if the update fails.
    - Use this tool to modify the structure of your Power BI models dynamically.
    - eg. to add measures, calculated columns, or modify relationships in the model.
    - Note:
    - if you are updating the entire model, ensure the TMSL definition includes the `createOrReplace` for the database object.
    - if you are only updating a table, include the `createOrReplace` for the table object.
    - if you are only updating, adding or deleting a measure, only script the createOrReplace for the table object and not the entire database object if you can and be sure to include the columns.
    
    ## The model hierarchy ##
    - **Database**: The top-level container for the model.
    - **Model**: Represents the entire model within the database.   
    - **Table**: Represents a table in the model, containing columns and measures.
    - **Column**: Represents a column in a table, which can be a data column or a calculated column.
    - **Measure**: Represents a calculation or aggregation based on the data in the model.  
    - **Partition**: Represents a partition of data within a table, often used for performance optimization.

    ## Creating TMSL for a new DirectLake semantic model ##
    - **RECOMMENDED**: Use `generate_directlake_tmsl_template` for automatic generation
    - **ALTERNATIVE**: You can use the file stored in the tmsl_model_template.json as an example to create a new DirectLake model.
    - You will need to change the model name, dataset name, and workspace name to match your environment.
    
    ## 🚨 CRITICAL DIRECTLAKE REQUIREMENTS - VALIDATION ENFORCED! 🚨 ##

    **The validation system now automatically checks for these critical requirements:**

    **MANDATORY #1: TABLE MODE RESTRICTION**  
    - ❌ **NEVER ADD**: "mode": "directLake" at the table level (AUTOMATICALLY DETECTED AND BLOCKED)
    - ✅ ONLY ADD: "mode": "directLake" in the partition object inside partitions array
    - 🚫 TABLE LEVEL: { "name": "TableName", "mode": "directLake" } ← VALIDATION ERROR!
    - ✅ PARTITION LEVEL: { "name": "Partition", "mode": "directLake", "source": {...} } ← VALIDATED!

    **MANDATORY #2: EXPRESSIONS BLOCK**
    - ❌ NEVER FORGET: Every DirectLake model MUST have an "expressions" section (AUTOMATICALLY CHECKED)
    - ✅ ALWAYS ADD: expressions block with "DatabaseQuery" using Sql.Database() function
    - 🔧 FORMAT: expressions array with name:"DatabaseQuery", kind:"m", expression array

    **MANDATORY #4: SCHEMA QUALIFICATION (CRITICAL FIX)**
    - ✅ ALWAYS ADD: "schemaName" property in DirectLake partition sources (AUTOMATICALLY DETECTED!)
    - ❌ NEVER OMIT: Schema qualification leads to table connection failures
    - 🔧 AUTO-DETECTION: System detects 'gold', 'dbo', or first available schema automatically
    - 🎯 VALIDATED: Schema name validation prevents common lakehouse connection issues
    
    ## DirectLake Model Creation Checklist - NOW AUTOMATED! ##
    The validation system automatically verifies ALL of these:
    1. ✅ Model has "expressions" section with "DatabaseQuery" M expression
    2. ✅ Sql.Database() function with connection string and SQL Analytics Endpoint ID
    3. ✅ Each table has "partitions" array with at least one partition
    4. ✅ Each partition has "mode": "directLake" (NOT at table level!)
    5. ✅ Each partition has "expressionSource": "DatabaseQuery"
    6. ✅ All column names and data types validated against actual lakehouse tables
    7. ✅ **CRITICAL**: No table object has "mode": "directLake" property (BLOCKED!)
    8. ✅ Table objects only contain: name, source, columns, partitions, measures (no mode properties)
    
    ## Common DirectLake Mistakes - NOW PREVENTED! ##
    The validation system prevents these errors:
    - 🚫 Missing expressions block entirely (VALIDATION ERROR)
    - 🚫 **CRITICAL ERROR**: Adding "mode": "directLake" to table object (BLOCKED!)
    - 🚫 Using lakehouse name instead of SQL Analytics Endpoint ID in Sql.Database() (DETECTED)
    - 🚫 Missing partitions array (VALIDATION ERROR)
    - 🚫 Wrong expressionSource value (WARNING PROVIDED)
    
    ## 🚨 NEVER ADD MODE TO TABLE OBJECTS - NOW ENFORCED! 🚨 ##
    - ❌ WRONG: { "name": "TableName", "mode": "directLake", "source": {...} } ← VALIDATION BLOCKS THIS!
    - ✅ CORRECT: { "name": "TableName", "source": {...}, "partitions": [{"mode": "directLake"}] } ← VALIDATION PASSES!
    
    ## Step-by-Step DirectLake Creation Process - ENHANCED! ##
    1. **NEW**: Use `generate_directlake_tmsl_template` to auto-generate valid TMSL
    2. **OPTIONAL**: Use `update_model_using_tmsl` with `validate_only=True` to pre-validate
    3. **TRADITIONAL**: Get lakehouse SQL connection details using get_lakehouse_sql_connection_string
    4. **TRADITIONAL**: Validate table schema using query_lakehouse_sql_endpoint 
    5. **ENHANCED**: Create TMSL with expressions block and proper partition structure (or use template)
    6. **ENHANCED**: Deploy using update_model_using_tmsl with automatic validation
    7. Test with execute_dax_query but only against the model name that got created.  Do not query a different model
    
    ## Notes for creating a new DirectLake Model ##
    - **RECOMMENDED**: Use the new `generate_directlake_tmsl_template` tool for automatic generation
    - To create a new model, you can use the `update_model_using_tmsl` tool with a TMSL definition that includes the `createOrReplace` for the database object.
    - **NEW**: Enhanced validation prevents common mistakes before deployment
    - The TMSL definition should include the structure of the model, including tables, columns, and measures.
    - Ensure you provide a valid dataset name and workspace name when creating a new model.
    - The tool will return a success message or an error if the creation fails.
    - Notes:
    - The TMSL definition should be a valid JSON string.
    - **IMPORTANT**: The Sql.Database function takes two arguments: (1) SQL Analytics Endpoint connection string, (2) SQL Analytics Endpoint ID (NOT the lakehouse name or lakehouse ID).
    - Use `get_lakehouse_sql_connection_string` tool to get the correct endpoint ID for the Sql.Database function.
    - Do not use the same name for the model as the Lakehouse, as this can cause conflicts.
    - Relationships ONLY need the following five properties: `name` , `fromTable` ,  `fromColumn` , `toTable` , `toColumn`
    - Do NOT use the crossFilterBehavior property in relationships for DirectLake models.
    - When creating a new model, ensure each table only uses columns from the lakehouse tables and not any other source.  Validate if needed that the table names are not the same as any other source.
    - Do not create a column called rowNumber or rowNum, as this is a reserved name in DirectLake models.
    - When creating a new Directlake model, save the TMSL definition to a file for future reference or updates in the models subfolder.
    - Do not attempt to modify an existing semantic model when asked to create a new semantic model.  This would be bad and may overwrite another model
    
    ## DirectLake Model Creation Checklist - FINAL VERIFICATION NOW AUTOMATED! ##
    The enhanced validation system automatically verifies ALL of these before deployment:
    1. ✅ Model has "expressions" section with "DatabaseQuery" M expression ← AUTOMATICALLY CHECKED!
    2. ✅ Sql.Database() function with connection string and SQL Analytics Endpoint ID
    3. ✅ Each table has "partitions" array with at least one partition
    4. ✅ Each partition has "mode": "directLake" (NOT at table level!) ← AUTOMATICALLY ENFORCED!
    5. ✅ Each partition has "expressionSource": "DatabaseQuery"
    6. ✅ All column names and data types validated against actual lakehouse tables
    7. ✅ **DEPLOYMENT BREAKER**: No table object has "mode": "directLake" property (BLOCKED!) ← AUTOMATICALLY PREVENTED!
    8. ✅ **STRUCTURE CHECK**: Table objects only have allowed properties: name, source, columns, partitions, measures
    
    ## 🚨 TOP 3 MISTAKES NOW PREVENTED BY VALIDATION! 🚨
    1. Missing expressions block = VALIDATION ERROR with fix suggestion
    2. **Table-level "mode": "directLake" = BLOCKED before deployment with detailed error**
    3. Wrong partition structure = VALIDATION ERROR with structure guidance
    4. Wrong Sql.Database arguments = DETECTED with correction suggestion
    
    ## 🚫 FORBIDDEN TABLE PROPERTIES - NOW ENFORCED! 🚫
    **The validation system blocks these properties in table objects:**
    - "mode": "directLake" ← VALIDATION ERROR
    
    ## 🎯 BEST PRACTICE ANALYZER - ENSURING MODEL QUALITY ##
    
    **🆕 INTEGRATED BPA WORKFLOW FOR MODEL DEVELOPMENT:**
    The Best Practice Analyzer is now integrated into your model development workflow to ensure compliance with industry standards:
    
    **When to Use BPA:**
    - ✅ **BEFORE deploying** new models - Run BPA on TMSL to catch issues early
    - ✅ **AFTER model changes** - Validate updates follow best practices  
    - ✅ **REGULAR audits** - Check existing models for optimization opportunities
    - ✅ **TROUBLESHOOTING** - Identify performance bottlenecks and issues
    - ✅ **CODE REVIEWS** - Validate TMSL changes before deployment
    
    **BPA Integration Points:**
    ```
    # Complete model development workflow with BPA
    1. template = generate_directlake_tmsl_template(workspace_id, lakehouse_id, tables, "MyModel")
    2. bpa_pre_check = analyze_tmsl_bpa(template)  # ← ANALYZE BEFORE DEPLOYMENT
    3. validation = update_model_using_tmsl(workspace, "MyModel", template, validate_only=True)
    4. deployment = update_model_using_tmsl(workspace, "MyModel", template, validate_only=False)
    5. bpa_final_check = analyze_model_bpa(workspace, "MyModel")  # ← VERIFY DEPLOYED MODEL
    ```
    
    **🚨 BPA PRIORITY RULES - FOCUS ON THESE FIRST:**
    
    **CRITICAL ERRORS (Fix Immediately):**
    - 🔴 **DAX Syntax Issues** - Unqualified column references, improper measure references
    - 🔴 **Performance Killers** - Double data types, unhidden foreign keys, excessive calculated columns
    - 🔴 **Model Structure** - Missing relationships, orphaned tables, improper formatting
    
    **HIGH-IMPACT WARNINGS (Address Soon):**
    - 🟡 **Performance Optimization** - Use DIVIDE() instead of "/", avoid IFERROR(), partition large tables
    - 🟡 **DAX Best Practices** - Use TREATAS instead of INTERSECT, avoid certain time intelligence in DirectQuery
    - 🟡 **Maintenance Issues** - Missing descriptions, improper naming conventions
    
    **OPTIMIZATION SUGGESTIONS (Continuous Improvement):**
    - 🟢 **Formatting Standards** - Format strings, data categorization, proper capitalization
    - 🟢 **Documentation** - Object descriptions, consistent naming patterns
    - 🟢 **Model Hygiene** - Remove redundant objects, clean up unused elements
    
    **🔧 COMMON BPA FIXES FOR DIRECTLAKE MODELS:**
    
    **Performance Issues:**
    ```
    ❌ "dataType": "double"           → ✅ "dataType": "decimal"
    ❌ "isHidden": false (foreign key) → ✅ "isHidden": true  
    ❌ "summarizeBy": "sum"           → ✅ "summarizeBy": "none"
    ```
    
    **DAX Expression Issues:**
    ```
    ❌ SUM(SalesAmount)               → ✅ SUM(Sales[SalesAmount])
    ❌ [Sales] / [Quantity]          → ✅ DIVIDE([Sales], [Quantity])
    ❌ IFERROR([Calc], 0)            → ✅ Use DIVIDE() or proper error handling
    ```
    
    **Formatting Issues:**
    ```
    ❌ Missing formatString           → ✅ "formatString": "#,0"
    ❌ "isKey": false (primary key)   → ✅ "isKey": true
    ❌ Missing description            → ✅ "description": "Clear description"
    ```
    
    **🎯 BPA-DRIVEN MODEL CREATION WORKFLOW:**
    
    **Step 1: Generate Clean Template**
    ```
    template = generate_directlake_tmsl_template(workspace_id, lakehouse_id, tables, "MyModel")
    # ↳ This already follows many BPA best practices
    ```
    
    **Step 2: Pre-Deployment BPA Check**
    ```
    bpa_analysis = analyze_tmsl_bpa(template)
    critical_errors = get_bpa_violations_by_severity("ERROR")
    # ↳ Fix any critical issues before deployment
    ```
    
    **Step 3: Address BPA Violations**
    ```
    # Fix issues in template based on BPA recommendations
    # Common fixes: data types, format strings, hiding keys, etc.
    ```
    
    **Step 4: Deploy and Final Verification**
    ```
    deployment = update_model_using_tmsl(workspace, "MyModel", fixed_template)
    final_bpa = analyze_model_bpa(workspace, "MyModel")
    performance_issues = get_bpa_violations_by_category("Performance")
    ```
    
    **🔍 BPA TROUBLESHOOTING SCENARIOS:**
    
    **Scenario: Model Performance Issues**
    ```
    # 1. Get performance-specific recommendations
    perf_issues = get_bpa_violations_by_category("Performance")
    
    # 2. Focus on high-impact fixes first
    critical_perf = get_bpa_violations_by_severity("ERROR") # Filter to performance category
    
    # 3. Research specific optimizations
    docs = search_learn_microsoft_content("Power BI performance optimization")
    ```
    
    **Scenario: DAX Code Review**
    ```
    # 1. Check DAX best practices compliance
    dax_issues = get_bpa_violations_by_category("DAX Expressions")
    
    # 2. Generate detailed report for review
    report = generate_bpa_report(workspace, dataset, "detailed")
    
    # 3. Research DAX patterns
    dax_docs = search_learn_microsoft_content("DAX best practices")
    ```
    
    **Scenario: Model Maintenance Audit**
    ```
    # 1. Full model analysis
    full_analysis = analyze_model_bpa(workspace, dataset)
    
    # 2. Categorize by maintenance areas
    maintenance = get_bpa_violations_by_category("Maintenance")
    formatting = get_bpa_violations_by_category("Formatting")
    naming = get_bpa_violations_by_category("Naming Conventions")
    
    # 3. Prioritize fixes
    summary_report = generate_bpa_report(workspace, dataset, "summary")
    ```
    
    **💡 BPA INTEGRATION TIPS:**
    
    - **Always run BPA** on TMSL templates before deployment
    - **Focus on ERROR severity** violations first - these are critical
    - **Use BPA categories** to organize improvement efforts
    - **Integrate BPA checks** into your development workflow
    - **Research violations** using Microsoft Learn integration
    - **Document BPA compliance** as part of model documentation
    - **Regular BPA audits** help maintain model quality over time
    - **Use BPA reports** for stakeholder communication about model health
    
    **🚀 ADVANCED BPA USAGE:**
    
    **Automated Quality Gates:**
    ```
    # Gate 1: No critical errors allowed
    errors = get_bpa_violations_by_severity("ERROR")
    if len(errors) > 0: block_deployment()
    
    # Gate 2: Performance threshold
    perf_issues = get_bpa_violations_by_category("Performance")  
    if len(perf_issues) > threshold: require_review()
    
    # Gate 3: Documentation standards
    maintenance = get_bpa_violations_by_category("Maintenance")
    if missing_descriptions > limit: require_documentation()
    ```
    
    **Continuous Improvement:**
    ```
    # Weekly model health check
    weekly_report = generate_bpa_report(workspace, dataset, "by_category")
    
    # Track improvement over time
    compare_bpa_results(current_analysis, previous_analysis)
    
    # Identify model-wide patterns
    analyze_all_models_in_workspace(workspace)
    ```
    - "defaultMode": "directLake" ← VALIDATION ERROR  
    - Any mode-related property ← VALIDATION ERROR
    
    ## CRITICAL: Schema Validation Before Model Creation ##
    - **ENHANCED**: The `generate_directlake_tmsl_template` tool automatically validates schemas
    - **TRADITIONAL**: Use the `query_lakehouse_sql_endpoint` tool to validate table schemas manually
    - Do not query all the data in the Lakehouse table - this is not needed and can be slow, especially for large tables.  Use the TOP 5 or similar queries to validate the structure.
    - DirectLake models must exactly match the source Delta table schema - any mismatch will cause deployment failures
    - **Schema-Aware Query Examples**:
      * `"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'your_table_name'"` (works with any schema setup)
      * `"SELECT TOP 5 * FROM your_table_name"` (use exact table name from list_fabric_delta_tables)
      * `"SELECT TOP 5 * FROM dbo.your_table_name"` (if lakehouse has defaultSchema: "dbo")
      * `"SHOW TABLES"` (to see all available tables and their naming patterns)
      * `"SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"` (to see schema structure)
    - Column names are case-sensitive and must match exactly
    - Data types must be compatible between Delta Lake and DirectLake
    - Never assume column names or structures - always validate first
    - **Troubleshooting**: If a query fails with "object not found", try alternative schema patterns (with/without dbo prefix)
    
    ## Example Enhanced Workflow ##
    ```
    # NEW RECOMMENDED APPROACH:
    1. template = generate_directlake_tmsl_template(workspace_id, lakehouse_id, ["dim_Date", "fact_Sales"], "MyModel")
    2. validation = update_model_using_tmsl(workspace, "MyModel", template, validate_only=True)  
    3. result = update_model_using_tmsl(workspace, "MyModel", template, validate_only=False)
    
    # TRADITIONAL APPROACH WITH VALIDATION:
    1. connection_info = get_lakehouse_sql_connection_string(workspace_id, lakehouse_id)
    2. schema_check = query_lakehouse_sql_endpoint(workspace_id, "INFORMATION_SCHEMA query")
    3. tmsl = create_manual_tmsl_definition()
    4. validation = update_model_using_tmsl(workspace, model, tmsl, validate_only=True)
    5. deployment = update_model_using_tmsl(workspace, model, tmsl, validate_only=False)
    ```

    ## 🆕 Power BI Desktop Detection and Local Development ##
    
    **New Local Development Capabilities:**
    The server now includes tools to detect and connect to local Power BI Desktop instances for development and testing:
    
    **Available Power BI Desktop Tools:**
    - `detect_local_powerbi_desktop` - Scan for running Power BI Desktop instances
    - `test_local_powerbi_connection` - Test connection to local Analysis Services
    - `compare_analysis_services_connections` - Compare connection types and requirements
    - `explore_local_powerbi_tables` - List tables in local Power BI Desktop models
    - `explore_local_powerbi_columns` - List columns in local models (all or specific table)
    - `explore_local_powerbi_measures` - List measures with DAX expressions
    - `execute_local_powerbi_dax` - Execute DAX queries against local models
    
    **Key Features:**
    - **Process Detection**: Automatically find running Power BI Desktop processes
    - **Port Discovery**: Identify Analysis Services port numbers for each instance
    - **Connection Strings**: Generate ready-to-use connection strings for local development
    - **File Detection**: Identify which .pbix files are currently open
    - **Connection Testing**: Validate connectivity to local instances
    - **Model Exploration**: List tables, columns, and measures in local models
    - **DAX Execution**: Run DAX queries against local instances without authentication
    
    **Use Cases:**
    - **Local Development**: Connect to models being developed in Power BI Desktop
    - **Testing**: Validate changes against local instances before publishing
    - **Debugging**: Analyze local models using BPA tools
    - **Model Exploration**: Examine table structures, columns, and measures locally
    - **DAX Testing**: Test DAX expressions against local data
    - **Integration**: Incorporate local Power BI Desktop models into development workflows
    
    **Example Power BI Desktop Usage:**
    ```
    # Detect all running Power BI Desktop instances
    instances = detect_local_powerbi_desktop()
    
    # Test connection to a specific port
    connection_test = test_local_powerbi_connection(55001)
    
    # Explore model structure
    tables = explore_local_powerbi_tables("Data Source=localhost:55001")
    columns = explore_local_powerbi_columns("Data Source=localhost:55001", "Sales")
    measures = explore_local_powerbi_measures("Data Source=localhost:55001")
    
    # Execute DAX queries
    dax_result = execute_local_powerbi_dax("Data Source=localhost:55001", "EVALUATE 'Sales'")
    
    # Compare different connection types
    comparison = compare_analysis_services_connections()
    
    # Use local connection for BPA analysis
    # (Note: BPA tools work with local instances using connection strings)
    ```
    
    **Connection Simplicity:**
    Power BI Desktop connections are much simpler than Power BI Service connections:
    - **Power BI Desktop**: `Data Source=localhost:port` (no authentication required)
    - **Power BI Service**: Complex connection string with tokens and authentication
    - **Analysis Services**: Windows/SQL authentication required
    
    This makes Power BI Desktop ideal for development and testing scenarios where
    you need quick, reliable access to semantic models without authentication complexity.
    
    **Power BI Desktop Connection Information:**
    - Power BI Desktop runs a local Analysis Services instance
    - Ports are typically dynamic (usually > 50000)
    - Connection format: `Data Source=localhost:{port}`
    - Each open .pbix file gets its own Analysis Services instance
    - Instances are automatically detected when Power BI Desktop is running

"""
)

# Register all MCP prompts from the prompts module
register_prompts(mcp)

# Initialize BPA Service
current_dir = os.path.dirname(os.path.abspath(__file__))
bpa_service = BPAService(current_dir)

@mcp.tool
def get_server_version() -> str:
    """Get the version information for the Semantic Model MCP Server."""
    return f"Semantic Model MCP Server v{__version__} - {__description__}"

@mcp.tool
def list_powerbi_workspaces() -> str:
    """Lists available Power BI workspaces for the current user."""
    return list_workspaces()

@mcp.tool
def list_powerbi_datasets(workspace_id: str) -> str:
    """Lists all datasets in a specified Power BI workspace."""
    return list_datasets(workspace_id)

@mcp.tool
def get_powerbi_workspace_id(workspace_name: str) -> str:
    """Gets the workspace ID for a given workspace name."""
    return get_workspace_id(workspace_name)

@mcp.tool
def list_powerbi_notebooks(workspace_id: str) -> str:
    """Lists all notebooks in a specified Power BI workspace."""
    return list_notebooks(workspace_id)

@mcp.tool
def list_fabric_lakehouses(workspace_id: str) -> str:
    """Lists all lakehouses in a specified Fabric workspace."""
    return list_lakehouses(workspace_id)

@mcp.tool
def list_fabric_delta_tables(workspace_id: str, lakehouse_id: str = None) -> str:
    """Lists all Delta Tables in a specified Fabric Lakehouse.
    If lakehouse_id is not provided, will use the first lakehouse found in the workspace.
    This function now supports both regular lakehouses and schema-enabled lakehouses by automatically
    falling back to SQL Analytics Endpoint queries when the Fabric API returns an error for schema-enabled lakehouses.
    """
    return list_delta_tables(workspace_id, lakehouse_id)

@mcp.tool
def debug_lakehouse_contents(workspace_id: str, lakehouse_id: str = None) -> str:
    """Debug function to check various API endpoints for lakehouse contents including files and items.
    """
    return list_lakehouse_files(workspace_id, lakehouse_id)

@mcp.tool
def get_lakehouse_sql_connection_string(workspace_id: str, lakehouse_id: str = None, lakehouse_name: str = None) -> str:
    """Gets the SQL endpoint connection string for a specified Fabric Lakehouse.
    You can specify either lakehouse_id or lakehouse_name to identify the lakehouse.
    Returns connection information including server name and connection string templates.
    """
    return fabric_get_lakehouse_sql_connection_string(workspace_id, lakehouse_id, lakehouse_name)

@mcp.tool
def clear_azure_token_cache() -> str:
    """Clears the authentication token cache. 
    Useful for debugging authentication issues or forcing token refresh.
    
    Note: Now uses unified Power BI token authentication for all services.
    """
    from core.auth import clear_token_cache
    
    try:
        # Clear the unified token cache
        clear_token_cache()
        return "Authentication token cache cleared successfully. All cached tokens have been removed."
    except Exception as e:
        return f"Failed to clear token cache: {str(e)}"

@mcp.tool
def get_azure_token_status() -> str:
    """Gets the current status of the authentication token cache.
    Shows token validity status for the unified Power BI authentication.
    
    Note: Now uses unified Power BI token authentication for all services.
    """
    from core.auth import _access_token, _token_expiry
    import json
    import time
    from datetime import datetime
    
    if not _access_token or not _token_expiry:
        return json.dumps({
            "status": "No token cached",
            "message": "No authentication token is currently cached"
        }, indent=2)
    
    current_time = time.time()
    is_valid = current_time < _token_expiry
    time_until_expiry = _token_expiry - current_time if is_valid else 0
    
    status = {
        "status": "Token cached",
        "is_valid": is_valid,
        "expires_at": datetime.fromtimestamp(_token_expiry).isoformat() if _token_expiry else None,
        "time_until_expiry_seconds": max(0, time_until_expiry),
        "authentication_scope": "Power BI API (unified for all services)",
        "note": "Single token now used for both Power BI API and lakehouse SQL endpoints"
    }
    
    return json.dumps(status, indent=2)

@mcp.tool
def execute_dax_query(workspace_name:str, dataset_name: str, dax_query: str, dataset_id: str = None) -> str:
    """Executes a DAX query against the Power BI model.
    This tool connects to the specified Power BI workspace and dataset name, executes the provided DAX query,
    Use the dataset_name to specify the model to query and NOT the dataset ID.
    The function connects to the Power BI service using an access token, executes the DAX query,
    and returns the results.
    """  
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotnet_dir = os.path.join(script_dir, "dotnet")
    
    print(f"Using .NET assemblies from: {dotnet_dir}")
    
    try:
        #clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.dll"))
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.Tabular.dll"))
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.Identity.Client.dll"))
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.IdentityModel.Abstractions.dll"))
        clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.AdomdClient.dll"))
    except Exception as e:
        return {"error": f"Failed to load required .NET assemblies: {str(e)}", "error_type": "assembly_load_error", "success": False}

    try:
        from Microsoft.AnalysisServices.AdomdClient import AdomdConnection ,AdomdDataReader  # type: ignore
    except ImportError as e:
        return {"error": f"Failed to import ADOMD libraries: {str(e)}", "error_type": "import_error", "success": False}

    # Validate authentication
    access_token = get_access_token()
    if not access_token:
        return {"error": "No valid access token available. Please check authentication.", "error_type": "authentication_error", "success": False}

    # Validate required parameters
    if not workspace_name or not workspace_name.strip():
        return {"error": "Workspace name is required and cannot be empty.", "error_type": "parameter_error", "success": False}
    
    if not dataset_name or not dataset_name.strip():
        return {"error": "Dataset name is required and cannot be empty.", "error_type": "parameter_error", "success": False}
    
    if not dax_query or not dax_query.strip():
        return {"error": "DAX query is required and cannot be empty.", "error_type": "parameter_error", "success": False}

    workspace_name_encoded = urllib.parse.quote(workspace_name)
    # Use URL-encoded workspace name and standard XMLA connection format
    # The connection string format is: Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name};Password={access_token};Catalog={dataset_name};
    connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};Catalog={dataset_name};"

    connection = None
    try:
        # Attempt to establish connection
        connection = AdomdConnection(connection_string)
        connection.Open()
        
        # Execute the DAX query
        command = connection.CreateCommand()
        command.CommandText = dax_query
        reader: AdomdDataReader = command.ExecuteReader()
        
        results = []
        while reader.Read():
            row = {}
            for i in range(reader.FieldCount):
                # Handle different data types and null values
                value = reader.GetValue(i)
                column_name = str(reader.GetName(i))  # Ensure column name is Python string
                
                if value is None or str(value) == "":
                    row[column_name] = None
                else:
                    # CRITICAL: Force immediate conversion to prevent System.Decimal from reaching FastMCP
                    value_str = str(value)
                    value_type = str(type(value))
                    
                    try:
                        if "Decimal" in value_type:
                            # Convert System.Decimal immediately to Python float
                            row[column_name] = float(value_str)
                        elif "Double" in value_type or "Single" in value_type:
                            # Convert System.Double/Single immediately to Python float  
                            row[column_name] = float(value_str)
                        elif "Int64" in value_type or "Int32" in value_type or "Int16" in value_type:
                            # Convert System.Int* immediately to Python int
                            row[column_name] = int(value_str)
                        elif "Boolean" in value_type:
                            # Convert System.Boolean immediately to Python bool
                            row[column_name] = value_str.lower() in ('true', '1', 'yes')
                        elif "DateTime" in value_type and hasattr(value, 'isoformat'):
                            # Convert DateTime objects to ISO string
                            row[column_name] = value.isoformat()
                        else:
                            # For all other types, use string representation
                            row[column_name] = value_str
                    except (ValueError, OverflowError, AttributeError) as conversion_error:
                        # If any conversion fails, use string representation
                        print(f"Warning: Failed to convert {column_name} value '{value_str}' (type: {value_type}): {conversion_error}")
                        row[column_name] = value_str
            
            results.append(row)
        
        reader.Close()
        
        # Get column names for metadata
        column_names = []
        if results:
            column_names = list(results[0].keys())
        
        # Return structured response with proper numeric types preserved
        # Since we've already converted System.Decimal to Python float above,
        # we can safely return the Python object without JSON serialization
        return {
            "success": True,
            "data": results,
            "row_count": len(results),
            "columns": column_names,
            "workspace": workspace_name,
            "dataset": dataset_name
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        error_details = str(e)
        
        # Categorize different types of errors and provide helpful messages
        if "authentication" in error_msg or "unauthorized" in error_msg or "login" in error_msg:
            return {"error": f"Authentication failed: {error_details}. Please check your access token and permissions.", "error_type": "authentication_error", "success": False}
        elif "workspace" in error_msg or "not found" in error_msg:
            return {"error": f"Workspace or dataset not found: {error_details}. Please verify workspace name '{workspace_name}' and dataset name '{dataset_name}' are correct.", "error_type": "not_found_error", "success": False}
        elif "permission" in error_msg or "access" in error_msg or "forbidden" in error_msg:
            return {"error": f"Permission denied: {error_details}. You may not have sufficient permissions to query this dataset.", "error_type": "permission_error", "success": False}
        elif "syntax" in error_msg or "parse" in error_msg or "invalid" in error_msg:
            return {"error": f"DAX query syntax error: {error_details}. Please check your DAX query syntax.", "error_type": "dax_syntax_error", "query_provided": "yes", "success": False}
        elif "timeout" in error_msg or "timed out" in error_msg:
            return {"error": f"Query timeout: {error_details}. The query took too long to execute.", "error_type": "timeout_error", "success": False}
        elif "connection" in error_msg or "network" in error_msg:
            return {"error": f"Connection error: {error_details}. Please check your network connection and try again.", "error_type": "connection_error", "success": False}
        else:
            return {"error": f"Unexpected error executing DAX query: {error_details}", "error_type": "general_error", "query_provided": "yes", "success": False}
    
    finally:
        # Ensure connection is always closed
        try:
            if connection is not None and hasattr(connection, 'State') and connection.State == 1:  # ConnectionState.Open = 1
                connection.Close()
        except Exception as cleanup_error:
            print(f"Warning: Error during connection cleanup: {cleanup_error}")
            # Don't return error here as it would mask the main error

# Internal helper function for SQL queries (not exposed as MCP tool)
def _internal_query_lakehouse_sql_endpoint(workspace_id: str, sql_query: str, lakehouse_id: str = None, lakehouse_name: str = None) -> str:
    """Executes a SQL query against a Fabric Lakehouse SQL Analytics Endpoint to validate table schemas and data.
    This tool connects to the specified Fabric Lakehouse SQL Analytics Endpoint and executes the provided SQL query.
    Use this tool to:
    - Validate actual column names and data types in lakehouse tables
    - Query table schemas before creating DirectLake models
    - Inspect data samples from lakehouse tables
    - Verify table structures match your model expectations
    
    Args:
        workspace_id: The Fabric workspace ID containing the lakehouse
        sql_query: The SQL query to execute (e.g., "SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'date'")
        lakehouse_id: Optional specific lakehouse ID to query
        lakehouse_name: Optional lakehouse name to query (alternative to lakehouse_id)
    
    Returns:
        JSON string containing query results or error message
    
    Example queries for schema validation:
    - "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'sales_1'"
    - "SELECT TOP 5 * FROM date"
    - "SHOW TABLES"
    """
    import json
    import struct

    # Use the same authentication token as all other Power BI functions
    # This eliminates the need for separate authentication and works with lakehouse SQL endpoints
    access_token = get_access_token()
    if not access_token:
        return json.dumps({
            "success": False,
            "error": "Authentication failed: Could not obtain access token"
        }, indent=2)
    
    # Convert token to SQL Server authentication format
    token_bytes = access_token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

    # Check if pyodbc is available
    if pyodbc is None:
        return json.dumps({
            "success": False,
            "error": "pyodbc is not installed. Please install it using: pip install pyodbc"
        }, indent=2)
    
    try:
        # Get the SQL Analytics Endpoint connection string
        connection_info = fabric_get_lakehouse_sql_connection_string(workspace_id, lakehouse_id, lakehouse_name)
        
        if "error" in connection_info.lower():
            return f"Error getting connection string: {connection_info}"
        
        # Parse the connection info to get the server and endpoint ID
        connection_data = json.loads(connection_info)
        server_name = connection_data.get("sql_endpoint", {}).get("server_name")
        endpoint_id = connection_data.get("sql_endpoint", {}).get("endpoint_id")
        
        if not server_name or not endpoint_id:
            return "Error: Could not retrieve SQL Analytics Endpoint information"
        
        # Build connection string for SQL Analytics Endpoint
        # For Fabric SQL Analytics Endpoints, use the lakehouse name as the database
        lakehouse_name = connection_data.get("lakehouse_name")
        if not lakehouse_name:
            return json.dumps({
                "success": False,
                "error": "Could not determine lakehouse name for database connection"
            }, indent=2)
        
        # Try different ODBC drivers in order of preference
        available_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server", 
            "SQL Server"
        ]
        
        # Detect which driver is available
        available_driver = None
        available_pyodbc_drivers = pyodbc.drivers()
        
        for driver in available_drivers:
            if driver in available_pyodbc_drivers:
                available_driver = driver
                break
        
        if not available_driver:
            return json.dumps({
                "success": False,
                "error": "No compatible ODBC driver found. Please install ODBC Driver for SQL Server.",
                "available_drivers": list(available_pyodbc_drivers),
                "looking_for": available_drivers
            }, indent=2)
        
        connection_string = (
            f"Driver={{{available_driver}}};"
            f"Server={server_name};"
            f"Database={lakehouse_name};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
        )
        
        # Debug: log connection attempt
        print(f"Attempting connection with driver: {available_driver}")
        print(f"Connection string: {connection_string}")
        
        # Execute the query using ActiveDirectoryInteractive authentication
        with pyodbc.connect(connection_string, attrs_before={1256  : token_struct}) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    # Handle special data types
                    if hasattr(value, 'isoformat'):  # datetime objects
                        row_dict[columns[i]] = value.isoformat()
                    elif isinstance(value, (bytes, bytearray)):  # binary data
                        row_dict[columns[i]] = str(value)
                    else:
                        row_dict[columns[i]] = value
                results.append(row_dict)
            
            return json.dumps({
                "success": True,
                "query": sql_query,
                "columns": columns,
                "row_count": len(results),
                "results": results[:100],  # Limit to first 100 rows to avoid large responses
                "note": f"Showing first 100 rows out of {len(results)} total rows" if len(results) > 100 else None
            }, indent=2)
            
    except pyodbc.Error as e:
        error_details = str(e)
        return json.dumps({
            "success": False,
            "error": f"SQL Error: {error_details}",
            "query": sql_query,
            "debug_info": {
                "server_name": server_name if 'server_name' in locals() else "Not available",
                "lakehouse_name": lakehouse_name if 'lakehouse_name' in locals() else "Not available",
                "available_driver": available_driver if 'available_driver' in locals() else "Not detected",
                "connection_string": connection_string if 'connection_string' in locals() else "Not available"
            }
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Connection Error: {str(e)}",
            "query": sql_query,
            "debug_info": {
                "connection_info": connection_info if 'connection_info' in locals() else "Not available"
            }
        }, indent=2)

@mcp.tool
def query_lakehouse_sql_endpoint(workspace_id: str, sql_query: str, lakehouse_id: str = None, lakehouse_name: str = None) -> str:
    """Executes a SQL query against a Fabric Lakehouse SQL Analytics Endpoint to validate table schemas and data.
    This tool connects to the specified Fabric Lakehouse SQL Analytics Endpoint and executes the provided SQL query.
    Use this tool to:
    - Validate actual column names and data types in lakehouse tables
    - Query table schemas before creating DirectLake models
    - Inspect data samples from lakehouse tables
    - Verify table structures match your model expectations
    
    Args:
        workspace_id: The Fabric workspace ID containing the lakehouse
        sql_query: The SQL query to execute (e.g., "SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'date'")
        lakehouse_id: Optional specific lakehouse ID to query
        lakehouse_name: Optional lakehouse name to query (alternative to lakehouse_id)
    
    Returns:
        JSON string containing query results or error message
    
    Example queries for schema validation:
    - "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'sales_1'"
    - "SELECT TOP 5 * FROM date"
    - "SHOW TABLES"
    """
    return _internal_query_lakehouse_sql_endpoint(workspace_id, sql_query, lakehouse_id, lakehouse_name)

@mcp.tool
def generate_directlake_tmsl_template(workspace_id: str, lakehouse_id: str = None, lakehouse_name: str = None, table_names: Optional[List[str]] = None, model_name: str = "NewDirectLakeModel") -> str:
    """Generates a valid DirectLake TMSL template with proper structure and validated schemas.
    
    This helper tool automatically creates a complete DirectLake TMSL definition by:
    1. Connecting to the specified lakehouse
    2. Validating table schemas using SQL Analytics Endpoint
    3. Generating proper TMSL structure with all required components
    4. Including validation-ready partitions and expressions
    
    Args:
        workspace_id: The Fabric workspace ID containing the lakehouse
        lakehouse_id: Optional specific lakehouse ID
        lakehouse_name: Optional lakehouse name (alternative to lakehouse_id)
        table_names: List of table names to include (if not provided, suggests available tables)
        model_name: Name for the new DirectLake model
    
    Returns:
        Complete TMSL JSON string ready for use with update_model_using_tmsl
    """
    
    try:
        # Get lakehouse connection information
        connection_info = fabric_get_lakehouse_sql_connection_string(workspace_id, lakehouse_id, lakehouse_name)
        if "error" in connection_info.lower():
            return f"Error getting lakehouse connection: {connection_info}"
        
        connection_data = json.loads(connection_info)
        server_name = connection_data.get("sql_endpoint", {}).get("server_name")
        endpoint_id = connection_data.get("sql_endpoint", {}).get("endpoint_id")
        actual_lakehouse_name = connection_data.get("lakehouse_name")
        
        if not server_name or not endpoint_id:
            return "Error: Could not retrieve SQL Analytics Endpoint information"
        
        # If no table names provided, get available tables
        if not table_names:
            delta_tables_result = list_delta_tables(workspace_id, lakehouse_id)
            try:
                delta_tables = json.loads(delta_tables_result)
                available_tables = [table["name"] for table in delta_tables]
                return f"Available tables in lakehouse '{actual_lakehouse_name}':\n{json.dumps(available_tables, indent=2)}\n\nPlease call this function again with specific table_names parameter."
            except:
                return f"Error retrieving available tables: {delta_tables_result}"
        
        # First, detect available schemas in the lakehouse
        schema_detection_query = "SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA"
        schema_result = _internal_query_lakehouse_sql_endpoint(workspace_id, schema_detection_query, lakehouse_id, lakehouse_name)
        
        detected_schema = "dbo"  # Default schema
        try:
            schema_data = json.loads(schema_result)
            if schema_data.get("success"):
                schemas = [row["TABLE_SCHEMA"] for row in schema_data.get("results", [])]
                # Prefer 'gold' schema if available, otherwise use first non-system schema
                if "gold" in schemas:
                    detected_schema = "gold"
                elif schemas:
                    # Filter out system schemas and use the first available
                    user_schemas = [s for s in schemas if s not in ["INFORMATION_SCHEMA", "sys", "db_accessadmin", "db_backupoperator", 
                                                                   "db_datareader", "db_datawriter", "db_ddladmin", "db_denydatareader", 
                                                                   "db_denydatawriter", "db_owner", "db_securityadmin", "guest"]]
                    if user_schemas:
                        detected_schema = user_schemas[0]
        except Exception as e:
            print(f"Warning: Could not detect schema, using default 'dbo': {e}")
        
        # Validate table schemas
        validated_tables = []
        for table_name in table_names:
            schema_query = f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION"
            schema_result = _internal_query_lakehouse_sql_endpoint(workspace_id, schema_query, lakehouse_id, lakehouse_name)
            
            try:
                schema_data = json.loads(schema_result)
                if schema_data.get("success"):
                    columns = []
                    for col in schema_data.get("results", []):
                        # Map SQL types to DirectLake types
                        sql_type = col["DATA_TYPE"].lower()
                        if sql_type in ["varchar", "nvarchar", "char", "nchar", "text", "ntext"]:
                            dl_type = "string"
                        elif sql_type in ["int", "bigint", "smallint", "tinyint"]:
                            dl_type = "int64"
                        elif sql_type in ["decimal", "numeric", "float", "real", "money", "smallmoney"]:
                            dl_type = "decimal"
                        elif sql_type in ["datetime", "datetime2", "date", "time", "smalldatetime"]:
                            dl_type = "dateTime"
                        elif sql_type in ["bit"]:
                            dl_type = "boolean"
                        else:
                            dl_type = "string"  # Default fallback
                        
                        columns.append({
                            "name": col["COLUMN_NAME"],
                            "dataType": dl_type,
                            "sourceColumn": col["COLUMN_NAME"],
                            "lineageTag": f"{table_name}_{col['COLUMN_NAME']}",
                            "sourceLineageTag": col["COLUMN_NAME"],
                            "summarizeBy": "sum" if dl_type in ["int64", "decimal"] and "quantity" in col["COLUMN_NAME"].lower() else "none"
                        })
                    
                    validated_tables.append({
                        "name": table_name,
                        "columns": columns,
                        "schema": detected_schema  # Add schema information to each table
                    })
                else:
                    return f"Error validating schema for table '{table_name}': {schema_data.get('error', 'Unknown error')}"
            except Exception as e:
                return f"Error processing schema for table '{table_name}': {str(e)}"
        
        # Generate complete TMSL structure
        tmsl_template = {
            "createOrReplace": {
                "object": {
                    "database": model_name
                },
                "database": {
                    "name": model_name,
                    "compatibilityLevel": 1604,
                    "model": {
                        "culture": "en-US",
                        "collation": "Latin1_General_100_BIN2_UTF8",
                        "dataAccessOptions": {
                            "legacyRedirects": True,
                            "returnErrorValuesAsNull": True
                        },
                        "defaultPowerBIDataSourceVersion": "powerBI_V3",
                        "sourceQueryCulture": "en-US",
                        "tables": [],
                        "expressions": [
                            {
                                "name": "DatabaseQuery",
                                "kind": "m",
                                "expression": [
                                    "let",
                                    f"    database = Sql.Database(\"{server_name}\", \"{endpoint_id}\")",
                                    "in",
                                    "    database"
                                ],
                                "lineageTag": "DatabaseQuery_expression",
                                "annotations": [
                                    {
                                        "name": "PBI_IncludeFutureArtifacts",
                                        "value": "False"
                                    }
                                ]
                            }
                        ],
                        "annotations": [
                            {
                                "name": "__PBI_TimeIntelligenceEnabled",
                                "value": "0"
                            },
                            {
                                "name": "PBI_QueryOrder",
                                "value": "[\"DatabaseQuery\"]"
                            },
                            {
                                "name": "PBI_ProTooling",
                                "value": "[\"WebModelingEdit\"]"
                            }
                        ]
                    }
                }
            }
        }
        
        # Add validated tables with proper DirectLake structure
        for table_info in validated_tables:
            table_def = {
                "name": table_info["name"],
                "lineageTag": f"{table_info['name']}_table",
                "sourceLineageTag": f"[{table_info['schema']}].[{table_info['name']}]",
                "columns": table_info["columns"],
                "partitions": [
                    {
                        "name": f"{table_info['name']}_partition",
                        "mode": "directLake",
                        "source": {
                            "type": "entity",
                            "schemaName": table_info["schema"],  # Add schema qualification
                            "entityName": table_info["name"],
                            "expressionSource": "DatabaseQuery"
                        }
                    }
                ]
            }
            tmsl_template["createOrReplace"]["database"]["model"]["tables"].append(table_def)
        
        return json.dumps(tmsl_template, indent=2)
        
    except Exception as e:
        return f"Error generating DirectLake TMSL template: {str(e)}"

@mcp.tool
def update_model_using_tmsl(workspace_name: str, dataset_name: str, tmsl_definition: str, validate_only: bool = False) -> str:
    """Updates the TMSL definition for an Analysis Services Model with enhanced validation.
    
    This tool connects to the specified Power BI workspace and dataset name, validates and updates the TMSL definition,
    and returns a success message or detailed error information if the update fails.
    
    Args:
        workspace_name: The Power BI workspace name
        dataset_name: The dataset/model name to update
        tmsl_definition: Valid TMSL JSON string
        validate_only: If True, only validates the TMSL without executing (default: False)
    
    Enhanced Features:
    - Pre-validates TMSL structure before sending to server
    - Checks for common DirectLake mistakes
    - Provides detailed error messages with suggestions
    - Validates required DirectLake components
    
    Returns:
        Success message or detailed error with suggestions for fixes
    """   
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotnet_dir = os.path.join(script_dir, "dotnet")

    print(f"Using .NET assemblies from: {dotnet_dir}")
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.dll"))
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.Tabular.dll"))
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.Identity.Client.dll"))
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.IdentityModel.Abstractions.dll"))

    from Microsoft.AnalysisServices.Tabular import Server# type: ignore
    from Microsoft.AnalysisServices import XmlaResultCollection  # type: ignore

    access_token = get_access_token()
    if not access_token:
        return "Error: No valid access token available"
    
    workspace_name_encoded = urllib.parse.quote(workspace_name)
    connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token}"
    server = Server()
    
    try:
        server.Connect(connection_string)
        
        # Enhanced TMSL validation before processing
        validation_result = validate_tmsl_structure(tmsl_definition)
        if not validation_result["valid"]:
            return f"❌ TMSL Validation Failed:\n{validation_result['error']}\n\n💡 Suggestions:\n{validation_result['suggestions']}"
        
        # If validate_only is True, return validation success without executing
        if validate_only:
            return f"✅ TMSL Validation Passed:\n{validation_result['summary']}\n\n📋 Structure validated successfully - ready for deployment!"
        
        # Parse the TMSL definition to check its structure
        try:
            tmsl = json.loads(tmsl_definition)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in TMSL definition - {e}"
        
        databaseCount = count_nodes_with_name(tmsl, "database")
        tableCount = count_nodes_with_name(tmsl, "table")
        
        # Check if the tmsl_definition already has createOrReplace at the root level
        if "createOrReplace" in tmsl:
            # TMSL already has createOrReplace wrapper, use as-is
            final_tmsl = tmsl_definition
        elif databaseCount > 0:
            # TMSL contains database definition, wrap with createOrReplace for database
            final_tmsl = json.dumps({
                "createOrReplace": {
                    "object": {
                        "database": dataset_name
                    },
                    "database": tmsl
                }
            })
        elif tableCount == 1:
            # TMSL contains single table definition, extract table name and wrap appropriately
            table_name = None
            if "name" in tmsl:
                table_name = tmsl["name"]
            elif isinstance(tmsl, dict):
                # Try to find table name in the structure
                for key, value in tmsl.items():
                    if key == "name" and isinstance(value, str):
                        table_name = value
                        break
            
            if not table_name:
                return "Error: Cannot determine table name from TMSL definition"
                
            final_tmsl = json.dumps({
                "createOrReplace": {
                    "object": {
                        "database": dataset_name,
                        "table": table_name
                    },
                    "table": tmsl
                }
            })
        else:
            # Assume it's a general model update, wrap with database createOrReplace
            final_tmsl = json.dumps({
                "createOrReplace": {
                    "object": {
                        "database": dataset_name
                    },
                    "database": tmsl
                }
            })

        retval: XmlaResultCollection = server.Execute(final_tmsl)
        
        # Check if the execution was successful by examining the XmlaResultCollection
        if retval is None:
            return f"TMSL definition updated successfully for dataset '{dataset_name}' in workspace '{workspace_name}'. ✅"
        
        # Iterate through the XmlaResultCollection to check for errors or messages
        errors = []
        messages = []
        warnings = []
        
        for result in retval:
            # Check for errors in the result
            if hasattr(result, 'HasErrors') and result.HasErrors:
                if hasattr(result, 'Messages'):
                    for message in result.Messages:
                        if hasattr(message, 'MessageType'):
                            if str(message.MessageType).lower() == 'error':
                                errors.append(str(message.Description) if hasattr(message, 'Description') else str(message))
                            elif str(message.MessageType).lower() == 'warning':
                                warnings.append(str(message.Description) if hasattr(message, 'Description') else str(message))
                            else:
                                messages.append(str(message.Description) if hasattr(message, 'Description') else str(message))
                        else:
                            # If no MessageType, treat as general message
                            messages.append(str(message.Description) if hasattr(message, 'Description') else str(message))
            elif hasattr(result, 'Messages'):
                # No explicit errors, but check messages anyway
                for message in result.Messages:
                    if hasattr(message, 'MessageType'):
                        if str(message.MessageType).lower() == 'error':
                            errors.append(str(message.Description) if hasattr(message, 'Description') else str(message))
                        elif str(message.MessageType).lower() == 'warning':
                            warnings.append(str(message.Description) if hasattr(message, 'Description') else str(message))
                        else:
                            messages.append(str(message.Description) if hasattr(message, 'Description') else str(message))
                    else:
                        messages.append(str(message.Description) if hasattr(message, 'Description') else str(message))
        
        # Determine the result based on what we found
        if errors:
            error_details = "; ".join(errors)
            return f"Error updating TMSL definition for dataset '{dataset_name}' in workspace '{workspace_name}': {error_details}"
        elif warnings:
            warning_details = "; ".join(warnings)
            success_msg = f"TMSL definition updated for dataset '{dataset_name}' in workspace '{workspace_name}' with warnings: {warning_details} ⚠️"
            if messages:
                success_msg += f" Additional info: {'; '.join(messages)}"
            return success_msg
        elif messages:
            message_details = "; ".join(messages)
            return f"TMSL definition updated for dataset '{dataset_name}' in workspace '{workspace_name}'. Server messages: {message_details} ✅"
        else:
            # No errors, warnings, or messages - successful execution
            return f"TMSL definition updated successfully for dataset '{dataset_name}' in workspace '{workspace_name}'. ✅"
        
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in TMSL definition - {e}"
    except ConnectionError as e:
        print(f"Connection error in update_model_using_tmsl: {e}")
        return f"Error connecting to Power BI service: {e}"
    except Exception as e:
        # Check if it's an Analysis Services specific error that might contain useful details
        error_message = str(e)
        print(f"Error in update_model_using_tmsl: {e}")
        
        # Provide more context for common error scenarios
        if "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
            return f"Authentication error: {error_message}. Please check your access token and permissions."
        elif "not found" in error_message.lower():
            return f"Dataset or workspace not found: {error_message}. Please verify the workspace name '{workspace_name}' and dataset name '{dataset_name}' are correct."
        elif "permission" in error_message.lower() or "access" in error_message.lower():
            return f"Permission error: {error_message}. You may not have sufficient permissions to modify this dataset."
        else:
            return f"Error updating TMSL definition: {error_message}"
    finally:
        # Ensure server connection is always closed
        try:
            if server and hasattr(server, 'Connected') and server.Connected:
                server.Disconnect()
        except:
            pass  # Ignore errors during cleanup
    
@mcp.tool
def get_model_definition(workspace_name:str = None, dataset_name:str=None) -> str:
    """Gets TMSL definition for an Analysis Services Model.
    This tool connects to the specified Power BI workspace and dataset name, retrieves the model definition,
    and returns the TMSL definition as a string.
    The function connects to the Power BI service using an access token, retrieves the model definition,
    and returns the result.
    Note: The workspace_name and dataset_name should be valid names in the Power BI service.
    """
    

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotnet_dir = os.path.join(script_dir, "dotnet")
    
    print(f"Using .NET assemblies from: {dotnet_dir}")
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.Tabular.dll"))
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.Identity.Client.dll"))
    clr.AddReference(os.path.join(dotnet_dir, "Microsoft.IdentityModel.Abstractions.dll"))
    
    from Microsoft.AnalysisServices.Tabular import Server,Database, JsonSerializer,SerializeOptions # type: ignore

    access_token = get_access_token()
    if not access_token:
        return "Error: No valid access token available"

    # Use URL-encoded workspace name and standard XMLA connection format

    workspace_name = urllib.parse.quote(workspace_name)
    connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name};Password={access_token}"

    server: Server = Server()
    server.Connect(connection_string)
    database: Database = server.Databases.GetByName(dataset_name)

    options = SerializeOptions()
    options.IgnoreTimestamps = True

    tmsl_definition = JsonSerializer.SerializeDatabase(database, options)
    return tmsl_definition



def register_tom_tools(mcp_instance):
    """Register TOM (Tabular Object Model) tools for enhanced semantic model operations."""
    
    from tools.tom_semantic_model_tools_python import (
        tom_connect_to_model, 
        tom_list_model_tables, 
        tom_add_measure_to_model,
        tom_update_measure_in_model,
        tom_delete_measure_from_model,
        tom_get_measure_info,
        tom_add_table_to_model,
        tom_update_table_in_model,
        tom_delete_table_from_model,
        tom_add_column_to_table,
        tom_update_column_in_table,
        tom_add_relationship_to_model,
        # Enhanced functions with proper database selection
        tom_connect_to_server_and_database,
        tom_list_tables_by_database_name,
        tom_add_measure_by_database_name,
        # NEW: Complete model creation functions
        tom_create_empty_semantic_model_with_auth,
        tom_add_lakehouse_expression_with_auth,
        tom_add_table_with_lakehouse_partition_with_auth,
        tom_add_data_source_expression,
        tom_add_relationships_to_model,
        tom_discover_lakehouse_schema,
        tom_create_complete_model_from_lakehouse,
        # NEW: Model refresh functions for relationship recalculation
        tom_refresh_semantic_model,
        tom_refresh_model_after_relationships
    )
    
    @mcp_instance.tool()
    def tom_add_measure_to_semantic_model(
        connection_string: str,
        table_name: str,
        measure_name: str,
        expression: str,
        format_string: Optional[str] = None,
        description: Optional[str] = None,
        display_folder: Optional[str] = None
    ) -> str:
        """
        Add a measure to a semantic model using the Tabular Object Model (TOM).
        
        TOM provides a superior approach to TMSL for incremental model changes:
        - Object-oriented API with strong typing
        - Incremental changes without risk of deleting existing objects
        - Built-in validation and relationship management
        - No need to reconstruct entire table definitions
        
        This tool works with both Power BI Service and local Power BI Desktop instances.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Target table name where the measure will be added
            measure_name: Name of the new measure
            expression: DAX expression for the measure (e.g., "SUM(Sales[Amount])")
            format_string: Optional format string (e.g., "$#,##0.00", "0.00%")
            description: Optional description for the measure
            display_folder: Optional display folder for organizing measures (e.g., "📊 Sales Metrics")
            
        Returns:
            JSON string with operation results, including success status and measure details
        """
        return tom_add_measure_to_model(
            connection_string=connection_string,
            table_name=table_name,
            measure_name=measure_name,
            expression=expression,
            format_string=format_string,
            description=description,
            display_folder=display_folder
        )
    
    @mcp_instance.tool()
    def tom_connect_to_semantic_model(
        connection_string: str
    ) -> str:
        """
        Connect to a semantic model using TOM and get model information.
        
        This tool verifies that TOM can successfully connect to a semantic model
        and provides information about the model structure.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            
        Returns:
            JSON string with connection results and model information
        """
        return tom_connect_to_model(connection_string)
    
    @mcp_instance.tool()
    def tom_list_tables_in_model(
        connection_string: str
    ) -> str:
        """
        List all tables in a semantic model using TOM.
        
        This tool provides detailed information about tables, columns, and measures
        in the semantic model using the Tabular Object Model.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            
        Returns:
            JSON string with table, column, and measure information
        """
        return tom_list_model_tables(connection_string)
    
    @mcp_instance.tool()
    def tom_get_measure_details(
        connection_string: str,
        table_name: str,
        measure_name: str
    ) -> str:
        """
        Get detailed information about a specific measure using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the table containing the measure
            measure_name: Name of the measure
            
        Returns:
            JSON string with measure details
        """
        return tom_get_measure_info(connection_string, table_name, measure_name)

    @mcp_instance.tool()
    def tom_update_measure_in_semantic_model(
        connection_string: str,
        table_name: str,
        measure_name: str,
        expression: Optional[str] = None,
        format_string: Optional[str] = None,
        description: Optional[str] = None,
        display_folder: Optional[str] = None
    ) -> str:
        """
        Update an existing measure in a semantic model using the Tabular Object Model (TOM).
        
        This tool allows you to modify specific properties of an existing measure without
        affecting other measures or table structures. You can update:
        - DAX expression
        - Format string (e.g., "$#,##0.00", "0.00%")
        - Description
        - Display folder
        
        Only the properties you specify will be updated; others remain unchanged.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the table containing the measure
            measure_name: Name of the measure to update
            expression: Optional new DAX expression for the measure
            format_string: Optional new format string for the measure
            description: Optional new description for the measure
            display_folder: Optional new display folder for the measure
            
        Returns:
            JSON string with operation results, including what changes were made
        """
        return tom_update_measure_in_model(
            connection_string=connection_string,
            table_name=table_name,
            measure_name=measure_name,
            expression=expression,
            format_string=format_string,
            description=description,
            display_folder=display_folder
        )

    @mcp_instance.tool()
    def tom_delete_measure_from_semantic_model(
        connection_string: str,
        table_name: str,
        measure_name: str
    ) -> str:
        """
        Delete a measure from a semantic model using the Tabular Object Model (TOM).
        
        This tool permanently removes a measure from the specified table. 
        Use with caution as this action cannot be undone.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the table containing the measure
            measure_name: Name of the measure to delete
            
        Returns:
            JSON string with operation results, including details of the deleted measure
        """
        return tom_delete_measure_from_model(
            connection_string=connection_string,
            table_name=table_name,
            measure_name=measure_name
        )

    # ===== TABLE MANAGEMENT TOOLS =====
    
    @mcp_instance.tool()
    def tom_add_table_to_semantic_model(
        connection_string: str,
        table_name: str,
        description: Optional[str] = None
    ) -> str:
        """
        Add a new table to a semantic model using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the new table
            description: Optional description for the table
            
        Returns:
            JSON string with operation results
        """
        return tom_add_table_to_model(
            connection_string=connection_string,
            table_name=table_name,
            description=description
        )
    
    @mcp_instance.tool()
    def tom_update_table_in_semantic_model(
        connection_string: str,
        table_name: str,
        new_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Update an existing table in a semantic model using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Current name of the table
            new_name: Optional new name for the table
            description: Optional new description for the table
            
        Returns:
            JSON string with operation results
        """
        return tom_update_table_in_model(
            connection_string=connection_string,
            table_name=table_name,
            new_name=new_name,
            description=description
        )
    
    @mcp_instance.tool()
    def tom_delete_table_from_semantic_model(
        connection_string: str,
        table_name: str
    ) -> str:
        """
        Delete a table from a semantic model using TOM.
        
        WARNING: This will permanently delete the table and all its columns, measures, and data!
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the table to delete
            
        Returns:
            JSON string with operation results
        """
        return tom_delete_table_from_model(
            connection_string=connection_string,
            table_name=table_name
        )

    # ===== COLUMN MANAGEMENT TOOLS =====
    
    @mcp_instance.tool()
    def tom_add_column_to_semantic_table(
        connection_string: str,
        table_name: str,
        column_name: str,
        data_type: str = "String",
        source_column: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Add a new column to a table in a semantic model using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the table to add the column to
            column_name: Name of the new column
            data_type: Data type of the column (String, Int64, Double, Boolean, DateTime)
            source_column: Optional source column reference for calculated columns
            description: Optional description for the column
            
        Returns:
            JSON string with operation results
        """
        return tom_add_column_to_table(
            connection_string=connection_string,
            table_name=table_name,
            column_name=column_name,
            data_type=data_type,
            source_column=source_column,
            description=description
        )
    
    @mcp_instance.tool()
    def tom_update_column_in_semantic_table(
        connection_string: str,
        table_name: str,
        column_name: str,
        new_name: Optional[str] = None,
        description: Optional[str] = None,
        expression: Optional[str] = None
    ) -> str:
        """
        Update an existing column in a table using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            table_name: Name of the table containing the column
            column_name: Current name of the column
            new_name: Optional new name for the column
            description: Optional new description for the column
            expression: Optional new expression for calculated columns
            
        Returns:
            JSON string with operation results
        """
        return tom_update_column_in_table(
            connection_string=connection_string,
            table_name=table_name,
            column_name=column_name,
            new_name=new_name,
            description=description,
            expression=expression
        )

    # ===== RELATIONSHIP MANAGEMENT TOOLS =====
    
    @mcp_instance.tool()
    def tom_add_relationship_to_semantic_model(
        connection_string: str,
        from_table: str,
        from_column: str,
        to_table: str,
        to_column: str,
        cross_filtering_behavior: str = "OneDirection"
    ) -> str:
        """
        Add a relationship between two tables in a semantic model using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            from_table: Name of the source table
            from_column: Name of the source column
            to_table: Name of the target table
            to_column: Name of the target column
            cross_filtering_behavior: Cross filtering behavior ("OneDirection", "BothDirections")
            
        Returns:
            JSON string with operation results
        """
        return tom_add_relationship_to_model(
            connection_string=connection_string,
            from_table=from_table,
            from_column=from_column,
            to_table=to_table,
            to_column=to_column,
            cross_filtering_behavior=cross_filtering_behavior
        )
    
    @mcp_instance.tool()
    def tom_add_single_relationship_to_powerbi_service(
        workspace_name: str,
        dataset_name: str,
        from_table: str,
        from_column: str,
        to_table: str,
        to_column: str,
        cross_filtering_behavior: str = "OneDirection"
    ) -> str:
        """
        Add a single relationship to a Power BI Service semantic model using TOM with automatic authentication.
        
        This enhanced TOM function automatically handles Power BI Service authentication and connection string construction,
        making it easy to add relationships to cloud-hosted semantic models without manual token management.
        
        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name
            from_table: Name of the source table
            from_column: Name of the source column
            to_table: Name of the target table
            to_column: Name of the target column
            cross_filtering_behavior: Cross filtering behavior ("OneDirection", "BothDirections")
            
        Returns:
            JSON string with operation results, including success status and relationship details
        """
        import urllib.parse
        import json
        
        # Get access token for Power BI Service authentication
        access_token = get_access_token()
        if not access_token:
            return json.dumps({
                "success": False,
                "error": "No valid access token available. Please check authentication.",
                "error_type": "authentication_error"
            }, indent=2)
        
        # Validate required parameters
        if not workspace_name or not workspace_name.strip():
            return json.dumps({
                "success": False,
                "error": "Workspace name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        if not dataset_name or not dataset_name.strip():
            return json.dumps({
                "success": False,
                "error": "Dataset name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        # Construct Power BI Service connection string WITHOUT catalog
        # Let TOM select the database by name instead  
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        server_connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        # Create relationship list for the enhanced function
        relationships_list = [{
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column,
            "cross_filtering_behavior": cross_filtering_behavior
        }]
        
        # Use enhanced TOM function with fixed relationship logic
        return tom_add_relationships_to_model(
            connection_string=server_connection_string,
            database_name=dataset_name,
            relationships_info=relationships_list
        )

    # Enhanced TOM functions for Power BI Service
    @mcp_instance.tool()
    def tom_add_measure_to_powerbi_service(
        workspace_name: str,
        dataset_name: str,
        table_name: str,
        measure_name: str,
        expression: str,
        format_string: Optional[str] = None,
        description: Optional[str] = None,
        display_folder: Optional[str] = None
    ) -> str:
        """
        Add a measure to a Power BI Service semantic model using TOM with automatic authentication.
        
        This enhanced TOM function automatically handles Power BI Service authentication and connection string construction,
        making it easy to add measures to cloud-hosted semantic models without manual token management.
        
        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name
            table_name: Target table name where the measure will be added
            measure_name: Name of the new measure
            expression: DAX expression for the measure (e.g., "SUM(Sales[Amount])")
            format_string: Optional format string (e.g., "$#,##0.00", "0.00%")
            description: Optional description for the measure
            display_folder: Optional display folder for organizing measures (e.g., "📊 Sales Metrics")
            
        Returns:
            JSON string with operation results, including success status and measure details
        """
        import urllib.parse
        
        # Get access token for Power BI Service authentication
        access_token = get_access_token()
        if not access_token:
            return json.dumps({
                "success": False,
                "error": "No valid access token available. Please check authentication.",
                "error_type": "authentication_error"
            }, indent=2)
        
        # Validate required parameters
        if not workspace_name or not workspace_name.strip():
            return json.dumps({
                "success": False,
                "error": "Workspace name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        if not dataset_name or not dataset_name.strip():
            return json.dumps({
                "success": False,
                "error": "Dataset name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        # Construct Power BI Service connection string WITHOUT catalog
        # Let TOM select the database by name instead  
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        server_connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        # Use enhanced TOM function with explicit database selection
        return tom_add_measure_by_database_name(
            server_connection_string=server_connection_string,
            database_name=dataset_name,
            table_name=table_name,
            measure_name=measure_name,
            expression=expression,
            format_string=format_string,
            description=description,
            display_folder=display_folder
        )

    @mcp_instance.tool()
    def tom_list_tables_in_powerbi_service(
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        List all tables in a Power BI Service semantic model using TOM with automatic authentication.
        
        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name
            
        Returns:
            JSON string with table, column, and measure information
        """
        import urllib.parse
        
        # Get access token for Power BI Service authentication
        access_token = get_access_token()
        if not access_token:
            return json.dumps({
                "success": False,
                "error": "No valid access token available. Please check authentication.",
                "error_type": "authentication_error"
            }, indent=2)
        
        # Construct Power BI Service connection string WITHOUT catalog
        # Let TOM select the database by name instead
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        server_connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        # Use enhanced TOM function with explicit database selection
        return tom_list_tables_by_database_name(
            server_connection_string=server_connection_string,
            database_name=dataset_name
        )

    @mcp_instance.tool()
    def tom_add_relationships_to_powerbi_service(
        workspace_name: str,
        dataset_name: str,
        relationships_info: str  # JSON string with relationship list
    ) -> str:
        """
        Add relationships to a Power BI Service semantic model using TOM with automatic authentication.
        
        This enhanced TOM function automatically handles Power BI Service authentication and connection string construction,
        making it easy to add relationships to cloud-hosted semantic models without manual token management.
        
        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name
            relationships_info: JSON string with list of relationship dictionaries
                Each relationship should have: from_table, from_column, to_table, to_column
                Optional: cross_filtering_behavior ("OneDirection" or "BothDirections")
            
        Returns:
            JSON string with operation results, including success status and relationship details
        """
        import urllib.parse
        import json
        
        # Get access token for Power BI Service authentication
        access_token = get_access_token()
        if not access_token:
            return json.dumps({
                "success": False,
                "error": "No valid access token available. Please check authentication.",
                "error_type": "authentication_error"
            }, indent=2)
        
        # Validate required parameters
        if not workspace_name or not workspace_name.strip():
            return json.dumps({
                "success": False,
                "error": "Workspace name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        if not dataset_name or not dataset_name.strip():
            return json.dumps({
                "success": False,
                "error": "Dataset name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        # Parse relationships JSON
        try:
            relationships_list = json.loads(relationships_info)
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON in relationships_info: {str(e)}",
                "error_type": "parameter_error"
            }, indent=2)
        
        # Construct Power BI Service connection string WITHOUT catalog
        # Let TOM select the database by name instead  
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        server_connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        # Use enhanced TOM function with fixed relationship logic
        return tom_add_relationships_to_model(
            connection_string=server_connection_string,
            database_name=dataset_name,
            relationships_info=relationships_list
        )

    # ============================================================================
    # COMPREHENSIVE MODEL CREATION TOOLS USING TOM
    # ============================================================================



    @mcp_instance.tool()
    def tom_create_empty_model_with_auth(
        workspace_name: str,
        database_name: str,
        compatibility_level: int = 1604
    ) -> str:
        """
        Create a new empty semantic model (database) using TOM with automatic Power BI Service authentication.
        
        Args:
            workspace_name: The Power BI workspace name
            database_name: Name for the new database/semantic model
            compatibility_level: Compatibility level for the model (default: 1604)
            
        Returns:
            JSON string with operation results
        """
        return tom_create_empty_semantic_model_with_auth(workspace_name, database_name, compatibility_level)



    @mcp_instance.tool()
    def tom_add_lakehouse_expression_with_auth(
        workspace_name: str,
        database_name: str,
        lakehouse_server: str,
        lakehouse_endpoint_id: str
    ) -> str:
        """
        Add DatabaseQuery expression for DirectLake connectivity to lakehouse with automatic authentication.
        This MUST be created before adding tables with DirectLake partitions.
        
        Args:
            workspace_name: The Power BI workspace name
            database_name: Name of the semantic model/database
            lakehouse_server: SQL Analytics Endpoint server name
            lakehouse_endpoint_id: SQL Analytics Endpoint ID/database name
        
        Returns:
            JSON string with operation results
        """
        from tools.tom_semantic_model_tools_python import tom_add_lakehouse_expression_with_auth
        return tom_add_lakehouse_expression_with_auth(workspace_name, database_name, lakehouse_server, lakehouse_endpoint_id)

    @mcp_instance.tool()
    def tom_add_table_with_lakehouse_partition_with_auth(
        workspace_name: str,
        database_name: str,
        table_name: str,
        columns_info: str,
        schema_name: str = "dbo"
    ) -> str:
        """
        Add a complete table with columns and DirectLake partition using TOM with automatic authentication.
        
        Args:
            workspace_name: The Power BI workspace name
            database_name: Name of the target database
            table_name: Name of the table to create
            columns_info: JSON string with list of column information dictionaries
            schema_name: Schema name in the lakehouse (default: "dbo")
            
        Returns:
            JSON string with operation results
        """
        import json
        from tools.tom_semantic_model_tools_python import tom_add_table_with_lakehouse_partition_with_auth
        columns_list = json.loads(columns_info)
        return tom_add_table_with_lakehouse_partition_with_auth(workspace_name, database_name, table_name, columns_list, schema_name)

    @mcp_instance.tool()
    def tom_add_lakehouse_data_source(
        connection_string: str,
        database_name: str,
        server_name: str,
        endpoint_id: str
    ) -> str:
        """
        Add the data source expression for DirectLake connectivity to lakehouse.
        
        Args:
            connection_string: Connection string for Analysis Services server
            database_name: Name of the target database
            server_name: SQL Analytics Endpoint server name
            endpoint_id: SQL Analytics Endpoint ID
            
        Returns:
            JSON string with operation results
        """
        return tom_add_data_source_expression(connection_string, database_name, server_name, endpoint_id)



    @mcp_instance.tool()
    def tom_add_model_relationships(
        connection_string: str,
        database_name: str,
        relationships_info: str  # JSON string of relationship information
    ) -> str:
        """
        Add relationships between tables using TOM.
        
        Args:
            connection_string: Connection string for Analysis Services server
            database_name: Name of the target database
            relationships_info: JSON string with list of relationship dictionaries
            
        Returns:
            JSON string with operation results
        """
        import json
        try:
            relationships_list = json.loads(relationships_info)
            return tom_add_relationships_to_model(connection_string, database_name, relationships_list)
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON in relationships_info: {str(e)}"
            })

    @mcp_instance.tool()
    def tom_discover_lakehouse_tables(
        workspace_id: str,
        lakehouse_id: str = None,
        lakehouse_name: str = None
    ) -> str:
        """
        Discover tables and their schema from a Fabric lakehouse using SQL Analytics Endpoint.
        
        Args:
            workspace_id: The Fabric workspace ID
            lakehouse_id: Optional lakehouse ID
            lakehouse_name: Optional lakehouse name (alternative to lakehouse_id)
            
        Returns:
            JSON string with table schema information
        """
        return tom_discover_lakehouse_schema(workspace_id, lakehouse_id, lakehouse_name)

    @mcp_instance.tool()
    def tom_create_model_from_lakehouse(
        connection_string: str,
        database_name: str,
        workspace_id: str,
        lakehouse_id: str = None,
        lakehouse_name: str = None,
        table_names: str = None,  # JSON string of table names
        relationships: str = None  # JSON string of relationships
    ) -> str:
        """
        Create a complete DirectLake semantic model from a Fabric lakehouse.
        
        This orchestrates the entire process:
        1. Discover lakehouse schema
        2. Create empty semantic model
        3. Add data source expression
        4. Add tables with columns and partitions
        5. Add relationships (if provided)
        
        Args:
            connection_string: Connection string for Analysis Services server
            database_name: Name for the new semantic model
            workspace_id: Fabric workspace ID containing the lakehouse
            lakehouse_id: Optional lakehouse ID
            lakehouse_name: Optional lakehouse name
            table_names: Optional JSON string of specific tables to include
            relationships: Optional JSON string of relationships to create
            
        Returns:
            JSON string with complete operation results
        """
        import json
        
        try:
            # Parse optional JSON parameters
            table_names_list = None
            if table_names:
                table_names_list = json.loads(table_names)
                
            relationships_list = None
            if relationships:
                relationships_list = json.loads(relationships)
            
            return tom_create_complete_model_from_lakehouse(
                connection_string, database_name, workspace_id, 
                lakehouse_id, lakehouse_name, table_names_list, relationships_list
            )
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Invalid JSON in parameters: {str(e)}"
            })

    # ============================================================================
    # MODEL REFRESH TOOLS FOR RELATIONSHIP RECALCULATION
    # ============================================================================

    @mcp_instance.tool()
    def tom_refresh_semantic_model_tool(
        connection_string: str,
        database_name: str,
        refresh_type: str = "calculate"
    ) -> str:
        """
        Refresh a semantic model to recalculate relationships and update data.
        
        This is essential after creating relationships in DirectLake models to ensure
        they are properly calculated and functional.
        
        Args:
            connection_string: Connection string for Analysis Services (e.g., "Data Source=localhost:65304" for local Desktop)
            database_name: Name of the database/semantic model to refresh
            refresh_type: Type of refresh ("full", "automatic", "dataOnly", "calculate", "clearValues")
            
        Returns:
            JSON string with refresh operation results
        """
        return tom_refresh_semantic_model(connection_string, database_name, refresh_type)

    @mcp_instance.tool()
    def tom_refresh_powerbi_service_model(
        workspace_name: str,
        dataset_name: str,
        refresh_type: str = "calculate"
    ) -> str:
        """
        Refresh a Power BI Service semantic model with automatic authentication.
        
        This function automatically handles Power BI Service authentication and is
        essential after creating relationships to ensure they are properly calculated.
        
        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to refresh
            refresh_type: Type of refresh ("calculate", "full", "automatic", "dataOnly", "clearValues")
            
        Returns:
            JSON string with refresh operation results
        """
        import urllib.parse
        import json
        
        # Get access token for Power BI Service authentication
        access_token = get_access_token()
        if not access_token:
            return json.dumps({
                "success": False,
                "error": "No valid access token available. Please check authentication.",
                "error_type": "authentication_error"
            }, indent=2)
        
        # Validate required parameters
        if not workspace_name or not workspace_name.strip():
            return json.dumps({
                "success": False,
                "error": "Workspace name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        if not dataset_name or not dataset_name.strip():
            return json.dumps({
                "success": False,
                "error": "Dataset name is required and cannot be empty.",
                "error_type": "parameter_error"
            }, indent=2)
        
        # Construct Power BI Service connection string
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        server_connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        # Use the core refresh function
        return tom_refresh_semantic_model(server_connection_string, dataset_name, refresh_type)

def main():
    """Main entry point for the Semantic Model MCP Server."""

    # Register tool modules
    register_bpa_tools(mcp)
    register_powerbi_desktop_tools(mcp)
    register_microsoft_learn_tools(mcp)
    register_chart_tools(mcp)  # Legacy Vega-Lite charts
    register_tom_tools(mcp)  # NEW: TOM-based semantic model tools
    
    # Register new Dash dashboard tools
    try:
        from tools.dash_tools import register_dash_tools
        register_dash_tools(mcp)
        logging.info("Dash dashboard tools registered successfully")
    except ImportError as e:
        logging.warning(f"Dash tools not available: {e}")
    except Exception as e:
        logging.error(f"Error registering Dash tools: {e}")

    logging.info("Starting Semantic Model MCP Server")
    mcp.run()

if __name__ == "__main__":
    main()
