"""
Best Practice Analyzer integration for the Semantic Model MCP Server
"""

import os
import json
from typing import Dict, List, Any, Optional
from .bpa_analyzer import BPAAnalyzer, BPAViolation, BPASeverity

class BPAService:
    """Service class for integrating BPA functionality into the MCP server"""
    
    def __init__(self, server_directory: str):
        """
        Initialize the BPA service
        
        Args:
            server_directory: The root directory of the MCP server
        """
        self.server_directory = server_directory
        self.rules_file = os.path.join(server_directory, "core", "bpa.json")
        self.analyzer = None
        
        # Initialize the analyzer if rules file exists
        if os.path.exists(self.rules_file):
            self.analyzer = BPAAnalyzer(self.rules_file)
    
    def analyze_model_from_tmsl(self, tmsl_definition: str) -> Dict[str, Any]:
        """
        Analyze a TMSL model and return BPA violations
        
        Args:
            tmsl_definition: TMSL JSON string
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.analyzer:
            return {
                'error': 'BPA rules not loaded. Please check if bpa.json exists.',
                'violations': [],
                'summary': {}
            }
        
        try:
            # Preprocess TMSL definition to handle formatting issues
            cleaned_tmsl = self._clean_tmsl_json(tmsl_definition)
            
            # Format/tidy the TMSL JSON for better BPA rule analysis
            formatted_tmsl = self._format_tmsl_json(cleaned_tmsl)
            
            # Parse TMSL
            tmsl_model = json.loads(formatted_tmsl)
            
            # Run analysis
            violations = self.analyzer.analyze_model(tmsl_model)
            
            # Get summary
            summary = self.analyzer.get_violations_summary()
            
            # Export violations
            violations_dict = self.analyzer.export_violations_to_dict()
            
            return {
                'success': True,
                'violations': violations_dict,
                'summary': summary,
                'rules_count': len(self.analyzer.rules),
                'analysis_complete': True
            }
            
        except json.JSONDecodeError as e:
            return {
                'error': f'Invalid TMSL JSON: {str(e)}',
                'violations': [],
                'summary': {}
            }
        except Exception as e:
            return {
                'error': f'Analysis failed: {str(e)}',
                'violations': [],
                'summary': {}
            }
    
    def get_violations_by_severity(self, severity_name: str) -> List[Dict[str, Any]]:
        """Get violations filtered by severity level"""
        if not self.analyzer:
            return []
        
        try:
            severity = BPASeverity[severity_name.upper()]
            violations = self.analyzer.get_violations_by_severity(severity)
            return [
                {
                    'rule_id': v.rule_id,
                    'rule_name': v.rule_name,
                    'category': v.category,
                    'object_type': v.object_type,
                    'object_name': v.object_name,
                    'table_name': v.table_name,
                    'description': v.description,
                    'fix_expression': v.fix_expression
                }
                for v in violations
            ]
        except KeyError:
            return []
    
    def get_violations_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get violations filtered by category"""
        if not self.analyzer:
            return []
        
        violations = self.analyzer.get_violations_by_category(category)
        return [
            {
                'rule_id': v.rule_id,
                'rule_name': v.rule_name,
                'severity': v.severity.name,
                'object_type': v.object_type,
                'object_name': v.object_name,
                'table_name': v.table_name,
                'description': v.description,
                'fix_expression': v.fix_expression
            }
            for v in violations
        ]
    
    def get_available_categories(self) -> List[str]:
        """Get list of available BPA rule categories"""
        if not self.analyzer:
            return []
        
        categories = set()
        for rule in self.analyzer.rules:
            categories.add(rule.category)
        
        return sorted(list(categories))
    
    def get_available_severities(self) -> List[Dict[str, Any]]:
        """Get list of available severity levels"""
        return [
            {'name': 'INFO', 'level': 1, 'description': 'Informational - suggestions for improvement'},
            {'name': 'WARNING', 'level': 2, 'description': 'Warning - potential issues that should be addressed'},
            {'name': 'ERROR', 'level': 3, 'description': 'Error - critical issues that should be fixed immediately'}
        ]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of loaded BPA rules"""
        if not self.analyzer:
            return {
                'error': 'BPA rules not loaded',
                'total_rules': 0,
                'categories': [],
                'severities': []
            }
        
        categories = {}
        severities = {}
        
        for rule in self.analyzer.rules:
            # Count by category
            categories[rule.category] = categories.get(rule.category, 0) + 1
            
            # Count by severity
            severity_name = rule.severity.name
            severities[severity_name] = severities.get(severity_name, 0) + 1
        
        return {
            'total_rules': len(self.analyzer.rules),
            'categories': categories,
            'severities': severities,
            'rules_file': self.rules_file
        }
    
    def format_violations_for_display(self, violations: List[Dict[str, Any]], 
                                    group_by: str = 'category') -> Dict[str, Any]:
        """
        Format violations for display, grouped by category or severity
        
        Args:
            violations: List of violation dictionaries
            group_by: How to group violations ('category', 'severity', 'object_type')
            
        Returns:
            Formatted violations grouped for display
        """
        if not violations:
            return {'groups': {}, 'total': 0}
        
        groups = {}
        
        for violation in violations:
            group_key = violation.get(group_by, 'Unknown')
            
            if group_key not in groups:
                groups[group_key] = {
                    'violations': [],
                    'count': 0
                }
            
            groups[group_key]['violations'].append(violation)
            groups[group_key]['count'] += 1
        
        # Sort groups by count (descending)
        sorted_groups = dict(sorted(groups.items(), 
                                  key=lambda x: x[1]['count'], 
                                  reverse=True))
        
        return {
            'groups': sorted_groups,
            'total': len(violations),
            'group_by': group_by
        }
    
    def generate_bpa_report(self, tmsl_definition: str, 
                          format_type: str = 'summary') -> Dict[str, Any]:
        """
        Generate a comprehensive BPA report
        
        Args:
            tmsl_definition: TMSL JSON string
            format_type: Type of report ('summary', 'detailed', 'by_category')
            
        Returns:
            Formatted BPA report
        """
        analysis_result = self.analyze_model_from_tmsl(tmsl_definition)
        
        if not analysis_result.get('success'):
            return analysis_result
        
        violations = analysis_result['violations']
        summary = analysis_result['summary']
        
        report = {
            'analysis_summary': summary,
            'rules_applied': analysis_result['rules_count'],
            'timestamp': json.dumps(None),  # Would use datetime in real implementation
            'format_type': format_type
        }
        
        if format_type == 'summary':
            report['violations_by_severity'] = {
                'ERROR': [v for v in violations if v['severity'] == 'ERROR'],
                'WARNING': [v for v in violations if v['severity'] == 'WARNING'],  
                'INFO': [v for v in violations if v['severity'] == 'INFO']
            }
            
        elif format_type == 'detailed':
            report['all_violations'] = violations
            
        elif format_type == 'by_category':
            categories = {}
            for violation in violations:
                category = violation['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(violation)
            
            report['violations_by_category'] = categories
        
        return report
    
    def _clean_tmsl_json(self, tmsl_definition: str) -> str:
        """
        Clean and preprocess TMSL JSON string to handle common formatting issues
        
        Args:
            tmsl_definition: Raw TMSL JSON string
            
        Returns:
            Cleaned JSON string ready for parsing
        """
        # Remove carriage returns and normalize line endings
        cleaned = tmsl_definition.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # If the string is already valid JSON, try parsing it first
        try:
            # Test if it's already valid JSON
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            # If not valid, try additional cleaning steps
            pass
        
        # Handle common issues with escaped JSON strings
        # If the string starts and ends with quotes, it might be a JSON string containing JSON
        if cleaned.startswith('"') and cleaned.endswith('"'):
            try:
                # Try to decode it as a JSON string
                decoded = json.loads(cleaned)
                if isinstance(decoded, str):
                    # If successful and result is a string, use that as the TMSL
                    cleaned = decoded
            except json.JSONDecodeError:
                # If that fails, remove the outer quotes manually
                cleaned = cleaned[1:-1]
        
        # Handle escaped quotes and backslashes
        cleaned = cleaned.replace('\\"', '"').replace('\\\\', '\\')
        
        # Handle escaped newlines in JSON strings
        cleaned = cleaned.replace('\\n', '\n').replace('\\t', '\t')
        
        return cleaned
    
    def _format_tmsl_json(self, tmsl_json: str) -> str:
        """
        Format and tidy TMSL JSON for better BPA rule analysis
        
        This method takes cleaned JSON and formats it consistently to improve
        BPA rule matching and analysis accuracy.
        
        Args:
            tmsl_json: Cleaned TMSL JSON string
            
        Returns:
            Formatted and tidied JSON string
        """
        try:
            # Parse the JSON to ensure it's valid
            tmsl_data = json.loads(tmsl_json)
            
            # Apply consistent formatting and structure
            formatted_data = self._tidy_tmsl_structure(tmsl_data)
            
            # Re-serialize with consistent formatting
            # Use separators to ensure consistent spacing
            # Use sort_keys=True for predictable key ordering (helps with rule matching)
            formatted_json = json.dumps(
                formatted_data,
                indent=2,
                separators=(',', ': '),
                sort_keys=True,
                ensure_ascii=False
            )
            
            return formatted_json
            
        except json.JSONDecodeError as e:
            # If formatting fails, return the original cleaned JSON
            print(f"Warning: TMSL JSON formatting failed: {str(e)}. Using original cleaned JSON.")
            return tmsl_json
        except Exception as e:
            # If any other error occurs, return the original cleaned JSON
            print(f"Warning: TMSL JSON tidying failed: {str(e)}. Using original cleaned JSON.")
            return tmsl_json
    
    def _tidy_tmsl_structure(self, tmsl_data: dict) -> dict:
        """
        Apply structural improvements to TMSL data for better BPA analysis
        
        Args:
            tmsl_data: Parsed TMSL data structure
            
        Returns:
            Tidied TMSL data structure
        """
        # Create a deep copy to avoid modifying the original
        import copy
        tidied_data = copy.deepcopy(tmsl_data)
        
        # Apply standardization to improve BPA rule matching
        tidied_data = self._standardize_tmsl_model_structure(tidied_data)
        
        return tidied_data
    
    def _standardize_tmsl_model_structure(self, tmsl_data: dict) -> dict:
        """
        Standardize TMSL model structure for consistent BPA analysis
        
        This ensures that:
        1. Model properties are consistently ordered
        2. Array elements (tables, columns, measures) are sorted for predictable analysis
        3. Missing optional properties are normalized
        4. Data types are consistently formatted
        
        Args:
            tmsl_data: TMSL data structure
            
        Returns:
            Standardized TMSL structure
        """
        # Find the model object in various possible TMSL structures
        model = None
        if 'create' in tmsl_data and 'database' in tmsl_data['create'] and 'model' in tmsl_data['create']['database']:
            model = tmsl_data['create']['database']['model']
        elif 'model' in tmsl_data:
            model = tmsl_data['model']
        elif 'createOrReplace' in tmsl_data and 'database' in tmsl_data['createOrReplace'] and 'model' in tmsl_data['createOrReplace']['database']:
            model = tmsl_data['createOrReplace']['database']['model']
        
        if not model:
            return tmsl_data
        
        # Standardize tables array
        if 'tables' in model and isinstance(model['tables'], list):
            for table in model['tables']:
                self._standardize_table_structure(table)
                
            # Sort tables by name for consistent ordering
            model['tables'].sort(key=lambda x: x.get('name', ''))
        
        # Standardize relationships array
        if 'relationships' in model and isinstance(model['relationships'], list):
            # Sort relationships for consistent ordering
            model['relationships'].sort(key=lambda x: f"{x.get('fromTable', '')}.{x.get('fromColumn', '')}")
        
        # Standardize expressions array
        if 'expressions' in model and isinstance(model['expressions'], list):
            # Sort expressions by name for consistent ordering
            model['expressions'].sort(key=lambda x: x.get('name', ''))
        
        return tmsl_data
    
    def _standardize_table_structure(self, table: dict) -> None:
        """
        Standardize individual table structure for consistent BPA analysis
        
        Args:
            table: Table object to standardize (modified in place)
        """
        # Standardize columns array
        if 'columns' in table and isinstance(table['columns'], list):
            for column in table['columns']:
                self._standardize_column_structure(column)
                
            # Sort columns: key columns first, then by name
            def column_sort_key(col):
                is_key = col.get('isKey', False)
                name = col.get('name', '')
                return (not is_key, name)  # False sorts before True, so keys come first
                
            table['columns'].sort(key=column_sort_key)
        
        # Standardize measures array
        if 'measures' in table and isinstance(table['measures'], list):
            for measure in table['measures']:
                self._standardize_measure_structure(measure)
                
            # Sort measures by name for consistent ordering
            table['measures'].sort(key=lambda x: x.get('name', ''))
        
        # Standardize partitions array
        if 'partitions' in table and isinstance(table['partitions'], list):
            # Sort partitions by name
            table['partitions'].sort(key=lambda x: x.get('name', ''))
        
        # Standardize hierarchies array
        if 'hierarchies' in table and isinstance(table['hierarchies'], list):
            # Sort hierarchies by name
            table['hierarchies'].sort(key=lambda x: x.get('name', ''))
    
    def _standardize_column_structure(self, column: dict) -> None:
        """
        Standardize individual column structure
        
        Args:
            column: Column object to standardize (modified in place)
        """
        # Ensure boolean properties are consistently represented
        for bool_prop in ['isHidden', 'isKey', 'isNullable', 'isUnique']:
            if bool_prop in column:
                column[bool_prop] = bool(column[bool_prop])
        
        # Standardize dataType casing
        if 'dataType' in column:
            data_type = column['dataType']
            if isinstance(data_type, str):
                # Ensure consistent casing for common data types
                data_type_map = {
                    'string': 'String',
                    'int64': 'Int64', 
                    'decimal': 'Decimal',
                    'double': 'Double',
                    'datetime': 'DateTime',
                    'boolean': 'Boolean'
                }
                column['dataType'] = data_type_map.get(data_type.lower(), data_type)
    
    def _standardize_measure_structure(self, measure: dict) -> None:
        """
        Standardize individual measure structure
        
        Args:
            measure: Measure object to standardize (modified in place)
        """
        # Ensure boolean properties are consistently represented
        for bool_prop in ['isHidden']:
            if bool_prop in measure:
                measure[bool_prop] = bool(measure[bool_prop])
        
        # Normalize formatString property
        if 'formatString' in measure and not measure['formatString']:
            # Remove empty format strings
            del measure['formatString']
