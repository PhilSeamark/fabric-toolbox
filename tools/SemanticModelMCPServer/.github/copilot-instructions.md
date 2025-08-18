## 🚨 **CRITICAL**: Always Activate Required Tools First

**MANDATORY RULE**: When using #semantic_model_mcp_server, ALWAYS activate the required tool categories BEFORE attempting to use any tools. Never assume tools are "disabled" - instead, proactively activate them.

### **🆕 SMART ACTIVATION SYSTEM (Recommended)**:

#### **Option 1: Auto-Detection (Easiest)**
```
smart_activate_tools("I want to run BPA analysis")
smart_activate_tools("Create charts from DAX results")
smart_activate_tools("Analyze local Power BI model")
```

#### **Option 2: Activate Everything (Fastest)**
```
activate_all_powerbi_tools
```

#### **Option 3: Specific Activation (Manual)**
- **For BPA Analysis**: `activate_powerbi_analysis_tools`
- **For Charts/Dashboards**: `activate_powerbi_dashboard_creation`
- **For Power BI Service**: `activate_powerbi_and_lakehouse_tools` 
- **For Local Power BI**: `activate_powerbi_local_development`
- **For Model Creation (TOM)**: `activate_powerbi_tom_management`
- **For TMSL Operations**: `activate_powerbi_tmsl_management`
- **For Lakehouses**: `activate_powerbi_lakehouse_management`

**WORKFLOW**: 
1. **SMART**: Use `smart_activate_tools("describe what you want to do")` for automatic detection
2. **FAST**: Use `activate_all_powerbi_tools` to activate everything at once
3. **MANUAL**: Use specific activation commands for individual categories
4. Then proceed with the requested operation
5. Never tell user "tools are disabled" - just activate them!

**See TOOL_ACTIVATION_GUIDE.md for complete details and examples.**

## Tools
1. **Mandatory** Using semantic_model_mcp_server MCP

## 🚀 PROVEN DirectLake Model Creation Workflow (MODEL_TEST_5 SUCCESS PATTERN)

### **STEP-BY-STEP PROCESS**: Complete Semantic Model Creation

**Use ONLY authentication-enabled `_with_auth` functions for Power BI Service models**

#### 1. Create Empty Model
```
mcp_semantic_mode_tom_create_empty_model_with_auth(
    workspace_name="DAX Performance Tuner Testing",
    database_name="model_name",
    compatibility_level=1604
)
```

#### 2. Add Lakehouse Expression (REQUIRED for DirectLake)
```
mcp_semantic_mode_tom_add_lakehouse_expression_with_auth(
    workspace_name="workspace_name", 
    database_name="model_name",
    lakehouse_server="x6eps4xrq2xudenlfv6naeo3i4-7334lqxnglfurij7lveziwsjdu.msit-datawarehouse.fabric.microsoft.com",
    lakehouse_endpoint_id="c1a9f62a-3a88-4732-b0ee-eae6830723e7"
)
```

#### 3. Add Tables with Correct Data Types
```
mcp_semantic_mode_tom_add_table_with_lakehouse_partition_with_au(
    workspace_name="workspace_name",
    database_name="model_name", 
    table_name="adw_FactInternetSales",  # Use actual lakehouse table names!
    columns_info=[
        {"name": "SalesAmount", "dataType": "Decimal", "sourceColumn": "SalesAmount", "summarizeBy": "Sum"},
        {"name": "OrderQuantity", "dataType": "Int64", "sourceColumn": "OrderQuantity", "summarizeBy": "Sum"},
        {"name": "ProductKey", "dataType": "Int64", "sourceColumn": "ProductKey"}
        # ... all columns with proper data types
    ]
)
```

**CRITICAL DATA TYPE MAPPING**:
- `decimal` SQL → `"Decimal"` with `"summarizeBy": "Sum"` for measures
- `int` SQL → `"Int64"` 
- `varchar` SQL → `"String"`
- `datetime2` SQL → `"DateTime"`
- `float` SQL → `"Double"`

#### 4. Create Relationships
```
mcp_semantic_mode_tom_add_relationships_to_powerbi_service(
    workspace_name="workspace_name",
    dataset_name="model_name",
    relationships_info=[
        {
            "from_table": "adw_FactInternetSales",
            "from_column": "ProductKey",
            "to_table": "adw_DimProduct", 
            "to_column": "ProductKey"
        }
    ]
)
```

#### 5. Refresh Model (MANDATORY after relationships)
```
mcp_semantic_mode_tom_refresh_powerbi_service_model(
    workspace_name="workspace_name",
    dataset_name="model_name",
    refresh_type="calculate"
)
```

#### 6. Add Key Measures
```
mcp_semantic_mode_tom_add_measure_to_powerbi_service(
    workspace_name="workspace_name",
    dataset_name="model_name",
    table_name="adw_FactInternetSales",
    measure_name="Total Sales",
    expression="SUM(adw_FactInternetSales[SalesAmount])",
    format_string="$#,##0.00"
)
```

#### 7. Validate with DAX Query
```
mcp_semantic_mode_execute_dax_query(
    workspace_name="workspace_name",
    dataset_name="model_name", 
    dax_query="EVALUATE SUMMARIZECOLUMNS(adw_DimDate[CalendarYear], \"Total Sales\", [Total Sales])"
)
```

### **CRITICAL SUCCESS FACTORS**

#### ✅ Use Correct Lakehouse Table Names
- **ALWAYS** use `adw_` prefix: `adw_FactInternetSales`, `adw_DimProduct`, `adw_DimDate`
- **NEVER** use generic names like `FactInternetSales`

#### ✅ Validate Lakehouse Schema First
```
mcp_semantic_mode_query_lakehouse_sql_endpoint(
    workspace_id="workspace_id",
    lakehouse_id="lakehouse_id", 
    sql_query="SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'adw_FactInternetSales'"
)
```

#### ✅ Proper Data Types for Numeric Measures
```json
{
    "name": "SalesAmount",
    "dataType": "Decimal",        // NOT "String"!
    "summarizeBy": "Sum"          // NOT "Default" for measures!
}
```

#### ✅ Model Refresh is MANDATORY
- DirectLake relationships require calculation refresh
- Always call `tom_refresh_powerbi_service_model` after adding relationships

### **DEPRECATED - DO NOT USE**
❌ Non-authentication functions (token expiration issues):
- `tom_add_table_with_lakehouse_partition` (use `_with_auth` version)
- `tom_add_lakehouse_expression` (use `_with_auth` version) 
- `tom_create_empty_model` (use `_with_auth` version)
- **NEVER** use generic names like `FactInternetSales`

#### ✅ Validate Lakehouse Schema First
```
mcp_semantic_mode_query_lakehouse_sql_endpoint(
    workspace_id="workspace_id",
    lakehouse_id="lakehouse_id", 
    sql_query="SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'adw_FactInternetSales'"
)
```

#### ✅ Proper Data Types for Numeric Measures
```json
{
    "name": "SalesAmount",
    "dataType": "Decimal",        // NOT "String"!
    "summarizeBy": "Sum"          // NOT "Default" for measures!
}
```

#### ✅ Model Refresh is MANDATORY
- DirectLake relationships require calculation refresh
- Always call `tom_refresh_powerbi_service_model` after adding relationships

### **DEPRECATED - DO NOT USE**
❌ Non-authentication functions (token expiration issues):
- `tom_add_table_with_lakehouse_partition` (use `_with_auth` version)
- `tom_add_lakehouse_expression` (use `_with_auth` version) 
- `tom_create_empty_model` (use `_with_auth` version)

## Lakehouse Configuration (DAX Performance Tuner Testing)
```
Workspace ID: c2c5f7fe-32ed-48cb-a13f-5d49945a491d
Lakehouse ID: 7457b3b9-8f5d-49c5-ba2e-6d6ed1c9cc25
SQL Endpoint: x6eps4xrq2xudenlfv6naeo3i4-7334lqxnglfurij7lveziwsjdu.msit-datawarehouse.fabric.microsoft.com
Endpoint ID: c1a9f62a-3a88-4732-b0ee-eae6830723e7
```

## Hybrid Approach: TMSL for Reading, TOM for Writing

### **PROVEN STRATEGY**: Use TMSL for Model Definition Retrieval, TOM for Model Modifications

**Key Principle**: Leverage the strengths of each approach:
- **TMSL**: Excellent for reading complete model definitions and understanding structure
- **TOM**: Superior for incremental modifications without risk of data loss

#### When to Use TMSL (Reading Operations)
- ✅ **Model Definition Retrieval**: `get_model_definition` or `get_local_powerbi_tmsl_definition`
- ✅ **Structure Analysis**: Understanding tables, columns, measures, relationships
- ✅ **Documentation**: Extracting complete model schemas
- ✅ **Validation**: Comparing before/after states
- ✅ **Backup**: Creating complete model snapshots

#### When to Use TOM (Writing Operations)  
- ✅ **Adding Measures**: `tom_add_measure_to_powerbi_service` or `tom_add_measure_to_semantic_model`
- ✅ **Creating Tables**: `tom_add_table_to_semantic_model`
- ✅ **Adding Columns**: `tom_add_column_to_semantic_table`
- ✅ **Creating Relationships**: `tom_add_relationship_to_semantic_model`
- ✅ **Updating Properties**: `tom_update_measure_in_semantic_model`
- ✅ **Incremental Changes**: Any modification that preserves existing objects

#### Hybrid Workflow Pattern
1. **Check Current State** (TMSL): `get_model_definition` → Understand existing structure
2. **Plan Modifications** (Analysis): Identify what needs to be added/changed
3. **Apply Changes** (TOM): Use specific TOM functions for targeted modifications
4. **Verify Results** (TMSL): `get_model_definition` → Confirm changes applied correctly

## TMSL Reference
When working with TMSL (Tabular Model Scripting Language) objects, **strongly recommend** referring to the official Microsoft Learn documentation:
- https://learn.microsoft.com/en-us/analysis-services/tmsl/tmsl-reference-tabular-objects?view=sql-analysis-services-2025

This article provides the authoritative schema and syntax for TMSL objects including tables, columns, measures, relationships, and all valid properties. Always validate TMSL structure against this reference to ensure compliance and avoid deployment errors.

## Universal TMSL Requirements (Power BI Service & Local Desktop)

### **CRITICAL DISCOVERY**: Universal TMSL Syntax Across All Environments

**Key Finding**: Both Power BI Service and local Power BI Desktop instances use identical TMSL command format for Import and DirectLake models, ensuring consistent deployment patterns across environments.

#### Universal Object Path Format (Both Model Types)
Always use complete object path specification:
```json
{
  "createOrReplace": {
    "object": {
      "database": "ModelName",
      "table": "TableName"
    },
    "table": {
      // Complete table definition required
    }
  }
}
```

#### Universal Complete Object Preservation (Both Model Types)
- **MUST include ALL existing columns** (including system columns like RowNumber)
- **MUST include ALL existing partitions** with complete source definitions
- **MUST include ALL existing measures** with all properties (lineageTag, dataType, etc.)
- **MUST include ALL existing annotations** and changedProperties
- **Missing any existing object will DELETE it permanently**

#### Universal Supported Commands (Power BI Service & Local Desktop)
- ✅ `createOrReplace` with object path - **ONLY supported command for all environments**
- ❌ `alter` - Returns "Unrecognized JSON property: alter" (all environments)
- ❌ `create` - Returns "Unrecognized JSON property: create" (all environments)
- ❌ Table-level without object path - Returns "object is not specified" (all environments)

#### Universal Safe Workflow (Both Model Types)
1. **Extract complete table structure** using `get_model_definition` or `get_local_powerbi_tmsl_definition`
2. **Preserve ALL existing objects** (columns, partitions, measures, annotations)
3. **Add new measure** to existing measures array
4. **Use enhanced validator** to verify no objects will be deleted
5. **Deploy with object path specification** using `update_model_using_tmsl` or `update_local_powerbi_tmsl_definition`

## Local Power BI Desktop Workflow - **PROVEN HYBRID APPROACH**

### **VALIDATED WORKFLOW**: Detect → Read (TMSL) → Modify (TOM) → Verify (TMSL)

**Key Learning**: Hybrid approach combining TMSL reading with TOM writing provides optimal reliability and safety.

#### Step-by-Step Hybrid Process:
1. **Detection**: `detect_local_powerbi_desktop` → Get connection string (e.g., "Data Source=localhost:65304")
2. **Read Current State**: `get_local_powerbi_tmsl_definition` → Extract complete model structure (TMSL)
3. **Plan Modifications**: Analyze current structure to identify required changes
4. **Apply Changes**: Use TOM functions (`tom_add_measure_to_semantic_model`, `tom_add_table_to_semantic_model`, etc.)
5. **Verify Results**: `get_local_powerbi_tmsl_definition` → Confirm changes applied correctly (TMSL)
6. **Test Functionality**: `execute_local_powerbi_dax` → Verify measures work as expected

**🔥 CRITICAL**: Always use TMSL for reading model definitions and TOM for making modifications - this eliminates JSON parsing issues and object deletion risks.

### TOM Database Selection for Power BI Service

**CRITICAL DISCOVERY**: TOM connection string `catalog` parameter is ignored by Power BI Service. Always use explicit database selection:

```python
# ❌ INCORRECT - catalog parameter ignored
connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace};catalog={dataset_name};Password={token};"

# ✅ CORRECT - explicit database selection  
connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace};Password={token};"
database = server.Databases.GetByName(database_name)
```

**Enhanced TOM Functions**: Use functions with explicit database selection:
- `tom_add_measure_to_powerbi_service` - Handles database selection automatically
- `tom_list_tables_in_powerbi_service` - Lists tables from correct database
- `tom_add_measure_by_database_name` - Direct database name specification

## TMSL vs TOM Decision Matrix

### **When to Use TMSL** (Read Operations Only)
| Operation | Tool | Use Case |
|-----------|------|----------|
| **Get Model Definition** | `get_model_definition` | Understanding existing structure before modifications |
| **Extract Table Schema** | `get_local_powerbi_tmsl_definition` | Documenting current state for analysis |
| **Structure Analysis** | TMSL output parsing | Identifying tables, columns, measures, relationships |
| **Validation** | TMSL comparison | Confirming changes were applied correctly |
| **Backup** | TMSL export | Creating complete model snapshots |

### **When to Use TOM** (Write/Modify Operations Only)
| Operation | Tool | Use Case |
|-----------|------|----------|
| **Add Measures** | `tom_add_measure_to_powerbi_service` | Creating new calculations |
| **Create Tables** | `tom_add_table_to_semantic_model` | Adding new data tables |
| **Add Columns** | `tom_add_column_to_semantic_table` | Extending table schemas |
| **Create Relationships** | `tom_add_relationship_to_semantic_model` | Linking tables |
| **Update Properties** | `tom_update_measure_in_semantic_model` | Modifying existing objects |

### **NEVER Use TMSL For** (Risk of Data Loss)
- ❌ Adding measures to existing models (requires complete table reconstruction)
- ❌ Modifying existing objects (deletes missing components)
- ❌ Creating new relationships (complex object preservation required)
- ❌ Any incremental changes (complete model replacement required)

### **NEVER Use TOM For** (Inefficient/Unreliable)
- ❌ Reading complete model definitions (TMSL provides structured output)
- ❌ Structure analysis (TMSL format easier to parse)
- ❌ Documentation extraction (TMSL includes all metadata)
- ❌ Validation checks (TMSL shows complete current state)

### Model Type Differences (Internal Structure Only)

| Aspect | Import Model | DirectLake Model |
|--------|-------------|------------------|
| **Partition Mode** | `import` | `directLake` |
| **Partition Source** | Complex M expressions | Simple entity references |
| **TMSL Commands** | `createOrReplace` only | `createOrReplace` only (Power BI Service & Local Desktop) |
| **Object Path** | Required | Required |
| **Complete Definitions** | Required | Required |

#### DirectLake Partition Structure Example
```json
{
  "name": "partition_name",
  "mode": "directLake",
  "source": {
    "type": "entity",
    "schemaName": "dbo",
    "expressionSource": "DatabaseQuery",
    "entityName": "table_name"
  }
}
```

## TMSL Deployment Best Practices

### Before Making Changes (Use TMSL)
1. **Identify model type** using `get_model_definition` or `get_local_powerbi_tmsl_definition`
2. **Extract current structure** to understand existing objects
3. **Document existing objects** (count columns, measures, partitions)
4. **Plan changes carefully** using structure analysis

### During Development (Use TOM)
1. **Apply targeted modifications** using specific TOM functions
2. **Leverage incremental changes** without full model reconstruction
3. **Maintain object relationships** automatically handled by TOM
4. **Avoid JSON parsing issues** with direct API calls

### After Deployment (Use TMSL)
1. **Verify changes applied** using `get_model_definition` or `get_local_powerbi_tmsl_definition`
2. **Test measure functionality** with DAX queries if applicable
3. **Document successful approaches** for future reference
4. **Compare before/after states** using TMSL structure analysis

### Error Resolution
- **"object is not specified"** → Add proper object path with database and table
- **"Unrecognized JSON property"** → Use only `createOrReplace` for Import models  
- **Missing objects after deployment** → Use TOM instead of TMSL for modifications
- **Authentication issues** → TMSL uses automatic auth, TOM requires explicit tokens

## Summary: When to Use Each Approach

### **Use TMSL When**: Checking, Reading, Understanding Models
- 📊 **Checking model definitions** before making changes
- 🔍 **Reading current structure** to understand what exists
- 📋 **Documenting model schemas** for analysis
- ✅ **Verifying changes** were applied correctly
- 💾 **Creating backups** of complete model state

### **Use TOM When**: Creating, Modifying, Updating Models  
- ➕ **Adding new measures** to existing tables
- 🏗️ **Creating new tables** in the model
- 🔗 **Building relationships** between tables
- ✏️ **Updating existing objects** (measures, columns, tables)
- 🔧 **Any modification** that changes the model

**Remember**: TMSL = Read-only operations, TOM = Write/modify operations

## 🆕 Comprehensive Tool Categories and Enhanced Features

### **🎯 Best Practice Analyzer (BPA) Tools**
The server includes a comprehensive Best Practice Analyzer that evaluates semantic models against industry best practices:

**Available BPA Tools:**
- `analyze_model_bpa` - Analyze a deployed model by workspace/dataset name
- `analyze_tmsl_bpa` - Analyze TMSL definition directly (with automatic JSON formatting)
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

### **🎨 Chart Generation and Visualization Tools**
Comprehensive chart generation capabilities that automatically create visualizations from DAX query results:

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

**Chart Output Files:**
- Charts are saved to the `output` directory
- Interactive charts: `.html` files (can be opened in browser)
- Static charts: `.png` files (high resolution, 300 DPI)
- Reports: `.md` files with analysis summaries

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

### **🔧 Enhanced Tabular Object Model (TOM) Tools**
Advanced TOM-based tools for semantic model manipulation, providing superior reliability for model modifications:

**TOM Advantages over TMSL:**
- **Incremental Changes** - Add/modify individual objects without risk of deleting existing ones
- **Object-Oriented API** - Work with strongly-typed objects instead of complex JSON
- **Built-in Validation** - Automatic relationship management and constraint checking
- **Simpler Syntax** - More intuitive programming model for common operations
- **Enhanced Safety** - No need to reconstruct entire table definitions

**TOM vs TMSL Comparison:**
```
TMSL Approach (Traditional):
1. Get complete table definition
2. Parse complex JSON structure  
3. Add measure to measures array
4. Reconstruct entire table (risk of deletion)
5. Deploy with createOrReplace command

TOM Approach (Enhanced):
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

**TOM Environment Support:**
- ✅ **Local Power BI Desktop** - Direct connection via Analysis Services port
- ✅ **Power BI Service** - XMLA endpoint for Premium workspaces
- ✅ **Azure Analysis Services** - Native TOM support
- ✅ **SQL Server Analysis Services** - Tabular models

### **🔍 Enhanced Local Power BI Desktop Detection Tools**
Automatically discover and connect to running Power BI Desktop instances for local development and testing:

**Enhanced Detection Capabilities:**
- **Automatic Discovery** - Find all running Power BI Desktop instances
- **Port Detection** - Identify Analysis Services ports for each instance
- **Model Information** - Extract model names and connection details
- **Multi-Instance Support** - Handle multiple Power BI Desktop instances simultaneously
- **File Detection** - Identify which .pbix files are currently open
- **Connection Testing** - Validate connectivity to local instances

**Enhanced Detection Functions:**
- `detect_local_powerbi_desktop` - Find all running instances
- `test_local_powerbi_connection` - Test connection to local Analysis Services
- `compare_analysis_services_connections` - Compare connection types and requirements
- `explore_local_powerbi_tables` - List tables in local Power BI Desktop models
- `explore_local_powerbi_columns` - List columns in local models (all or specific table)
- `explore_local_powerbi_measures` - List measures with DAX expressions
- `execute_local_powerbi_dax` - Execute DAX queries against local models

**Local Development Benefits:**
- **No Authentication Required** - Local connections bypass Power BI Service authentication
- **Real-time Testing** - Test changes immediately in your local development environment
- **Model Extraction** - Get TMSL definitions directly from your .pbix files
- **Rapid Prototyping** - Quickly iterate on model designs locally

**Connection Simplicity:**
Power BI Desktop connections are much simpler than Power BI Service connections:
- **Power BI Desktop**: `Data Source=localhost:port` (no authentication required)
- **Power BI Service**: Complex connection string with tokens and authentication
- **Analysis Services**: Windows/SQL authentication required

**Power BI Desktop Connection Information:**
- Power BI Desktop runs a local Analysis Services instance
- Ports are typically dynamic (usually > 50000)
- Connection format: `Data Source=localhost:{port}`
- Each open .pbix file gets its own Analysis Services instance
- Instances are automatically detected when Power BI Desktop is running

### **📚 Microsoft Learn Research Integration**
Enhanced access to Microsoft Learn documentation and research articles:

**Research Capabilities:**
- **DAX (Data Analysis Expressions)** - Functions, syntax, best practices, and examples
- **TMSL (Tabular Model Scripting Language)** - Model definitions, schema updates, and scripting
- **DirectLake** - Implementation guides, best practices, and troubleshooting
- **Power BI** - Features, configuration, and advanced techniques
- **Microsoft Fabric** - Data engineering, analytics, and integration patterns
- **Analysis Services** - Tabular models, performance optimization, and administration
- **Data modeling** - Star schema design, relationships, and performance tuning

**Available Research Functions:**
- `search_learn_microsoft_content` - Search Microsoft Learn documentation
- `get_learn_microsoft_paths` - Get learning paths
- `get_learn_microsoft_modules` - Get training modules
- `get_learn_microsoft_content` - Get specific content by URL

**Research Integration Guidelines:**
When users ask questions about these topics, ALWAYS search Microsoft Learn first to provide the most current and authoritative Microsoft documentation before giving general advice.

**IMPORTANT**: Always refer to https://learn.microsoft.com/en-us/analysis-services/tmsl/tmsl-reference-tabular-objects for authoritative TMSL syntax and schema validation

## 🚀 Enhanced DirectLake Model Creation Features

### **🆕 RECOMMENDED APPROACH - Auto-Generation with Validation**
1. **Step 1**: Use `generate_directlake_tmsl_template` to auto-generate valid TMSL
2. **Step 2**: Use `update_model_using_tmsl` with `validate_only=True` to pre-validate
3. **Step 3**: Use `update_model_using_tmsl` with `validate_only=False` to deploy

**Enhanced Benefits:**
- ✅ Automatic schema validation against lakehouse tables
- ✅ Pre-validated TMSL structure with all required components
- ✅ Proper data type mapping from SQL to DirectLake
- ✅ Built-in validation before deployment
- ✅ Detailed error messages with fix suggestions

### **Enhanced TMSL Validation System**
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

### **🚨 CRITICAL DirectLake Requirements - VALIDATION ENFORCED!**

**MANDATORY #1: TABLE MODE RESTRICTION**  
- ❌ **NEVER ADD**: "mode": "directLake" at the table level (AUTOMATICALLY DETECTED AND BLOCKED)
- ✅ ONLY ADD: "mode": "directLake" in the partition object inside partitions array
- 🚫 TABLE LEVEL: { "name": "TableName", "mode": "directLake" } ← VALIDATION ERROR!
- ✅ PARTITION LEVEL: { "name": "Partition", "mode": "directLake", "source": {...} } ← VALIDATED!

**MANDATORY #2: EXPRESSIONS BLOCK**
- ❌ NEVER FORGET: Every DirectLake model MUST have an "expressions" section (AUTOMATICALLY CHECKED)
- ✅ ALWAYS ADD: expressions block with "DatabaseQuery" using Sql.Database() function
- 🔧 FORMAT: expressions array with name:"DatabaseQuery", kind:"m", expression array

**MANDATORY #3: SCHEMA QUALIFICATION (CRITICAL FIX)**
- ✅ ALWAYS ADD: "schemaName" property in DirectLake partition sources (AUTOMATICALLY DETECTED!)
- ❌ NEVER OMIT: Schema qualification leads to table connection failures
- 🔧 AUTO-DETECTION: System detects 'gold', 'dbo', or first available schema automatically
- 🎯 VALIDATED: Schema name validation prevents common lakehouse connection issues

### **🚫 FORBIDDEN TABLE PROPERTIES - NOW ENFORCED!**
**The validation system blocks these properties in table objects:**
- "mode": "directLake" ← VALIDATION ERROR
- "defaultMode": "directLake" ← VALIDATION ERROR  
- Any mode-related property ← VALIDATION ERROR

## 🎯 Integrated BPA Workflow for Model Development

### **🆕 COMPLETE MODEL DEVELOPMENT WORKFLOW WITH BPA:**

**BPA Integration Points:**
```
# Complete model development workflow with BPA
1. template = generate_directlake_tmsl_template(workspace_id, lakehouse_id, tables, "MyModel")
2. bpa_pre_check = analyze_tmsl_bpa(template)  # ← ANALYZE BEFORE DEPLOYMENT
3. validation = update_model_using_tmsl(workspace, "MyModel", template, validate_only=True)
4. deployment = update_model_using_tmsl(workspace, "MyModel", template, validate_only=False)
5. bpa_final_check = analyze_model_bpa(workspace, "MyModel")  # ← VERIFY DEPLOYED MODEL
```

### **🚨 BPA PRIORITY RULES - FOCUS ON THESE FIRST:**

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

### **🔧 COMMON BPA FIXES FOR DIRECTLAKE MODELS:**

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

### **🔍 BPA TROUBLESHOOTING SCENARIOS:**

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

## 📋 Enhanced Usage Guidelines

### **Schema Validation Best Practices:**
- **ENHANCED**: The `generate_directlake_tmsl_template` tool automatically validates schemas
- **TRADITIONAL**: Use the `query_lakehouse_sql_endpoint` tool to validate table schemas manually
- Do not query all the data in the Lakehouse table - use TOP 5 or similar queries to validate structure
- DirectLake models must exactly match the source Delta table schema - any mismatch will cause deployment failures

**Schema-Aware Query Examples:**
- `"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'your_table_name'"` (works with any schema setup)
- `"SELECT TOP 5 * FROM your_table_name"` (use exact table name from list_fabric_delta_tables)
- `"SELECT TOP 5 * FROM dbo.your_table_name"` (if lakehouse has defaultSchema: "dbo")
- `"SHOW TABLES"` (to see all available tables and their naming patterns)
- `"SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"` (to see schema structure)

**SQL Query Schema Considerations:**
- **Table Naming**: Lakehouse tables can be queried using different naming patterns:
  * **Pattern 1**: `SELECT * FROM table_name` (when lakehouse has no default schema)
  * **Pattern 2**: `SELECT * FROM dbo.table_name` (when lakehouse is schema-enabled with dbo as default)
  * **Pattern 3**: `SELECT * FROM dbo_table_name` (tables prefixed with schema in their actual name)
- **Schema Detection**: Check lakehouse properties - if `"defaultSchema": "dbo"` exists, use schema-qualified names
- **Best Practice**: Try the table name as returned by `list_fabric_delta_tables` first, then try with schema prefix if needed

### **DAX Query Guidelines:**
- **IMPORTANT**: When returning a single value, use braces {} around the expression as a table constructor:
  - CORRECT: EVALUATE {COUNTROWS(table)}
  - INCORRECT: EVALUATE COUNTROWS(table)
- Do not use DAX queries to learn about columns in Lakehouse tables
- NEVER use DAX queries when the user asks for SQL/T-SQL queries
- Use `query_lakehouse_sql_endpoint` tool for SQL queries - never use execute_dax_query for SQL requests
- If SQL query fails, do not follow up with a DAX Query
- Use this tool to validate table schemas, column names, and data types before creating DirectLake models

### **Model Creation Guidelines:**
- **IMPORTANT**: The Sql.Database function takes two arguments: (1) SQL Analytics Endpoint connection string, (2) SQL Analytics Endpoint ID (NOT the lakehouse name or lakehouse ID)
- Use `get_lakehouse_sql_connection_string` tool to get the correct endpoint ID for the Sql.Database function
- Do not use the same name for the model as the Lakehouse, as this can cause conflicts
- Relationships ONLY need the following five properties: `name`, `fromTable`, `fromColumn`, `toTable`, `toColumn`
- Do NOT use the crossFilterBehavior property in relationships for DirectLake models
- When creating a new model, ensure each table only uses columns from the lakehouse tables and not any other source
- Do not create a column called rowNumber or rowNum, as this is a reserved name in DirectLake models
- When creating a new DirectLake model, save the TMSL definition to a file for future reference or updates in the models subfolder
- Do not attempt to modify an existing semantic model when asked to create a new semantic model

### **Fabric Lakehouse Support:**
- Use `list_fabric_lakehouses` to see all lakehouses in a workspace
- Use `list_fabric_delta_tables` to see Delta Tables in a specific lakehouse
- If you don't specify a lakehouse ID, the tool will use the first lakehouse found
- Delta Tables are the primary table format used in Fabric lakehouses

### **Example Queries:**
- "Can you get a list of workspaces?"
- "Can you list notebooks in workspace X?"
- "Show me the lakehouses in this workspace"
- "Search Microsoft Learn for DirectLake best practices"
- "Find DAX documentation for time intelligence functions"
- "Research TMSL syntax for creating DirectLake models"
- "Look up Power BI performance optimization techniques"
- "List all Delta Tables in lakehouse Y"
- "Show me the data pipelines in this workspace"
- "Analyze my model for best practice violations"
- "Generate a BPA report for MyDataset"
- "Show me all performance-related issues in my model"
- "What are the critical errors in my TMSL definition?"

When creating new files in Agent mode to give output or summaries, always add them to the same subfolder called `output`.  These files should have a consistent header and include diagrams as much as possible.