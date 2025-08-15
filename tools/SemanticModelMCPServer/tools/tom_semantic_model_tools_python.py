"""
Tabular Object Model (TOM) Tools for Semantic Model Manipulation

This module provides TOM-based tools for working with Power BI semantic models,
using pythonnet to directly access .NET Analysis Services libraries.

Key advantages over TMSL:
- Incremental changes without risk of deleting existing objects
- Object-oriented programming with strong typing
- Built-in validation and relationship management
- Simpler API for common operations like adding measures

Supports both Power BI Service and local Power BI Desktop instances.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add .NET libraries path
dotnet_path = Path(__file__).parent.parent / "dotnet"
if str(dotnet_path) not in sys.path:
    sys.path.append(str(dotnet_path))

# Import pythonnet and configure .NET
try:
    import clr
    
    # Add references to Analysis Services assemblies
    clr.AddReference("Microsoft.AnalysisServices.Tabular")
    clr.AddReference("Microsoft.AnalysisServices.Core") 
    clr.AddReference("Microsoft.AnalysisServices")
    
    # Import .NET namespaces
    from Microsoft.AnalysisServices.Tabular import Server, Database, Model, Table, Measure, Column  # type: ignore
    from Microsoft.AnalysisServices.Tabular import ModeType, ExpressionKind, Partition, NamedExpression  # type: ignore
    from Microsoft.AnalysisServices.Tabular import EntityPartitionSource, StructuredDataSource  # type: ignore
    from Microsoft.AnalysisServices import ConnectionException  # type: ignore
    from System import Exception as DotNetException  # type: ignore
    
    logger.info("Successfully loaded Analysis Services .NET libraries via pythonnet")
    TOM_AVAILABLE = True
    
except Exception as e:
    logger.error(f"Failed to load .NET libraries: {e}")
    TOM_AVAILABLE = False
    # Create dummy classes for type hints
    class Server: pass
    class Model: pass
    class Table: pass
    class Measure: pass

class TOMSemanticModelManager:
    """
    Tabular Object Model manager for semantic model operations using pythonnet.
    
    This class provides a Python interface to TOM operations using direct .NET interop
    for better reliability and performance compared to TMSL.
    """
    
    def __init__(self):
        if not TOM_AVAILABLE:
            raise RuntimeError("TOM libraries not available. Please ensure pythonnet and Analysis Services assemblies are properly installed.")
        
        self.server: Optional[Server] = None
        self.model: Optional[Model] = None
        logger.info("TOM Semantic Model Manager initialized")
    
    def connect(self, connection_string: str, database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to Analysis Services server and optionally select a specific database.
        
        Args:
            connection_string: Connection string for Analysis Services server (without catalog)
            database_name: Optional specific database name to connect to
            
        Returns:
            Connection result with server and model information
        """
        try:
            self.server = Server()
            self.server.Connect(connection_string)
            
            # Check if any databases exist
            if self.server.Databases.Count == 0:
                return {
                    "success": False,
                    "error": "No databases found on server",
                    "connection_string": connection_string
                }
            
            # DEBUG: List all available databases
            available_databases = [db.Name for db in self.server.Databases]
            logger.info(f"Available databases on server: {available_databases}")
            
            # Select database - either by name or first available
            if database_name:
                try:
                    database = self.server.Databases.GetByName(database_name)
                    logger.info(f"Successfully selected database: {database_name}")
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Database '{database_name}' not found. Available databases: {available_databases}",
                        "connection_string": connection_string,
                        "database_name": database_name,
                        "available_databases": available_databases
                    }
            else:
                database = self.server.Databases[0]
                logger.info(f"Using first available database: {database.Name}")
                
            self.model = database.Model
            
            # Gather connection info
            tables_count = self.model.Tables.Count if self.model.Tables else 0
            measures_count = sum(table.Measures.Count for table in self.model.Tables) if self.model.Tables else 0
            
            result = {
                "success": True,
                "connection_string": connection_string,
                "server_name": self.server.Name if hasattr(self.server, 'Name') else "Unknown",
                "database_name": database.Name,
                "model_name": self.model.Name if hasattr(self.model, 'Name') else database.Name,
                "tables_count": tables_count,
                "measures_count": measures_count,
                "compatibility_level": self.model.DefaultCompatibilityLevel if hasattr(self.model, 'DefaultCompatibilityLevel') else "Unknown"
            }
            
            logger.info(f"Successfully connected to: {connection_string}")
            logger.info(f"Database: {database.Name}, Tables: {tables_count}, Measures: {measures_count}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return {
                "success": False,
                "error": str(e),
                "connection_string": connection_string
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from Analysis Services server.
        
        Returns:
            Disconnection result
        """
        try:
            if self.server:
                self.server.Disconnect()
                self.server = None
                self.model = None
                logger.info("Disconnected from server")
                
            return {"success": True, "message": "Disconnected successfully"}
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return {"success": False, "error": str(e)}
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the model.
        
        Returns:
            Dictionary with table information
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            tables = []
            for table in self.model.Tables:
                table_info = {
                    "name": table.Name,
                    "columns_count": table.Columns.Count,
                    "measures_count": table.Measures.Count,
                    "partitions_count": table.Partitions.Count if hasattr(table, 'Partitions') else 0,
                    "is_hidden": table.IsHidden if hasattr(table, 'IsHidden') else False,
                    "description": table.Description if hasattr(table, 'Description') else ""
                }
                
                # Add column information
                columns = []
                for column in table.Columns:
                    columns.append({
                        "name": column.Name,
                        "data_type": str(column.DataType) if hasattr(column, 'DataType') else "Unknown",
                        "is_hidden": column.IsHidden if hasattr(column, 'IsHidden') else False
                    })
                table_info["columns"] = columns
                
                # Add measure information
                measures = []
                for measure in table.Measures:
                    measures.append({
                        "name": measure.Name,
                        "expression": measure.Expression if hasattr(measure, 'Expression') else "",
                        "format_string": measure.FormatString if hasattr(measure, 'FormatString') else "",
                        "description": measure.Description if hasattr(measure, 'Description') else ""
                    })
                table_info["measures"] = measures
                
                tables.append(table_info)
            
            return {
                "success": True,
                "tables": tables,
                "total_tables": len(tables)
            }
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return {"success": False, "error": str(e)}
    
    def add_measure(self, table_name: str, measure_name: str, expression: str,
                   format_string: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new measure to a table using TOM.
        
        Args:
            table_name: Name of the table to add the measure to
            measure_name: Name of the new measure
            expression: DAX expression for the measure
            format_string: Optional format string for the measure
            description: Optional description for the measure
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Check if measure already exists
            for existing_measure in target_table.Measures:
                if existing_measure.Name == measure_name:
                    return {
                        "success": False,
                        "error": f"Measure '{measure_name}' already exists in table '{table_name}'"
                    }
            
            # Create new measure
            new_measure = Measure()
            new_measure.Name = measure_name
            new_measure.Expression = expression
            
            if format_string:
                new_measure.FormatString = format_string
            if description:
                new_measure.Description = description
            
            # Add measure to table
            target_table.Measures.Add(new_measure)
            
            # Save changes to the model
            self.model.SaveChanges()
            
            logger.info(f"Successfully added measure '{measure_name}' to table '{table_name}'")
            
            return {
                "success": True,
                "message": f"Measure '{measure_name}' added successfully to table '{table_name}'",
                "measure_info": {
                    "name": measure_name,
                    "expression": expression,
                    "format_string": format_string or "",
                    "description": description or "",
                    "table_name": table_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding measure: {e}")
            return {"success": False, "error": str(e)}
    
    def update_measure(self, table_name: str, measure_name: str, 
                      expression: Optional[str] = None, format_string: Optional[str] = None, 
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing measure in a table using TOM.
        
        Args:
            table_name: Name of the table containing the measure
            measure_name: Name of the measure to update
            expression: Optional new DAX expression for the measure
            format_string: Optional new format string for the measure
            description: Optional new description for the measure
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Find the measure to update
            target_measure = None
            for measure in target_table.Measures:
                if measure.Name == measure_name:
                    target_measure = measure
                    break
            
            if not target_measure:
                return {
                    "success": False,
                    "error": f"Measure '{measure_name}' not found in table '{table_name}'"
                }
            
            # Store original values for comparison
            original_expression = target_measure.Expression if hasattr(target_measure, 'Expression') else ""
            original_format = target_measure.FormatString if hasattr(target_measure, 'FormatString') else ""
            original_description = target_measure.Description if hasattr(target_measure, 'Description') else ""
            
            # Update properties if provided
            changes_made = []
            
            if expression is not None and expression != original_expression:
                target_measure.Expression = expression
                changes_made.append(f"Expression: '{original_expression}' → '{expression}'")
            
            if format_string is not None and format_string != original_format:
                target_measure.FormatString = format_string
                changes_made.append(f"Format: '{original_format}' → '{format_string}'")
            
            if description is not None and description != original_description:
                target_measure.Description = description
                changes_made.append(f"Description: '{original_description}' → '{description}'")
            
            if not changes_made:
                return {
                    "success": True,
                    "message": f"No changes needed for measure '{measure_name}' in table '{table_name}'",
                    "changes_made": []
                }
            
            # Save changes to the model
            self.model.SaveChanges()
            
            logger.info(f"Successfully updated measure '{measure_name}' in table '{table_name}'. Changes: {', '.join(changes_made)}")
            
            return {
                "success": True,
                "message": f"Measure '{measure_name}' updated successfully in table '{table_name}'",
                "changes_made": changes_made,
                "measure_info": {
                    "name": measure_name,
                    "expression": target_measure.Expression if hasattr(target_measure, 'Expression') else "",
                    "format_string": target_measure.FormatString if hasattr(target_measure, 'FormatString') else "",
                    "description": target_measure.Description if hasattr(target_measure, 'Description') else "",
                    "table_name": table_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating measure: {e}")
            return {"success": False, "error": str(e)}

    def get_measure_info(self, table_name: str, measure_name: str) -> Dict[str, Any]:
        """
        Get information about a specific measure.
        
        Args:
            table_name: Name of the table containing the measure
            measure_name: Name of the measure
            
        Returns:
            Measure information
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Find the measure
            target_measure = None
            for measure in target_table.Measures:
                if measure.Name == measure_name:
                    target_measure = measure
                    break
            
            if not target_measure:
                return {
                    "success": False,
                    "error": f"Measure '{measure_name}' not found in table '{table_name}'"
                }
            
            measure_info = {
                "name": target_measure.Name,
                "expression": target_measure.Expression if hasattr(target_measure, 'Expression') else "",
                "format_string": target_measure.FormatString if hasattr(target_measure, 'FormatString') else "",
                "description": target_measure.Description if hasattr(target_measure, 'Description') else "",
                "table_name": table_name,
                "data_type": str(target_measure.DataType) if hasattr(target_measure, 'DataType') else "Unknown"
            }
            
            return {
                "success": True,
                "measure": measure_info
            }
            
        except Exception as e:
            logger.error(f"Error getting measure info: {e}")
            return {"success": False, "error": str(e)}

    # ===== TABLE OPERATIONS =====
    
    def add_table(self, table_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new table to the model.
        
        Args:
            table_name: Name of the new table
            description: Optional description for the table
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Check if table already exists
            for existing_table in self.model.Tables:
                if existing_table.Name == table_name:
                    return {
                        "success": False,
                        "error": f"Table '{table_name}' already exists in model"
                    }
            
            # Create new table (requires .NET import)
            from Microsoft.AnalysisServices.Tabular import Table  # type: ignore
            new_table = Table()
            new_table.Name = table_name
            
            if description:
                new_table.Description = description
            
            # Add table to model
            self.model.Tables.Add(new_table)
            
            # Save changes
            self.model.SaveChanges()
            
            logger.info(f"Successfully added table '{table_name}' to model")
            
            return {
                "success": True,
                "message": f"Table '{table_name}' added successfully to model",
                "table_info": {
                    "name": table_name,
                    "description": description or "",
                    "columns_count": 0,
                    "measures_count": 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding table: {e}")
            return {"success": False, "error": str(e)}
    
    def update_table(self, table_name: str, new_name: Optional[str] = None, 
                     description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing table's properties.
        
        Args:
            table_name: Current name of the table
            new_name: Optional new name for the table
            description: Optional new description for the table
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Check if new name conflicts
            if new_name and new_name != table_name:
                for table in self.model.Tables:
                    if table.Name == new_name:
                        return {
                            "success": False,
                            "error": f"Table '{new_name}' already exists in model"
                        }
            
            # Store original values
            original_name = target_table.Name
            original_description = target_table.Description if hasattr(target_table, 'Description') else ""
            
            # Update properties if provided
            changes_made = []
            
            if new_name and new_name != original_name:
                target_table.Name = new_name
                changes_made.append(f"Name: '{original_name}' → '{new_name}'")
            
            if description is not None and description != original_description:
                target_table.Description = description
                changes_made.append(f"Description: '{original_description}' → '{description}'")
            
            if not changes_made:
                return {
                    "success": True,
                    "message": f"No changes needed for table '{table_name}'",
                    "changes_made": []
                }
            
            # Save changes
            self.model.SaveChanges()
            
            final_name = new_name if new_name else table_name
            logger.info(f"Successfully updated table '{original_name}' → '{final_name}'. Changes: {', '.join(changes_made)}")
            
            return {
                "success": True,
                "message": f"Table updated successfully",
                "changes_made": changes_made,
                "table_info": {
                    "name": final_name,
                    "description": target_table.Description if hasattr(target_table, 'Description') else "",
                    "columns_count": target_table.Columns.Count if target_table.Columns else 0,
                    "measures_count": target_table.Measures.Count if target_table.Measures else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating table: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_table(self, table_name: str) -> Dict[str, Any]:
        """
        Delete a table from the model.
        
        Args:
            table_name: Name of the table to delete
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Get info before deletion
            columns_count = target_table.Columns.Count if target_table.Columns else 0
            measures_count = target_table.Measures.Count if target_table.Measures else 0
            
            # Remove table from model
            self.model.Tables.Remove(target_table)
            
            # Save changes
            self.model.SaveChanges()
            
            logger.info(f"Successfully deleted table '{table_name}' from model")
            
            return {
                "success": True,
                "message": f"Table '{table_name}' deleted successfully from model",
                "deleted_info": {
                    "table_name": table_name,
                    "columns_deleted": columns_count,
                    "measures_deleted": measures_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error deleting table: {e}")
            return {"success": False, "error": str(e)}

    # ===== COLUMN OPERATIONS =====
    
    def add_column(self, table_name: str, column_name: str, data_type: str = "String",
                   source_column: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new column to a table.
        
        Args:
            table_name: Name of the table to add the column to
            column_name: Name of the new column
            data_type: Data type of the column (String, Int64, Double, Boolean, DateTime, etc.)
            source_column: Optional source column reference for calculated columns
            description: Optional description for the column
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Check if column already exists
            for existing_column in target_table.Columns:
                if existing_column.Name == column_name:
                    return {
                        "success": False,
                        "error": f"Column '{column_name}' already exists in table '{table_name}'"
                    }
            
            # Create new column
            from Microsoft.AnalysisServices.Tabular import DataColumn, CalculatedColumn  # type: ignore
            from Microsoft.AnalysisServices.Tabular import DataType  # type: ignore
            
            # Determine column type and create accordingly
            if source_column:
                # Calculated column
                new_column = CalculatedColumn()
                new_column.Expression = source_column
            else:
                # Data column
                new_column = DataColumn()
                if hasattr(new_column, 'SourceColumn'):
                    new_column.SourceColumn = column_name
            
            new_column.Name = column_name
            
            # Set data type if supported
            if hasattr(new_column, 'DataType'):
                try:
                    # Map string data type to .NET enum
                    data_type_mapping = {
                        "String": "String",
                        "Int64": "Int64", 
                        "Double": "Double",
                        "Boolean": "Boolean",
                        "DateTime": "DateTime",
                        "Decimal": "Decimal"
                    }
                    if data_type in data_type_mapping:
                        # This might need adjustment based on actual .NET enum values
                        pass  # Let TOM infer the data type
                except:
                    pass  # Let TOM handle data type inference
            
            if description:
                new_column.Description = description
            
            # Add column to table
            target_table.Columns.Add(new_column)
            
            # Save changes
            self.model.SaveChanges()
            
            logger.info(f"Successfully added column '{column_name}' to table '{table_name}'")
            
            return {
                "success": True,
                "message": f"Column '{column_name}' added successfully to table '{table_name}'",
                "column_info": {
                    "name": column_name,
                    "data_type": data_type,
                    "source_column": source_column or "",
                    "description": description or "",
                    "table_name": table_name,
                    "column_type": "Calculated" if source_column else "Data"
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            return {"success": False, "error": str(e)}
    
    def update_column(self, table_name: str, column_name: str, new_name: Optional[str] = None,
                     description: Optional[str] = None, expression: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing column's properties.
        
        Args:
            table_name: Name of the table containing the column
            column_name: Current name of the column
            new_name: Optional new name for the column
            description: Optional new description for the column
            expression: Optional new expression for calculated columns
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find the target table
            target_table = None
            for table in self.model.Tables:
                if table.Name == table_name:
                    target_table = table
                    break
            
            if not target_table:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found in model"
                }
            
            # Find the column
            target_column = None
            for column in target_table.Columns:
                if column.Name == column_name:
                    target_column = column
                    break
            
            if not target_column:
                return {
                    "success": False,
                    "error": f"Column '{column_name}' not found in table '{table_name}'"
                }
            
            # Check if new name conflicts
            if new_name and new_name != column_name:
                for column in target_table.Columns:
                    if column.Name == new_name:
                        return {
                            "success": False,
                            "error": f"Column '{new_name}' already exists in table '{table_name}'"
                        }
            
            # Store original values
            original_name = target_column.Name
            original_description = target_column.Description if hasattr(target_column, 'Description') else ""
            original_expression = ""
            if hasattr(target_column, 'Expression'):
                original_expression = target_column.Expression if target_column.Expression else ""
            
            # Update properties if provided
            changes_made = []
            
            if new_name and new_name != original_name:
                target_column.Name = new_name
                changes_made.append(f"Name: '{original_name}' → '{new_name}'")
            
            if description is not None and description != original_description:
                target_column.Description = description
                changes_made.append(f"Description: '{original_description}' → '{description}'")
            
            if expression is not None and hasattr(target_column, 'Expression') and expression != original_expression:
                target_column.Expression = expression
                changes_made.append(f"Expression: '{original_expression}' → '{expression}'")
            
            if not changes_made:
                return {
                    "success": True,
                    "message": f"No changes needed for column '{column_name}' in table '{table_name}'",
                    "changes_made": []
                }
            
            # Save changes
            self.model.SaveChanges()
            
            final_name = new_name if new_name else column_name
            logger.info(f"Successfully updated column '{original_name}' → '{final_name}' in table '{table_name}'. Changes: {', '.join(changes_made)}")
            
            return {
                "success": True,
                "message": f"Column updated successfully",
                "changes_made": changes_made,
                "column_info": {
                    "name": final_name,
                    "description": target_column.Description if hasattr(target_column, 'Description') else "",
                    "expression": target_column.Expression if hasattr(target_column, 'Expression') else "",
                    "table_name": table_name,
                    "data_type": str(target_column.DataType) if hasattr(target_column, 'DataType') else "Unknown"
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating column: {e}")
            return {"success": False, "error": str(e)}

    # ===== RELATIONSHIP OPERATIONS =====
    
    def add_relationship(self, from_table: str, from_column: str, to_table: str, to_column: str,
                        cross_filtering_behavior: str = "OneDirection") -> Dict[str, Any]:
        """
        Add a relationship between two tables.
        
        Args:
            from_table: Name of the source table
            from_column: Name of the source column
            to_table: Name of the target table  
            to_column: Name of the target column
            cross_filtering_behavior: Cross filtering behavior ("OneDirection", "BothDirections")
            
        Returns:
            Result of the operation
        """
        if not self.model:
            return {"success": False, "error": "Not connected to a model"}
        
        try:
            # Find source table and column
            from_table_obj = None
            from_column_obj = None
            for table in self.model.Tables:
                if table.Name == from_table:
                    from_table_obj = table
                    for column in table.Columns:
                        if column.Name == from_column:
                            from_column_obj = column
                            break
                    break
            
            if not from_table_obj:
                return {"success": False, "error": f"Source table '{from_table}' not found"}
            if not from_column_obj:
                return {"success": False, "error": f"Source column '{from_column}' not found in table '{from_table}'"}
            
            # Find target table and column
            to_table_obj = None
            to_column_obj = None
            for table in self.model.Tables:
                if table.Name == to_table:
                    to_table_obj = table
                    for column in table.Columns:
                        if column.Name == to_column:
                            to_column_obj = column
                            break
                    break
            
            if not to_table_obj:
                return {"success": False, "error": f"Target table '{to_table}' not found"}
            if not to_column_obj:
                return {"success": False, "error": f"Target column '{to_column}' not found in table '{to_table}'"}
            
            # Check if relationship already exists
            if hasattr(self.model, 'Relationships'):
                for rel in self.model.Relationships:
                    if (hasattr(rel, 'FromColumn') and hasattr(rel, 'ToColumn') and
                        rel.FromColumn == from_column_obj and rel.ToColumn == to_column_obj):
                        return {
                            "success": False,
                            "error": f"Relationship already exists between {from_table}.{from_column} and {to_table}.{to_column}"
                        }
            
            # Create new relationship
            from Microsoft.AnalysisServices.Tabular import SingleColumnRelationship  # type: ignore
            new_relationship = SingleColumnRelationship()
            new_relationship.FromColumn = from_column_obj
            new_relationship.ToColumn = to_column_obj
            
            # Set cross filtering behavior
            if hasattr(new_relationship, 'CrossFilteringBehavior'):
                if cross_filtering_behavior == "BothDirections":
                    # This might need adjustment based on actual enum values
                    pass  # Let TOM handle default behavior for now
            
            # Add relationship to model
            if hasattr(self.model, 'Relationships'):
                self.model.Relationships.Add(new_relationship)
            
            # Save changes
            self.model.SaveChanges()
            
            logger.info(f"Successfully added relationship: {from_table}.{from_column} → {to_table}.{to_column}")
            
            return {
                "success": True,
                "message": f"Relationship added successfully",
                "relationship_info": {
                    "from_table": from_table,
                    "from_column": from_column,
                    "to_table": to_table,
                    "to_column": to_column,
                    "cross_filtering": cross_filtering_behavior
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return {"success": False, "error": str(e)}

# MCP Tool Functions
def tom_connect_to_model(connection_string: str) -> str:
    """
    Connect to a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services (local Desktop or Service)
        
    Returns:
        JSON string with connection result
    """
    try:
        manager = TOMSemanticModelManager()
        result = manager.connect(connection_string)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM connection failed: {str(e)}",
            "connection_string": connection_string
        }
        return json.dumps(error_result, indent=2)

def tom_list_model_tables(connection_string: str) -> str:
    """
    List all tables in a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        
    Returns:
        JSON string with table information
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # List tables
        result = manager.list_tables()
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM table listing failed: {str(e)}",
            "connection_string": connection_string
        }
        return json.dumps(error_result, indent=2)

def tom_add_measure_to_model(connection_string: str, table_name: str, measure_name: str, 
                           expression: str, format_string: Optional[str] = None, 
                           description: Optional[str] = None) -> str:
    """
    Add a measure to a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the table to add the measure to
        measure_name: Name of the new measure
        expression: DAX expression for the measure
        format_string: Optional format string for the measure
        description: Optional description for the measure
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Add measure
        result = manager.add_measure(table_name, measure_name, expression, format_string, description)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM measure addition failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name,
            "measure_name": measure_name
        }
        return json.dumps(error_result, indent=2)

def tom_update_measure_in_model(connection_string: str, table_name: str, measure_name: str,
                               expression: Optional[str] = None, format_string: Optional[str] = None,
                               description: Optional[str] = None) -> str:
    """
    Update an existing measure in a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the table containing the measure
        measure_name: Name of the measure to update
        expression: Optional new DAX expression for the measure
        format_string: Optional new format string for the measure
        description: Optional new description for the measure
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Update measure
        result = manager.update_measure(table_name, measure_name, expression, format_string, description)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM measure update failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name,
            "measure_name": measure_name
        }
        return json.dumps(error_result, indent=2)

def tom_get_measure_info(connection_string: str, table_name: str, measure_name: str) -> str:
    """
    Get information about a specific measure using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the table containing the measure
        measure_name: Name of the measure
        
    Returns:
        JSON string with measure information
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Get measure info
        result = manager.get_measure_info(table_name, measure_name)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM measure info retrieval failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name,
            "measure_name": measure_name
        }
        return json.dumps(error_result, indent=2)

# ===== TABLE MCP FUNCTIONS =====

def tom_add_table_to_model(connection_string: str, table_name: str, 
                          description: Optional[str] = None) -> str:
    """
    Add a table to a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the new table
        description: Optional description for the table
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Add table
        result = manager.add_table(table_name, description)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM table addition failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name
        }
        return json.dumps(error_result, indent=2)

def tom_update_table_in_model(connection_string: str, table_name: str,
                             new_name: Optional[str] = None, description: Optional[str] = None) -> str:
    """
    Update a table in a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Current name of the table
        new_name: Optional new name for the table
        description: Optional new description for the table
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Update table
        result = manager.update_table(table_name, new_name, description)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM table update failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name
        }
        return json.dumps(error_result, indent=2)

def tom_delete_table_from_model(connection_string: str, table_name: str) -> str:
    """
    Delete a table from a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the table to delete
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Delete table
        result = manager.delete_table(table_name)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM table deletion failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name
        }
        return json.dumps(error_result, indent=2)

# ===== COLUMN MCP FUNCTIONS =====

def tom_add_column_to_table(connection_string: str, table_name: str, column_name: str,
                           data_type: str = "String", source_column: Optional[str] = None,
                           description: Optional[str] = None) -> str:
    """
    Add a column to a table in a semantic model using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the table to add the column to
        column_name: Name of the new column
        data_type: Data type of the column (String, Int64, Double, Boolean, DateTime)
        source_column: Optional source column reference for calculated columns
        description: Optional description for the column
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Add column
        result = manager.add_column(table_name, column_name, data_type, source_column, description)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM column addition failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name,
            "column_name": column_name
        }
        return json.dumps(error_result, indent=2)

def tom_update_column_in_table(connection_string: str, table_name: str, column_name: str,
                              new_name: Optional[str] = None, description: Optional[str] = None,
                              expression: Optional[str] = None) -> str:
    """
    Update a column in a table using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        table_name: Name of the table containing the column
        column_name: Current name of the column
        new_name: Optional new name for the column
        description: Optional new description for the column
        expression: Optional new expression for calculated columns
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Update column
        result = manager.update_column(table_name, column_name, new_name, description, expression)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM column update failed: {str(e)}",
            "connection_string": connection_string,
            "table_name": table_name,
            "column_name": column_name
        }
        return json.dumps(error_result, indent=2)

# ===== RELATIONSHIP MCP FUNCTIONS =====

def tom_add_relationship_to_model(connection_string: str, from_table: str, from_column: str,
                                 to_table: str, to_column: str, 
                                 cross_filtering_behavior: str = "OneDirection") -> str:
    """
    Add a relationship between two tables using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services
        from_table: Name of the source table
        from_column: Name of the source column
        to_table: Name of the target table
        to_column: Name of the target column
        cross_filtering_behavior: Cross filtering behavior ("OneDirection", "BothDirections")
        
    Returns:
        JSON string with operation result
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect
        connect_result = manager.connect(connection_string)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Add relationship
        result = manager.add_relationship(from_table, from_column, to_table, to_column, cross_filtering_behavior)
        
        # Disconnect
        manager.disconnect()
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM relationship addition failed: {str(e)}",
            "connection_string": connection_string,
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column
        }
        return json.dumps(error_result, indent=2)

# Enhanced TOM functions with proper database selection

def tom_connect_to_server_and_database(server_connection_string: str, database_name: str) -> str:
    """
    Connect to Analysis Services server and select a specific database by name.
    
    Args:
        server_connection_string: Connection string for Analysis Services server (without catalog)
        database_name: Name of the database/semantic model to connect to
        
    Returns:
        JSON string with connection results and model information
    """
    try:
        manager = TOMSemanticModelManager()
        result = manager.connect(server_connection_string, database_name)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"TOM connection failed: {str(e)}",
            "server_connection_string": server_connection_string,
            "database_name": database_name
        }
        return json.dumps(error_result, indent=2)

def tom_list_tables_by_database_name(server_connection_string: str, database_name: str) -> str:
    """
    List all tables in a semantic model using TOM with explicit database selection.
    
    Args:
        server_connection_string: Connection string for Analysis Services server (without catalog)
        database_name: Name of the database/semantic model to list tables from
        
    Returns:
        JSON string with table, column, and measure information
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect to server and select specific database
        connect_result = manager.connect(server_connection_string, database_name)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # List tables using existing method
        tables_result = manager.list_tables()
        return json.dumps(tables_result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to list tables: {str(e)}",
            "server_connection_string": server_connection_string,
            "database_name": database_name
        }
        return json.dumps(error_result, indent=2)

def tom_add_measure_by_database_name(server_connection_string: str, database_name: str, 
                                   table_name: str, measure_name: str, expression: str,
                                   format_string: Optional[str] = None, 
                                   description: Optional[str] = None) -> str:
    """
    Add a measure to a semantic model using TOM with explicit database selection.
    
    Args:
        server_connection_string: Connection string for Analysis Services server (without catalog)
        database_name: Name of the database/semantic model 
        table_name: Target table name where the measure will be added
        measure_name: Name of the new measure
        expression: DAX expression for the measure
        format_string: Optional format string for the measure
        description: Optional description for the measure
        
    Returns:
        JSON string with operation results
    """
    try:
        manager = TOMSemanticModelManager()
        
        # Connect to server and select specific database
        connect_result = manager.connect(server_connection_string, database_name)
        if not connect_result.get("success", False):
            return json.dumps(connect_result, indent=2)
        
        # Add measure using existing method
        result = manager.add_measure(table_name, measure_name, expression, format_string, description)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to add measure: {str(e)}",
            "server_connection_string": server_connection_string,
            "database_name": database_name,
            "table_name": table_name,
            "measure_name": measure_name
        }
        return json.dumps(error_result, indent=2)

# Test function for development
def test_tom_connection(connection_string: str = "Data Source=localhost:65304"):
    """Test TOM connection and basic operations."""
    print("Testing TOM connection...")
    
    # Test connection
    result = tom_connect_to_model(connection_string)
    print("Connection result:")
    print(result)
    
    # Test table listing
    print("\nTesting table listing...")
    result = tom_list_model_tables(connection_string)
    print("Tables result:")
    print(result)

# ============================================================================
# ADVANCED TOM FUNCTIONS FOR COMPLETE MODEL CREATION FROM LAKEHOUSE
# ============================================================================

def tom_create_empty_semantic_model(connection_string: str, database_name: str, 
                                   compatibility_level: int = 1604) -> str:
    """
    Create a new empty semantic model (database) using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services server (without catalog)
        database_name: Name for the new database/semantic model
        compatibility_level: Compatibility level for the model (default: 1604)
        
    Returns:
        JSON string with operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from Microsoft.AnalysisServices.Tabular import Database, Model  # type: ignore
        
        manager = TOMSemanticModelManager()
        server = Server()
        server.Connect(connection_string)
        
        # Check if database already exists
        try:
            existing_db = server.Databases.GetByName(database_name)
            return json.dumps({
                "success": False,
                "error": f"Database '{database_name}' already exists",
                "database_name": database_name
            })
        except:
            # Database doesn't exist, which is what we want
            pass
        
        # Create new database
        database = Database()
        database.Name = database_name
        database.ID = database_name
        
        # Set compatibility level directly as integer - TOM will handle conversion
        database.CompatibilityLevel = compatibility_level
        
        # Create the model
        model = Model()
        model.Name = database_name
        database.Model = model
        
        # Add basic model properties for DirectLake
        model.Culture = "en-US"
        model.Collation = "Latin1_General_100_BIN2_UTF8"
        model.SourceQueryCulture = "en-US"
        
        # Add to server
        server.Databases.Add(database)
        database.Update()
        
        logger.info(f"Successfully created empty semantic model: {database_name}")
        
        return json.dumps({
            "success": True,
            "database_name": database_name,
            "compatibility_level": compatibility_level,
            "message": f"Empty semantic model '{database_name}' created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating empty semantic model: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name
        })

def tom_create_empty_semantic_model_with_auth(workspace_name: str, database_name: str, 
                                             compatibility_level: int = 1604) -> str:
    """
    Create a new empty semantic model (database) using TOM with automatic Power BI Service authentication.
    
    Args:
        workspace_name: The Power BI workspace name
        database_name: Name for the new database/semantic model
        compatibility_level: Compatibility level for the model (default: 1604)
        
    Returns:
        JSON string with operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from core.auth import get_access_token
        import urllib.parse
        from Microsoft.AnalysisServices.Tabular import Database, Model  # type: ignore
        
        # Get access token automatically
        access_token = get_access_token()
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        server = Server()
        server.Connect(connection_string)
        
        # Check if database already exists
        try:
            existing_db = server.Databases.GetByName(database_name)
            return json.dumps({
                "success": False,
                "error": f"Database '{database_name}' already exists",
                "database_name": database_name,
                "workspace_name": workspace_name
            })
        except:
            # Database doesn't exist, which is what we want
            pass
        
        # Create new database
        database = Database()
        database.Name = database_name
        database.ID = database_name
        
        # Set compatibility level directly as integer - TOM will handle conversion
        database.CompatibilityLevel = compatibility_level
        
        # Create the model
        model = Model()
        model.Name = database_name
        database.Model = model
        
        # Add basic model properties for DirectLake
        model.Culture = "en-US"
        model.Collation = "Latin1_General_100_BIN2_UTF8"
        model.SourceQueryCulture = "en-US"
        
        # Add to server
        server.Databases.Add(database)
        database.Update()
        
        logger.info(f"Successfully created empty semantic model: {database_name}")
        
        return json.dumps({
            "success": True,
            "database_name": database_name,
            "workspace_name": workspace_name,
            "compatibility_level": compatibility_level,
            "message": f"Empty semantic model '{database_name}' created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating empty semantic model: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name,
            "workspace_name": workspace_name
        })
    finally:
        try:
            server.Disconnect()
        except:
            pass

def tom_add_lakehouse_expression_with_auth(workspace_name: str, database_name: str, 
                                          lakehouse_server: str, lakehouse_endpoint_id: str) -> str:
    """
    Add DatabaseQuery expression for DirectLake connectivity to lakehouse with automatic authentication.
    This MUST be created before adding tables with DirectLake partitions.
    
    Args:
        workspace_name: The Power BI workspace name
        database_name: Name of the semantic model/database
        lakehouse_server: SQL Analytics Endpoint server name (e.g., "abc.datawarehouse.fabric.microsoft.com")
        lakehouse_endpoint_id: SQL Analytics Endpoint ID/database name
    
    Returns:
        JSON string with operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from core.auth import get_access_token
        import urllib.parse
        from Microsoft.AnalysisServices.Tabular import NamedExpression, ExpressionKind  # type: ignore
        
        # Get access token automatically
        access_token = get_access_token()
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        # Connect to server
        server = Server()
        server.Connect(connection_string)
        
        # Get database by name
        database = server.Databases.GetByName(database_name)
        if database is None:
            return json.dumps({
                "success": False,
                "error": f"Database '{database_name}' not found"
            })
        
        # Create the DatabaseQuery expression for DirectLake
        expression = NamedExpression()
        expression.Name = "DatabaseQuery"
        
        # FIX: Use direct enum value assignment for Python.NET 3.0 compatibility
        expression.Kind = ExpressionKind.M
        
        # Build M expression for lakehouse connection (following DirectLake pattern)
        m_expression = [
            "let",
            f'    database = Sql.Database("{lakehouse_server}", "{lakehouse_endpoint_id}")',
            "in",
            "    database"
        ]
        
        # Set expression content
        expression.Expression = "\n".join(m_expression)
        
        # Add lineage tag for tracking
        expression.LineageTag = "DatabaseQuery_expression"
        
        # Add expression to model
        database.Model.Expressions.Add(expression)
        
        # Save model changes
        database.Model.SaveChanges()
        
        logger.info(f"Successfully added lakehouse expression to model: {database_name}")
        
        return json.dumps({
            "success": True,
            "message": f"DatabaseQuery expression added successfully to model '{database_name}'",
            "expression_name": "DatabaseQuery",
            "expression_type": "M",
            "lakehouse_server": lakehouse_server,
            "lakehouse_endpoint": lakehouse_endpoint_id,
            "expression_content": expression.Expression,
            "workspace_name": workspace_name
        })
        
    except Exception as e:
        logger.error(f"Error adding lakehouse expression: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name,
            "workspace_name": workspace_name
        })
    finally:
        try:
            server.Disconnect()
        except:
            pass

def tom_add_data_source_expression(connection_string: str, database_name: str,
                                  server_name: str, endpoint_id: str) -> str:
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
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from Microsoft.AnalysisServices.Tabular import NamedExpression  # type: ignore
        from System.Collections.Generic import List  # type: ignore
        from System import String  # type: ignore
        
        manager = TOMSemanticModelManager()
        result = manager.connect(connection_string, database_name)
        
        if not result["success"]:
            return json.dumps(result)
        
        # Create the DatabaseQuery expression for DirectLake
        expression = NamedExpression()
        expression.Name = "DatabaseQuery"
        expression.Kind = "m"  # Power Query M expression
        
        # Build the M expression for SQL Analytics Endpoint
        m_expression = [
            "let",
            f'    database = Sql.Database("{server_name}", "{endpoint_id}")',
            "in",
            "    database"
        ]
        
        # Convert to .NET string list
        expression_list = List[String]()
        for line in m_expression:
            expression_list.Add(line)
        expression.Expression = expression_list
        
        # Add annotations
        from Microsoft.AnalysisServices.Tabular import Annotation  # type: ignore
        annotation = Annotation()
        annotation.Name = "PBI_IncludeFutureArtifacts"
        annotation.Value = "False"
        expression.Annotations.Add(annotation)
        
        # Add to model
        manager.model.Expressions.Add(expression)
        manager.model.SaveChanges()
        
        logger.info(f"Successfully added DatabaseQuery expression to model: {database_name}")
        
        return json.dumps({
            "success": True,
            "database_name": database_name,
            "expression_name": "DatabaseQuery",
            "server_name": server_name,
            "endpoint_id": endpoint_id,
            "message": "Data source expression added successfully"
        })
        
    except Exception as e:
        logger.error(f"Error adding data source expression: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name
        })

def tom_add_lakehouse_data_source(connection_string: str, database_name: str,
                                 server_name: str, endpoint_id: str) -> str:
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
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        manager = TOMSemanticModelManager()
        result = manager.connect(connection_string, database_name)
        
        if not result["success"]:
            return json.dumps(result)
        
        # Create structured data source for DirectLake
        data_source = StructuredDataSource()
        data_source.Name = "LakehouseDataSource"
        data_source.Description = f"Lakehouse SQL Analytics Endpoint: {server_name}"
        
        # For DirectLake, we need to set the connection string to the SQL Analytics Endpoint
        data_source.ConnectionString = f"Data Source={server_name};Initial Catalog=lh;Integrated Security=SSPI;"
        
        # Add data source to model
        manager.model.DataSources.Add(data_source)
        manager.model.SaveChanges()
        
        logger.info(f"Successfully added lakehouse data source to model '{database_name}'")
        
        return json.dumps({
            "success": True,
            "database_name": database_name,
            "data_source_name": data_source.Name,
            "server_name": server_name,
            "endpoint_id": endpoint_id,
            "message": f"Lakehouse data source added successfully to model"
        })
        
    except Exception as e:
        logger.error(f"Error adding lakehouse data source: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name
        })


def tom_add_lakehouse_expression(connection_string, database_name, lakehouse_server, lakehouse_endpoint_id):
    """
    Add DatabaseQuery expression for DirectLake connectivity to lakehouse.
    This MUST be created before adding tables with DirectLake partitions.
    
    Args:
        connection_string: TOM connection string for Power BI Service
        database_name: Name of the semantic model/database
        lakehouse_server: SQL Analytics Endpoint server name (e.g., "abc.datawarehouse.fabric.microsoft.com")
        lakehouse_endpoint_id: SQL Analytics Endpoint ID/database name
    
    Returns:
        JSON string with operation results
    """
    import json
    
    try:
        # Connect to server
        server = Server()
        server.Connect(connection_string)
        
        # Get database by name
        database = server.Databases.GetByName(database_name)
        if database is None:
            return json.dumps({
                "success": False,
                "error": f"Database '{database_name}' not found"
            })
        
        # Create the DatabaseQuery expression for DirectLake
        expression = NamedExpression()
        expression.Name = "DatabaseQuery"
        
        # FIX: Use direct enum value assignment for Python.NET 3.0 compatibility
        expression.Kind = ExpressionKind.M
        
        # Build M expression for lakehouse connection (following DirectLake pattern)
        m_expression = [
            "let",
            f'    database = Sql.Database("{lakehouse_server}", "{lakehouse_endpoint_id}")',
            "in",
            "    database"
        ]
        
        # Set expression content
        expression.Expression = "\n".join(m_expression)
        
        # Add lineage tag for tracking
        expression.LineageTag = "DatabaseQuery_expression"
        
        # Add expression to model
        database.Model.Expressions.Add(expression)
        
        # Save model changes
        database.Model.SaveChanges()
        
        return json.dumps({
            "success": True,
            "message": f"DatabaseQuery expression added successfully to model '{database_name}'",
            "expression_name": "DatabaseQuery",
            "expression_type": "M",
            "lakehouse_server": lakehouse_server,
            "lakehouse_endpoint": lakehouse_endpoint_id,
            "expression_content": expression.Expression
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to add expression: {str(e)}",
            "error_type": str(type(e).__name__)
        })
    finally:
        try:
            server.Disconnect()
        except:
            pass


def tom_add_table_with_columns_and_partition(connection_string: str, database_name: str,
                                            table_name: str, columns_info: List[Dict],
                                            schema_name: str = "dbo") -> str:
    """
    Add a complete table with columns and DirectLake partition using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services server
        database_name: Name of the target database
        table_name: Name of the table to create
        columns_info: List of dictionaries with column information
        schema_name: Schema name in the lakehouse (default: "dbo")
        
    Returns:
        JSON string with operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from Microsoft.AnalysisServices.Tabular import Table, DataColumn, Partition, PartitionSourceType  # type: ignore
        
        manager = TOMSemanticModelManager()
        result = manager.connect(connection_string, database_name)
        
        if not result["success"]:
            return json.dumps(result)
        
        # Create new table
        table = Table()
        table.Name = table_name
        table.LineageTag = f"{table_name}_table"
        table.SourceLineageTag = f"[{schema_name}].[{table_name}]"
        
        # Add columns to the table
        columns_added = []
        for col_info in columns_info:
            column = DataColumn()
            column.Name = col_info["name"]
            column.SourceColumn = col_info["name"]
            column.LineageTag = f"{table_name}_{col_info['name']}"
            column.SourceLineageTag = col_info["name"]
            
            # Map data types from SQL to TOM and set sourceProviderType
            from Microsoft.AnalysisServices.Tabular import DataType  # type: ignore
            sql_type = col_info.get("data_type", "").lower()
            
            # CRITICAL FIX: Add sourceProviderType for DirectLake compatibility
            if sql_type == "int":
                column.DataType = DataType.Int64
                column.SourceProviderType = "int"
            elif sql_type == "bigint":
                column.DataType = DataType.Int64
                column.SourceProviderType = "bigint"
            elif sql_type == "smallint":
                column.DataType = DataType.Int64
                column.SourceProviderType = "smallint"
            elif sql_type == "datetime2":
                column.DataType = DataType.DateTime
                column.SourceProviderType = "datetime2"
            elif sql_type == "varchar":
                column.DataType = DataType.String
                column.SourceProviderType = "varchar(8000)"
            elif "decimal" in sql_type or "numeric" in sql_type or "float" in sql_type or "money" in sql_type:
                column.DataType = DataType.Decimal
                column.SourceProviderType = sql_type
            elif "date" in sql_type or "time" in sql_type:
                column.DataType = DataType.DateTime
                column.SourceProviderType = sql_type
            elif "bit" in sql_type or "boolean" in sql_type:
                column.DataType = DataType.Boolean
                column.SourceProviderType = sql_type
            else:
                column.DataType = DataType.String
                column.SourceProviderType = "varchar(8000)"  # Default for unknown string types
            
            # Set summarization behavior - FIX: Use text-based enum parsing
            if column.DataType == DataType.Int64 or column.DataType == DataType.Decimal:
                # Import enum for SummarizeBy
                from Microsoft.AnalysisServices.Tabular import AggregateFunction  # type: ignore
                from System import Enum  # type: ignore
                # Numeric columns default to sum, but foreign keys should be none
                if "key" in col_info["name"].lower() and col_info["name"].lower() != table_name.lower() + "key":
                    column.SummarizeBy = Enum.Parse(AggregateFunction, "None")  # Use text-based parsing
                else:
                    column.SummarizeBy = Enum.Parse(AggregateFunction, "Sum")   # Use text-based parsing
            else:
                from Microsoft.AnalysisServices.Tabular import AggregateFunction  # type: ignore
                from System import Enum  # type: ignore
                column.SummarizeBy = Enum.Parse(AggregateFunction, "None")  # Use text-based parsing
            
            table.Columns.Add(column)
            columns_added.append({
                "name": col_info["name"],
                "data_type": str(column.DataType),  # Convert enum to string for JSON serialization
                "source_provider_type": column.SourceProviderType,  # Include sourceProviderType
                "summarize_by": str(column.SummarizeBy)  # Convert enum to string for JSON serialization
            })
        
        # Create DirectLake partition
        partition = Partition()
        partition.Name = f"{table_name}_partition"
        # Handle Python.NET 3.0 enum conversion for Mode
        partition.Mode = ModeType.DirectLake
        
        # Create the partition source using EntityPartitionSource for DirectLake
        source = EntityPartitionSource()
        source.SchemaName = schema_name
        source.EntityName = table_name
        # FIX: Get reference to DatabaseQuery expression object, not string
        database_query_expression = manager.model.Expressions.Find("DatabaseQuery")
        if database_query_expression is None:
            raise Exception("DatabaseQuery expression not found. You must create it first using tom_add_lakehouse_expression()")
        source.ExpressionSource = database_query_expression  # Reference to actual expression object
        
        partition.Source = source
        table.Partitions.Add(partition)
        
        # Add table to model
        manager.model.Tables.Add(table)
        manager.model.SaveChanges()
        
        logger.info(f"Successfully added table '{table_name}' with {len(columns_added)} columns")
        
        return json.dumps({
            "success": True,
            "database_name": database_name,
            "table_name": table_name,
            "columns_added": columns_added,
            "partition_name": partition.Name,
            "schema_name": schema_name,
            "message": f"Table '{table_name}' added successfully with DirectLake partition"
        })
        
    except Exception as e:
        logger.error(f"Error adding table with columns and partition: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name,
            "table_name": table_name
        })

def tom_add_table_with_lakehouse_partition_with_auth(workspace_name: str, database_name: str,
                                                    table_name: str, columns_info: List[Dict],
                                                    schema_name: str = "dbo") -> str:
    """
    Add a complete table with columns and DirectLake partition using TOM with automatic authentication.
    
    Args:
        workspace_name: The Power BI workspace name
        database_name: Name of the target database
        table_name: Name of the table to create
        columns_info: List of dictionaries with column information
        schema_name: Schema name in the lakehouse (default: "dbo")
        
    Returns:
        JSON string with operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from core.auth import get_access_token
        import urllib.parse
        from Microsoft.AnalysisServices.Tabular import Table, DataColumn, Partition, PartitionSourceType  # type: ignore
        from Microsoft.AnalysisServices.Tabular import EntityPartitionSource, ModeType, DataType, AggregateFunction  # type: ignore
        
        # Get access token automatically
        access_token = get_access_token()
        workspace_name_encoded = urllib.parse.quote(workspace_name)
        connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
        
        manager = TOMSemanticModelManager()
        result = manager.connect(connection_string, database_name)
        
        if not result["success"]:
            return json.dumps(result)
        
        # Create new table
        table = Table()
        table.Name = table_name
        table.LineageTag = f"{table_name}_table"
        table.SourceLineageTag = f"[{schema_name}].[{table_name}]"
        
        # Add columns to the table
        columns_added = []
        for col_info in columns_info:
            column = DataColumn()
            column.Name = col_info["name"]
            column.SourceColumn = col_info.get("sourceColumn", col_info["name"])
            column.LineageTag = f"{table_name}_{col_info['name']}"
            column.SourceLineageTag = col_info["name"]
            
            # Map data types
            data_type = col_info.get("dataType", "String")
            if data_type == "String":
                column.DataType = DataType.String
                column.SourceProviderType = "varchar(8000)"
            elif data_type == "Int64":
                column.DataType = DataType.Int64
                column.SourceProviderType = "int"
            elif data_type == "Decimal":
                column.DataType = DataType.Decimal
                column.SourceProviderType = "decimal(18,2)"
            elif data_type == "Double":
                column.DataType = DataType.Double
                column.SourceProviderType = "float"
            elif data_type == "DateTime":
                column.DataType = DataType.DateTime
                column.SourceProviderType = "datetime2"
            elif data_type == "Boolean":
                column.DataType = DataType.Boolean
                column.SourceProviderType = "bit"
            else:
                column.DataType = DataType.String  # Default fallback
                column.SourceProviderType = "varchar(8000)"
            
            # Set SummarizeBy if specified (important for numeric columns like SalesAmount)
            summarize_by = col_info.get("summarizeBy", "Default")
            if summarize_by == "Sum":
                column.SummarizeBy = AggregateFunction.Sum
            elif summarize_by == "Count":
                column.SummarizeBy = AggregateFunction.Count
            elif summarize_by == "Average":
                column.SummarizeBy = AggregateFunction.Average
            elif summarize_by == "None":
                column.SummarizeBy = AggregateFunction.None_
            else:
                column.SummarizeBy = AggregateFunction.Default
            
            table.Columns.Add(column)
            columns_added.append({
                "name": column.Name,
                "dataType": data_type,
                "sourceColumn": column.SourceColumn,
                "summarizeBy": summarize_by
            })
        
        # Create DirectLake partition
        partition = Partition()
        partition.Name = f"{table_name}_partition"
        # Handle Python.NET 3.0 enum conversion for Mode
        partition.Mode = ModeType.DirectLake
        
        # Create the partition source using EntityPartitionSource for DirectLake
        source = EntityPartitionSource()
        source.SchemaName = schema_name
        source.EntityName = table_name
        # FIX: Get reference to DatabaseQuery expression object, not string
        database_query_expression = manager.model.Expressions.Find("DatabaseQuery")
        if database_query_expression is None:
            return json.dumps({
                "success": False,
                "error": "DatabaseQuery expression not found. You must create it first using tom_add_lakehouse_expression_with_auth()"
            })
        source.ExpressionSource = database_query_expression  # Reference to actual expression object
        
        partition.Source = source
        table.Partitions.Add(partition)
        
        # Add table to model
        manager.model.Tables.Add(table)
        manager.model.SaveChanges()
        
        logger.info(f"Successfully added table '{table_name}' with {len(columns_added)} columns")
        
        return json.dumps({
            "success": True,
            "database_name": database_name,
            "table_name": table_name,
            "columns_added": columns_added,
            "partition_name": partition.Name,
            "schema_name": schema_name,
            "workspace_name": workspace_name,
            "message": f"Table '{table_name}' added successfully with DirectLake partition"
        })
        
    except Exception as e:
        logger.error(f"Error adding table with columns and partition: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name,
            "table_name": table_name,
            "workspace_name": workspace_name
        })
    finally:
        try:
            if 'manager' in locals():
                manager.disconnect()
        except:
            pass

def tom_add_relationships_to_model(connection_string: str, database_name: str,
                                 relationships_info: List[Dict]) -> str:
    """
    Add relationships between tables using TOM.
    
    Args:
        connection_string: Connection string for Analysis Services server
        database_name: Name of the target database
        relationships_info: List of relationship dictionaries with from/to table/column info
        
    Returns:
        JSON string with operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from Microsoft.AnalysisServices.Tabular import Server  # type: ignore
        
        # Connect directly using Server instead of manager
        server = Server()
        server.Connect(connection_string)
        
        try:
            # Get the target database
            database = server.Databases.FindByName(database_name)
            if not database:
                return json.dumps({
                    "success": False,
                    "error": f"Database '{database_name}' not found",
                    "available_databases": [db.Name for db in server.Databases]
                })
            
            model = database.Model
            relationships_added = []
            errors = []
            
            for i, rel_info in enumerate(relationships_info):
                try:
                    # Validate relationship info structure
                    required_fields = ["from_table", "from_column", "to_table", "to_column"]
                    missing_fields = [field for field in required_fields if field not in rel_info]
                    if missing_fields:
                        errors.append(f"Relationship {i}: Missing required fields: {missing_fields}")
                        continue
                    
                    # Find the tables using TOM Find method
                    from_table = model.Tables.Find(rel_info["from_table"])
                    to_table = model.Tables.Find(rel_info["to_table"])
                    
                    if not from_table:
                        errors.append(f"Relationship {i}: From table '{rel_info['from_table']}' not found")
                        continue
                    if not to_table:
                        errors.append(f"Relationship {i}: To table '{rel_info['to_table']}' not found")
                        continue
                    
                    # Find the columns using TOM Find method
                    from_column = from_table.Columns.Find(rel_info["from_column"])
                    to_column = to_table.Columns.Find(rel_info["to_column"])
                    
                    if not from_column:
                        errors.append(f"Relationship {i}: From column '{rel_info['from_column']}' not found in table '{rel_info['from_table']}'")
                        continue
                    if not to_column:
                        errors.append(f"Relationship {i}: To column '{rel_info['to_column']}' not found in table '{rel_info['to_table']}'")
                        continue
                    
                    # Check if relationship already exists
                    relationship_name = f"{rel_info['from_table']}_{rel_info['from_column']}_{rel_info['to_table']}_{rel_info['to_column']}"
                    existing_rel = model.Relationships.Find(relationship_name)
                    if existing_rel:
                        errors.append(f"Relationship {i}: Relationship '{relationship_name}' already exists")
                        continue
                    
                    # FIX: Create relationship using proper TOM object instantiation pattern
                    # Same pattern as measures: create object, set properties, add to collection
                    
                    try:
                        # Import the specific relationship class from .NET
                        from Microsoft.AnalysisServices.Tabular import SingleColumnRelationship  # type: ignore
                        
                        # Create new relationship object (like we do for measures)
                        relationship = SingleColumnRelationship()
                        relationship.Name = relationship_name
                        
                        # Set relationship endpoints
                        relationship.FromTable = from_table
                        relationship.FromColumn = from_column
                        relationship.ToTable = to_table
                        relationship.ToColumn = to_column
                        
                        # Set cross filtering behavior with proper enum handling
                        cross_filter = rel_info.get("cross_filtering_behavior", "OneDirection")
                        try:
                            # Import the enum type for cross filtering behavior
                            from Microsoft.AnalysisServices.Tabular import CrossFilteringBehavior  # type: ignore
                            
                            if cross_filter == "BothDirections":
                                relationship.CrossFilteringBehavior = CrossFilteringBehavior.BothDirections
                            else:
                                relationship.CrossFilteringBehavior = CrossFilteringBehavior.OneDirection
                                
                        except ImportError:
                            # Fallback: try with Enum conversion for Python.NET 3.0+
                            try:
                                from System import Enum  # type: ignore
                                if cross_filter == "BothDirections":
                                    relationship.CrossFilteringBehavior = Enum.ToObject(type(relationship.CrossFilteringBehavior), 2)
                                else:
                                    relationship.CrossFilteringBehavior = Enum.ToObject(type(relationship.CrossFilteringBehavior), 1)
                            except:
                                # Final fallback: skip setting cross filtering behavior
                                logger.warning(f"Could not set cross filtering behavior for relationship {relationship.Name}")
                                pass
                        
                        # Set additional properties
                        relationship.IsActive = True
                        
                        # Add the prepared relationship to the model (like we do for measures)
                        model.Relationships.Add(relationship)
                        
                    except ImportError:
                        # Fallback: try generic Relationship import
                        try:
                            from Microsoft.AnalysisServices.Tabular import Relationship  # type: ignore
                            
                            # Try to use generic Relationship class
                            relationship = Relationship()
                            relationship.Name = relationship_name
                            relationship.FromTable = from_table
                            relationship.FromColumn = from_column
                            relationship.ToTable = to_table
                            relationship.ToColumn = to_column
                            relationship.IsActive = True
                            
                            model.Relationships.Add(relationship)
                            
                        except Exception as fallback_error:
                            raise Exception(f"Could not create relationship with any method: {fallback_error}")
                    
                    except Exception as create_error:
                        raise Exception(f"Relationship creation failed: {create_error}")
                    
                    relationships_added.append({
                        "name": relationship.Name,
                        "from_table": rel_info["from_table"],
                        "from_column": rel_info["from_column"],
                        "to_table": rel_info["to_table"],
                        "to_column": rel_info["to_column"],
                        "cross_filtering": str(relationship.CrossFilteringBehavior) if hasattr(relationship, 'CrossFilteringBehavior') else "OneDirection",
                        "is_active": relationship.IsActive
                    })
                    
                    logger.info(f"Successfully prepared relationship: {relationship.Name}")
                    
                except Exception as rel_error:
                    error_msg = f"Relationship {i} error: {str(rel_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            # Save all changes at once
            if relationships_added:
                try:
                    model.SaveChanges()
                    logger.info(f"Successfully saved {len(relationships_added)} relationships")
                except Exception as save_error:
                    return json.dumps({
                        "success": False,
                        "error": f"Failed to save relationships: {str(save_error)}",
                        "relationships_prepared": len(relationships_added),
                        "errors": errors
                    })
            
            return json.dumps({
                "success": True,
                "database_name": database_name,
                "relationships_added": relationships_added,
                "total_relationships": len(relationships_added),
                "errors": errors,
                "message": f"Successfully added {len(relationships_added)} relationships" + 
                          (f" with {len(errors)} errors" if errors else "")
            })
            
        finally:
            # Always disconnect
            if server.Connected:
                server.Disconnect()
        
    except Exception as e:
        logger.error(f"Error adding relationships: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name
        })

def tom_discover_lakehouse_schema(workspace_id: str, lakehouse_id: str = None, 
                                lakehouse_name: str = None) -> str:
    """
    Discover tables and their schema from a Fabric lakehouse using SQL Analytics Endpoint.
    
    Args:
        workspace_id: The Fabric workspace ID
        lakehouse_id: Optional lakehouse ID
        lakehouse_name: Optional lakehouse name (alternative to lakehouse_id)
        
    Returns:
        JSON string with table schema information
    """
    try:
        # Import the lakehouse query function
        from tools.fabric_metadata import get_lakehouse_sql_connection_string
        from server import _internal_query_lakehouse_sql_endpoint
        
        # Get all tables in the lakehouse
        tables_query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' 
        AND TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'sys')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        tables_result = _internal_query_lakehouse_sql_endpoint(
            workspace_id, tables_query, lakehouse_id, lakehouse_name
        )
        
        if "error" in tables_result.lower():
            return json.dumps({
                "success": False,
                "error": f"Failed to get tables: {tables_result}"
            })
        
        tables_data = json.loads(tables_result)
        if not tables_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": "No tables found in lakehouse"
            })
        
        # For each table, get detailed column information
        tables_schema = []
        
        for table_row in tables_data["results"]:
            schema_name = table_row["TABLE_SCHEMA"]
            table_name = table_row["TABLE_NAME"]
            
            # Get columns for this table
            columns_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                ORDINAL_POSITION,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{schema_name}' 
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            
            columns_result = _internal_query_lakehouse_sql_endpoint(
                workspace_id, columns_query, lakehouse_id, lakehouse_name
            )
            
            if "error" not in columns_result.lower():
                columns_data = json.loads(columns_result)
                if columns_data.get("success", False):
                    table_info = {
                        "schema_name": schema_name,
                        "table_name": table_name,
                        "full_name": f"{schema_name}.{table_name}",
                        "columns": columns_data["results"]
                    }
                    tables_schema.append(table_info)
        
        return json.dumps({
            "success": True,
            "workspace_id": workspace_id,
            "lakehouse_id": lakehouse_id,
            "lakehouse_name": lakehouse_name,
            "tables": tables_schema,
            "total_tables": len(tables_schema)
        })
        
    except Exception as e:
        logger.error(f"Error discovering lakehouse schema: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

def tom_create_complete_model_from_lakehouse(connection_string: str, database_name: str,
                                           workspace_id: str, lakehouse_id: str = None,
                                           lakehouse_name: str = None, 
                                           table_names: List[str] = None,
                                           relationships: List[Dict] = None) -> str:
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
        table_names: Optional list of specific tables to include (if None, includes all)
        relationships: Optional list of relationships to create
        
    Returns:
        JSON string with complete operation results
    """
    try:
        # Step 1: Discover lakehouse schema
        logger.info("Step 1: Discovering lakehouse schema...")
        schema_result = tom_discover_lakehouse_schema(workspace_id, lakehouse_id, lakehouse_name)
        schema_data = json.loads(schema_result)
        
        if not schema_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": f"Failed to discover lakehouse schema: {schema_data.get('error', 'Unknown error')}",
                "step": "schema_discovery"
            })
        
        # Filter tables if specific ones are requested
        all_tables = schema_data["tables"]
        if table_names:
            filtered_tables = [t for t in all_tables if t["table_name"] in table_names]
        else:
            filtered_tables = all_tables
        
        if not filtered_tables:
            return json.dumps({
                "success": False,
                "error": "No matching tables found in lakehouse",
                "available_tables": [t["table_name"] for t in all_tables],
                "step": "table_filtering"
            })
        
        # Step 2: Get lakehouse connection info for data source expression
        logger.info("Step 2: Getting lakehouse connection information...")
        from tools.fabric_metadata import get_lakehouse_sql_connection_string
        connection_info = get_lakehouse_sql_connection_string(workspace_id, lakehouse_id, lakehouse_name)
        connection_data = json.loads(connection_info)
        
        server_name = connection_data.get("sql_endpoint", {}).get("server_name")
        endpoint_id = connection_data.get("sql_endpoint", {}).get("endpoint_id")
        
        if not server_name or not endpoint_id:
            return json.dumps({
                "success": False,
                "error": "Could not get SQL Analytics Endpoint information",
                "step": "connection_info"
            })
        
        # Step 3: Create empty semantic model
        logger.info("Step 3: Creating empty semantic model...")
        create_result = tom_create_empty_semantic_model(connection_string, database_name)
        create_data = json.loads(create_result)
        
        if not create_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": f"Failed to create empty model: {create_data.get('error', 'Unknown error')}",
                "step": "model_creation"
            })
        
        # Step 4: Add data source expression
        logger.info("Step 4: Adding data source expression...")
        expression_result = tom_add_data_source_expression(connection_string, database_name, server_name, endpoint_id)
        expression_data = json.loads(expression_result)
        
        if not expression_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": f"Failed to add data source expression: {expression_data.get('error', 'Unknown error')}",
                "step": "data_source_expression"
            })
        
        # Step 5: Add tables with columns and partitions
        logger.info("Step 5: Adding tables with columns and partitions...")
        tables_added = []
        
        for table_info in filtered_tables:
            table_result = tom_add_table_with_columns_and_partition(
                connection_string, database_name, 
                table_info["table_name"], 
                table_info["columns"],
                table_info["schema_name"]
            )
            table_data = json.loads(table_result)
            
            if table_data.get("success", False):
                tables_added.append(table_data)
                logger.info(f"Successfully added table: {table_info['table_name']}")
            else:
                logger.error(f"Failed to add table {table_info['table_name']}: {table_data.get('error', 'Unknown error')}")
        
        # Step 6: Add relationships (if provided)
        relationships_result = None
        if relationships:
            logger.info("Step 6: Adding relationships...")
            relationships_result = tom_add_relationships_to_model(connection_string, database_name, relationships)
        
        # Compile final results
        result = {
            "success": True,
            "database_name": database_name,
            "workspace_id": workspace_id,
            "lakehouse_id": lakehouse_id,
            "lakehouse_name": lakehouse_name,
            "server_name": server_name,
            "endpoint_id": endpoint_id,
            "tables_discovered": len(all_tables),
            "tables_included": len(filtered_tables),
            "tables_added": len(tables_added),
            "tables_details": tables_added,
            "relationships_result": json.loads(relationships_result) if relationships_result else None,
            "message": f"Successfully created semantic model '{database_name}' with {len(tables_added)} tables"
        }
        
        logger.info(f"Successfully completed model creation: {database_name}")
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error creating complete model from lakehouse: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "step": "orchestration"
        })

if __name__ == "__main__":
    # Test with local Power BI Desktop
    test_tom_connection()

def tom_refresh_semantic_model(connection_string: str, database_name: str, 
                              refresh_type: str = "full") -> str:
    """
    Refresh a semantic model to recalculate relationships and update data.
    
    This is essential after creating relationships in DirectLake models to ensure
    they are properly calculated and functional.
    
    Args:
        connection_string: Connection string for Analysis Services server
        database_name: Name of the database/semantic model to refresh
        refresh_type: Type of refresh ("full", "automatic", "dataOnly", "calculate", "clearValues")
        
    Returns:
        JSON string with refresh operation results
    """
    if not TOM_AVAILABLE:
        return json.dumps({"success": False, "error": "TOM libraries not available"})
    
    try:
        from Microsoft.AnalysisServices.Tabular import Server, RefreshType  # type: ignore
        from System import Enum  # type: ignore
        
        # Connect to server
        server = Server()
        server.Connect(connection_string)
        
        try:
            # Get the target database
            database = server.Databases.FindByName(database_name)
            if not database:
                return json.dumps({
                    "success": False,
                    "error": f"Database '{database_name}' not found",
                    "available_databases": [db.Name for db in server.Databases]
                })
            
            # Map refresh type string to enum
            refresh_type_map = {
                "full": "Full",
                "automatic": "Automatic", 
                "dataOnly": "DataOnly",
                "calculate": "Calculate",
                "clearValues": "ClearValues"
            }
            
            refresh_enum_value = refresh_type_map.get(refresh_type.lower(), "Full")
            
            # Parse the enum using text-based approach for Python.NET 3.0+
            refresh_enum = Enum.Parse(RefreshType, refresh_enum_value)
            
            logger.info(f"Starting {refresh_type} refresh of model '{database_name}'...")
            
            # Perform the refresh - this is synchronous and may take time
            database.Model.RequestRefresh(refresh_enum)
            database.Model.SaveChanges()
            
            logger.info(f"Successfully completed {refresh_type} refresh of model '{database_name}'")
            
            return json.dumps({
                "success": True,
                "database_name": database_name,
                "refresh_type": refresh_type,
                "message": f"Model '{database_name}' refreshed successfully with {refresh_type} refresh",
                "note": "Relationships should now be properly calculated and functional"
            })
            
        finally:
            # Always disconnect
            if server.Connected:
                server.Disconnect()
        
    except Exception as e:
        logger.error(f"Error refreshing semantic model: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "database_name": database_name,
            "refresh_type": refresh_type
        })

def tom_refresh_model_after_relationships(connection_string: str, database_name: str) -> str:
    """
    Convenience function to refresh a model after creating relationships.
    
    Uses a 'calculate' refresh which is faster than 'full' and sufficient for 
    recalculating relationships in DirectLake models.
    
    Args:
        connection_string: Connection string for Analysis Services server
        database_name: Name of the database/semantic model to refresh
        
    Returns:
        JSON string with refresh operation results
    """
    return tom_refresh_semantic_model(connection_string, database_name, "calculate")
