## Tools
1. **Mandatory** Using semantic_model_mcp_server MCP

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

When creating new files in Agent mode to give output or summaries, always add them to the same subfolder called `output`.  These files should have a consistent header and include diagrams as much as possible.