"""
TMSL Table Extraction Helper

This module provides helper functions to safely extract individual table structures
from complete TMSL model definitions for table-level createOrReplace operations.
"""

import json
from typing import Dict, Any, Optional


def extract_table_structure(complete_tmsl: str, table_name: str) -> Dict[str, Any]:
    """
    Extract a specific table's complete structure from a full TMSL model definition.
    
    This function helps create safe table-level TMSL operations by extracting
    ALL existing table objects (columns, measures, partitions, etc.) to prevent
    accidental deletion during createOrReplace operations.
    
    Args:
        complete_tmsl: Complete TMSL model definition (JSON string)
        table_name: Name of table to extract
        
    Returns:
        Dict containing table-level createOrReplace TMSL structure
        
    Raises:
        ValueError: If table not found or TMSL invalid
    """
    try:
        tmsl_data = json.loads(complete_tmsl)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid TMSL JSON: {e}")
    
    # Extract model from various possible structures
    model = None
    if "model" in tmsl_data:
        model = tmsl_data["model"]
    elif "createOrReplace" in tmsl_data and "database" in tmsl_data["createOrReplace"]:
        if "model" in tmsl_data["createOrReplace"]["database"]:
            model = tmsl_data["createOrReplace"]["database"]["model"]
    
    if not model:
        raise ValueError("No model found in TMSL definition")
    
    # Find the target table
    if "tables" not in model:
        raise ValueError("No tables found in model")
    
    target_table = None
    for table in model["tables"]:
        if table.get("name") == table_name:
            target_table = table.copy()  # Deep copy to avoid modifications
            break
    
    if not target_table:
        available_tables = [t.get("name", "unnamed") for t in model["tables"]]
        raise ValueError(f"Table '{table_name}' not found. Available tables: {available_tables}")
    
    # Create table-level TMSL structure
    table_tmsl = {
        "createOrReplace": {
            "table": target_table
        }
    }
    
    return table_tmsl


def add_measure_to_table_tmsl(table_tmsl: Dict[str, Any], measure_name: str, 
                             measure_expression: str, format_string: Optional[str] = None,
                             description: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a new measure to an existing table TMSL structure.
    
    IMPORTANT: This assumes the table_tmsl already contains ALL existing objects.
    Use extract_table_structure() first to get complete table definition.
    
    Args:
        table_tmsl: Complete table TMSL from extract_table_structure()
        measure_name: Name of new measure
        measure_expression: DAX expression for measure
        format_string: Optional format string (e.g., "#,0", "0.00%")
        description: Optional measure description
        
    Returns:
        Updated table TMSL with new measure added
    """
    # Get table content
    table_content = table_tmsl["createOrReplace"]["table"]
    
    # Initialize measures array if missing
    if "measures" not in table_content:
        table_content["measures"] = []
    
    # Create new measure definition
    new_measure = {
        "name": measure_name,
        "expression": measure_expression
    }
    
    if format_string:
        new_measure["formatString"] = format_string
    
    if description:
        new_measure["description"] = description
    
    # Check if measure already exists
    existing_measures = table_content["measures"]
    for i, measure in enumerate(existing_measures):
        if measure.get("name") == measure_name:
            # Replace existing measure
            existing_measures[i] = new_measure
            return table_tmsl
    
    # Add new measure
    existing_measures.append(new_measure)
    
    return table_tmsl


def validate_table_completeness(table_tmsl: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a table TMSL contains all necessary objects to prevent data loss.
    
    Args:
        table_tmsl: Table-level TMSL structure
        
    Returns:
        Dict with validation results: {"valid": bool, "warnings": list, "suggestions": list}
    """
    table_content = table_tmsl.get("createOrReplace", {}).get("table", {})
    table_name = table_content.get("name", "unnamed_table")
    
    warnings = []
    suggestions = []
    
    # Check for critical objects
    if "columns" not in table_content or len(table_content["columns"]) == 0:
        warnings.append(f"❌ CRITICAL: Table '{table_name}' missing columns - ALL existing columns will be DELETED!")
        suggestions.append("Use extract_table_structure() to get complete table definition with all columns")
    
    if "partitions" not in table_content or len(table_content["partitions"]) == 0:
        warnings.append(f"❌ CRITICAL: Table '{table_name}' missing partitions - table will become unusable!")
        suggestions.append("Include all existing partitions with complete source definitions")
    
    # Check for optional but important objects
    if "measures" not in table_content:
        warnings.append(f"⚠️ Table '{table_name}' has no measures - existing measures will be deleted if any exist")
        suggestions.append("If table has existing measures, include them or they will be permanently deleted")
    
    # Validate object structures
    if "columns" in table_content:
        for i, column in enumerate(table_content["columns"]):
            if "name" not in column:
                warnings.append(f"❌ Column #{i+1} missing 'name' property")
            if "dataType" not in column:
                warnings.append(f"⚠️ Column '{column.get('name', f'#{i+1}')}' missing 'dataType' property")
    
    if "measures" in table_content:
        for i, measure in enumerate(table_content["measures"]):
            if "name" not in measure:
                warnings.append(f"❌ Measure #{i+1} missing 'name' property")
            if "expression" not in measure:
                warnings.append(f"❌ Measure '{measure.get('name', f'#{i+1}')}' missing 'expression' property")
    
    return {
        "valid": len([w for w in warnings if w.startswith("❌")]) == 0,
        "warnings": warnings,
        "suggestions": suggestions
    }


def create_safe_measure_addition_workflow(complete_tmsl: str, table_name: str, 
                                        measure_name: str, measure_expression: str,
                                        format_string: Optional[str] = None,
                                        description: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete workflow for safely adding a measure to a table.
    
    This function:
    1. Extracts complete table structure from model
    2. Adds the new measure
    3. Validates the result
    4. Returns ready-to-deploy TMSL with validation results
    
    Args:
        complete_tmsl: Complete TMSL model definition (JSON string)
        table_name: Target table name
        measure_name: New measure name
        measure_expression: DAX expression
        format_string: Optional format string
        description: Optional description
        
    Returns:
        Dict with: {"tmsl": dict, "validation": dict, "safe": bool, "warnings": list}
    """
    try:
        # Step 1: Extract complete table structure
        table_tmsl = extract_table_structure(complete_tmsl, table_name)
        
        # Step 2: Add new measure
        updated_tmsl = add_measure_to_table_tmsl(
            table_tmsl, measure_name, measure_expression, format_string, description
        )
        
        # Step 3: Validate completeness
        validation = validate_table_completeness(updated_tmsl)
        
        # Step 4: Check if safe to deploy
        is_safe = validation["valid"] and len(validation["warnings"]) == 0
        
        return {
            "tmsl": updated_tmsl,
            "validation": validation,
            "safe": is_safe,
            "warnings": validation["warnings"],
            "suggestions": validation["suggestions"],
            "summary": f"Measure '{measure_name}' {'ready for deployment' if is_safe else 'NEEDS ATTENTION'} in table '{table_name}'"
        }
        
    except Exception as e:
        return {
            "tmsl": None,
            "validation": {"valid": False, "warnings": [f"❌ ERROR: {str(e)}"], "suggestions": []},
            "safe": False,
            "warnings": [f"❌ ERROR: {str(e)}"],
            "suggestions": ["Check table name and TMSL structure"],
            "summary": f"Failed to create measure addition for table '{table_name}'"
        }


# Example usage in comments:
"""
# Safe measure addition workflow:

# 1. Get complete model TMSL
complete_tmsl = get_model_definition("workspace", "dataset")

# 2. Create safe measure addition
result = create_safe_measure_addition_workflow(
    complete_tmsl=complete_tmsl,
    table_name="Sales",
    measure_name="Monthly Growth %", 
    measure_expression="VAR Current = SUM(Sales[Amount]) VAR Previous = CALCULATE(SUM(Sales[Amount]), DATEADD(Calendar[Date], -1, MONTH)) RETURN DIVIDE(Current - Previous, Previous, 0)",
    format_string="0.00%",
    description="Month-over-month sales growth percentage"
)

# 3. Check if safe to deploy
if result["safe"]:
    print("✅ Safe to deploy!")
    # Deploy the TMSL
    update_result = update_model_using_tmsl("workspace", "dataset", json.dumps(result["tmsl"]))
else:
    print("❌ Not safe to deploy:")
    for warning in result["warnings"]:
        print(f"  {warning}")
    for suggestion in result["suggestions"]:
        print(f"  💡 {suggestion}")
"""
