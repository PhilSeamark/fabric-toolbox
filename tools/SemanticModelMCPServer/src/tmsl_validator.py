"""
TMSL Validation Helper Module

This module contains validation functions for TMSL (Tabular Model Scripting Language) definitions,
supporting both Import and DirectLake models. It provides comprehensive validation to prevent common
deployment failures and structural issues.

Functions:
- validate_tmsl_structure: Main validation function for complete TMSL definitions (supports Import and DirectLake)
- validate_single_table_tmsl: Specialized validation for single table updates
- detect_model_type: Helper function to detect if model is Import or DirectLake
"""

import json
from typing import Dict, Any


def detect_model_type(model: Dict[str, Any]) -> str:
    """Detects the model type (Import or DirectLake) based on partition modes.
    
    Args:
        model: The model section of the TMSL definition
    
    Returns:
        str: "import", "directlake", "mixed", or "unknown"
    """
    if "tables" not in model:
        return "unknown"
    
    partition_modes = set()
    
    for table in model["tables"]:
        if "partitions" in table:
            for partition in table["partitions"]:
                mode = partition.get("mode", "unknown")
                partition_modes.add(mode)
    
    if not partition_modes:
        return "unknown"
    elif "directLake" in partition_modes and "import" in partition_modes:
        return "mixed"
    elif "directLake" in partition_modes:
        return "directlake"
    elif "import" in partition_modes:
        return "import"
    else:
        return "unknown"


def validate_tmsl_structure(tmsl_definition: str) -> Dict[str, Any]:
    """Validates TMSL structure for common mistakes and required components.
    Supports both Import and DirectLake models.
    
    Args:
        tmsl_definition: JSON string containing the TMSL definition
    
    Returns:
        dict: {
            "valid": bool,
            "error": str,
            "suggestions": str,
            "summary": str,
            "warnings": str
        }
    """
    try:
        tmsl = json.loads(tmsl_definition)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON syntax: {e}",
            "suggestions": "Fix JSON syntax errors. Use a JSON validator to check your TMSL structure.",
            "summary": "JSON validation failed",
            "warnings": ""
        }
    
    errors = []
    warnings = []
    suggestions = []
    
    # Check for createOrReplace wrapper or extract model content
    model_content = tmsl
    if "createOrReplace" in tmsl:
        if "database" in tmsl["createOrReplace"]:
            model_content = tmsl["createOrReplace"]["database"]
        elif "table" in tmsl["createOrReplace"]:
            # Single table update - different validation
            return validate_single_table_tmsl(tmsl)
    
    # Validate model structure based on model type
    if "model" in model_content:
        model = model_content["model"]
        model_type = detect_model_type(model)
        
        # Apply validation rules based on model type
        if model_type == "directlake":
            # DirectLake specific validation
            validate_directlake_requirements(model, errors, warnings, suggestions)
        elif model_type == "import":
            # Import model validation (more relaxed)
            validate_import_requirements(model, errors, warnings, suggestions)
        elif model_type == "mixed":
            warnings.append("⚠️ Mixed model detected with both Import and DirectLake partitions")
            suggestions.append("Consider using consistent partition modes for better performance")
            # Apply both validations but make DirectLake requirements optional
            validate_import_requirements(model, errors, warnings, suggestions)
            validate_directlake_requirements(model, [], warnings, suggestions, optional=True)
        else:
            warnings.append("⚠️ Could not determine model type - applying basic validation only")
            validate_basic_requirements(model, errors, warnings, suggestions)
        
        # Common validation for all model types
        validate_common_requirements(model, errors, warnings, suggestions)
    
    # Determine validation result
    is_valid = len(errors) == 0
    
    # Build summary
    summary_parts = []
    if len(errors) == 0:
        summary_parts.append("✅ No critical errors found")
    else:
        summary_parts.append(f"❌ {len(errors)} critical errors detected")
    
    if len(warnings) > 0:
        summary_parts.append(f"⚠️ {len(warnings)} warnings")
    
    return {
        "valid": is_valid,
        "error": "\n".join(errors) if errors else "",
        "suggestions": "\n".join(suggestions) if suggestions else "TMSL structure looks good!",
        "summary": " | ".join(summary_parts),
        "warnings": "\n".join(warnings) if warnings else ""
    }


def validate_directlake_requirements(model: Dict[str, Any], errors: list, warnings: list, suggestions: list, optional: bool = False):
    """Validates DirectLake-specific requirements."""
    error_prefix = "⚠️" if optional else "❌ CRITICAL:"
    
    # Check for expressions block with DatabaseQuery
    if "expressions" not in model:
        if not optional:
            errors.append(f"{error_prefix} Missing 'expressions' block - DirectLake models require DatabaseQuery expression")
            suggestions.append("Add expressions block with DatabaseQuery using Sql.Database() function")
    else:
        expressions = model["expressions"]
        database_query_found = False
        for expr in expressions:
            if expr.get("name") == "DatabaseQuery" and expr.get("kind") == "m":
                database_query_found = True
                expression_content = expr.get("expression", "")
                if isinstance(expression_content, list):
                    expression_content = " ".join(expression_content)
                elif isinstance(expression_content, str):
                    pass
                else:
                    expression_content = str(expression_content)
                
                if "Sql.Database" not in expression_content:
                    warnings.append("⚠️ DatabaseQuery expression doesn't contain Sql.Database() function")
                    suggestions.append("Ensure DatabaseQuery uses Sql.Database(server, endpoint_id) format")
        
        if not database_query_found and not optional:
            errors.append(f"{error_prefix} DatabaseQuery expression not found in expressions block")
            suggestions.append("Add DatabaseQuery expression with kind='m' and Sql.Database() function")
    
    # Validate DirectLake partitions
    if "tables" in model:
        for table in model["tables"]:
            table_name = table.get("name", "unnamed_table")
            if "partitions" in table:
                for partition in table["partitions"]:
                    if partition.get("mode") == "directLake":
                        validate_directlake_partition(table_name, partition, errors, warnings, suggestions)


def validate_import_requirements(model: Dict[str, Any], errors: list, warnings: list, suggestions: list):
    """Validates Import model requirements (more flexible than DirectLake)."""
    # Import models can have expressions but don't require DatabaseQuery
    if "expressions" in model:
        expressions = model["expressions"]
        for expr in expressions:
            # Validate expression syntax if present
            if "expression" not in expr:
                warnings.append(f"⚠️ Expression '{expr.get('name', 'unnamed')}' missing 'expression' property")
    
    # Validate Import partitions
    if "tables" in model:
        for table in model["tables"]:
            table_name = table.get("name", "unnamed_table")
            if "partitions" in table:
                for partition in table["partitions"]:
                    if partition.get("mode") == "import":
                        validate_import_partition(table_name, partition, errors, warnings, suggestions)


def validate_basic_requirements(model: Dict[str, Any], errors: list, warnings: list, suggestions: list):
    """Basic validation for models where type cannot be determined."""
    if "tables" not in model:
        errors.append("❌ Model missing 'tables' array")
        suggestions.append("Add tables array to model definition")
        return
    
    for table in model["tables"]:
        table_name = table.get("name", "unnamed_table")
        if "partitions" not in table:
            warnings.append(f"⚠️ Table '{table_name}' missing partitions array")
            suggestions.append(f"Add partitions array to table '{table_name}'")


def validate_common_requirements(model: Dict[str, Any], errors: list, warnings: list, suggestions: list):
    """Validates requirements common to all model types."""
    if "tables" in model:
        for table in model["tables"]:
            table_name = table.get("name", "unnamed_table")
            
            # Check for INVALID table-level mode property (common mistake)
            if "mode" in table:
                errors.append(f"❌ CRITICAL ERROR: Table '{table_name}' has 'mode' property at table level - THIS BREAKS DEPLOYMENT!")
                suggestions.append(f"REMOVE 'mode' from table '{table_name}' - mode belongs in partitions only!")
            
            # Check for INVALID table-level defaultMode property
            if "defaultMode" in table:
                errors.append(f"❌ CRITICAL ERROR: Table '{table_name}' has 'defaultMode' property - INVALID!")
                suggestions.append(f"REMOVE 'defaultMode' from table '{table_name}'")
            
            # Basic partition validation
            if "partitions" in table:
                partitions = table["partitions"]
                if len(partitions) == 0:
                    warnings.append(f"⚠️ Table '{table_name}' has empty partitions array")
                    suggestions.append(f"Add at least one partition to table '{table_name}'")


def validate_directlake_partition(table_name: str, partition: Dict[str, Any], errors: list, warnings: list, suggestions: list):
    """Validates DirectLake partition structure."""
    if "source" not in partition:
        errors.append(f"❌ DirectLake partition in table '{table_name}' missing 'source' property")
        suggestions.append(f"Add source property to DirectLake partition in table '{table_name}'")
    else:
        source = partition["source"]
        if source.get("expressionSource") != "DatabaseQuery":
            warnings.append(f"⚠️ DirectLake partition in table '{table_name}' should use expressionSource='DatabaseQuery'")
            suggestions.append(f"Set expressionSource to 'DatabaseQuery' in table '{table_name}' partition")
        
        if "schemaName" not in source:
            warnings.append(f"⚠️ DirectLake partition in table '{table_name}' missing 'schemaName' - may cause connection issues")
            suggestions.append(f"Add 'schemaName' property to DirectLake partition source in table '{table_name}' (e.g., 'dbo', 'gold')")
        
        if "entityName" not in source:
            errors.append(f"❌ DirectLake partition in table '{table_name}' missing 'entityName'")
            suggestions.append(f"Add 'entityName' property to DirectLake partition source in table '{table_name}'")


def validate_import_partition(table_name: str, partition: Dict[str, Any], errors: list, warnings: list, suggestions: list):
    """Validates Import partition structure."""
    if "source" not in partition:
        errors.append(f"❌ Import partition in table '{table_name}' missing 'source' property")
        suggestions.append(f"Add source property to Import partition in table '{table_name}'")
    else:
        source = partition["source"]
        if "type" not in source:
            warnings.append(f"⚠️ Import partition source in table '{table_name}' missing 'type' property")
            suggestions.append(f"Add 'type' property to Import partition source in table '{table_name}' (e.g., 'm', 'sql')")
        
        if source.get("type") == "m" and "expression" not in source:
            errors.append(f"❌ M partition source in table '{table_name}' missing 'expression' property")
            suggestions.append(f"Add 'expression' property with M query to partition source in table '{table_name}'")


def validate_table_object_preservation(table_content: Dict[str, Any], table_name: str, errors: list, warnings: list, suggestions: list):
    """Validates that table createOrReplace operations include all necessary objects to prevent data loss.
    
    Critical TMSL Rule: When using createOrReplace on a table, you must include ALL existing objects
    (columns, measures, partitions, etc.) or they will be permanently deleted.
    """
    required_objects = ["columns", "partitions"]
    optional_objects = ["measures", "hierarchies", "annotations"]
    
    # Check for required objects
    for obj_type in required_objects:
        if obj_type not in table_content:
            errors.append(f"❌ CRITICAL: Table '{table_name}' missing '{obj_type}' - createOrReplace will DELETE existing {obj_type}!")
            suggestions.append(f"Include ALL existing {obj_type} in table '{table_name}' to prevent data loss")
    
    # Warn about optional objects that might be missing
    for obj_type in optional_objects:
        if obj_type not in table_content:
            warnings.append(f"⚠️ Table '{table_name}' missing '{obj_type}' - existing {obj_type} will be DELETED if they exist!")
            suggestions.append(f"If table '{table_name}' has existing {obj_type}, include them to prevent deletion")
    
    # Specific validation for measures (common operation)
    if "measures" in table_content:
        measures = table_content["measures"]
        if len(measures) == 0:
            warnings.append(f"⚠️ Table '{table_name}' has empty measures array - existing measures will be deleted!")
            suggestions.append(f"Include ALL existing measures in table '{table_name}' or remove empty measures array")
        else:
            # Validate measure structure
            for i, measure in enumerate(measures):
                if "name" not in measure:
                    errors.append(f"❌ Measure #{i+1} in table '{table_name}' missing 'name' property")
                if "expression" not in measure:
                    errors.append(f"❌ Measure '{measure.get('name', f'#{i+1}')}' in table '{table_name}' missing 'expression' property")
    
    # Validate columns if present
    if "columns" in table_content:
        columns = table_content["columns"]
        if len(columns) == 0:
            errors.append(f"❌ CRITICAL: Table '{table_name}' has empty columns array - ALL existing columns will be DELETED!")
            suggestions.append(f"Include ALL existing columns in table '{table_name}' - empty array destroys table structure")
        else:
            for i, column in enumerate(columns):
                if "name" not in column:
                    errors.append(f"❌ Column #{i+1} in table '{table_name}' missing 'name' property")
                if "dataType" not in column:
                    warnings.append(f"⚠️ Column '{column.get('name', f'#{i+1}')}' in table '{table_name}' missing 'dataType' property")


def validate_single_table_tmsl(tmsl: Dict[str, Any]) -> Dict[str, Any]:
    """Validates TMSL for single table updates with comprehensive object preservation checks.
    
    Args:
        tmsl: Parsed TMSL dictionary for single table operations
    
    Returns:
        dict: Validation result with same structure as validate_tmsl_structure
    """
    table_content = tmsl.get("createOrReplace", {}).get("table", {})
    table_name = table_content.get("name", "unnamed_table")
    
    errors = []
    suggestions = []
    warnings = []
    
    # CRITICAL: Add object preservation validation first
    validate_table_object_preservation(table_content, table_name, errors, warnings, suggestions)
    
    # Add critical warning about table-level operations
    warnings.insert(0, f"🔥 CRITICAL WARNING: createOrReplace on table '{table_name}' will REPLACE entire table!")
    warnings.insert(1, f"🔥 Any existing objects not included will be PERMANENTLY DELETED!")
    suggestions.insert(0, f"VERIFY: Include ALL existing columns, measures, partitions, and hierarchies in table '{table_name}'")
    suggestions.insert(1, f"BACKUP: Export current table structure before applying changes to table '{table_name}'")
    
    # Determine table type based on partitions
    table_type = "unknown"
    if "partitions" in table_content:
        for partition in table_content["partitions"]:
            mode = partition.get("mode", "unknown")
            if mode == "directLake":
                table_type = "directlake"
                break
            elif mode == "import":
                table_type = "import"
                break
    
    # Apply common validation
    validate_common_requirements({"tables": [table_content]}, errors, warnings, suggestions)
    
    # Apply type-specific validation
    if table_type == "directlake":
        # Check partitions for DirectLake requirements
        if "partitions" in table_content:
            directlake_partition_found = False
            for partition in table_content["partitions"]:
                if partition.get("mode") == "directLake":
                    directlake_partition_found = True
                    validate_directlake_partition(table_name, partition, errors, warnings, suggestions)
            
            if not directlake_partition_found:
                errors.append(f"❌ CRITICAL: Table '{table_name}' has no DirectLake partition")
                suggestions.append(f"Add partition with mode='directLake' to table '{table_name}'")
    elif table_type == "import":
        # Import table validation
        if "partitions" in table_content:
            for partition in table_content["partitions"]:
                if partition.get("mode") == "import":
                    validate_import_partition(table_name, partition, errors, warnings, suggestions)
    
    return {
        "valid": len(errors) == 0,
        "error": "\n".join(errors),
        "suggestions": "\n".join(suggestions) if suggestions else f"Single table '{table_name}' TMSL structure looks good!",
        "summary": f"Single table '{table_name}' validation ({table_type} type) - DESTRUCTIVE OPERATION WARNING",
        "warnings": "\n".join(warnings) if warnings else ""
    }
