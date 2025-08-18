"""
BPA (Best Practice Analyzer) Tools for Semantic Model MCP Server

This module contains all BPA-related MCP tools for analyzing semantic models
and TMSL definitions against best practice rules.
"""

import os
from fastmcp import FastMCP
import json
from core.bpa_service import BPAService

def register_bpa_tools(mcp: FastMCP):
    """Register all BPA-related MCP tools"""

    @mcp.tool
    def analyze_model_bpa(workspace_name: str, dataset_name: str) -> str:
        """Analyze a semantic model against Best Practice Analyzer (BPA) rules.

        This tool retrieves the TMSL definition of a model and runs it through
        a comprehensive set of best practice rules to identify potential issues.
        
        OPTIMIZED: Handles large TMSL processing server-side to avoid chat context bloat.

        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to analyze

        Returns:
            JSON string with BPA analysis results including violations and summary
        """
        try:
            # Import required modules
            import sys
            import os
            
            # Add the parent directory to sys.path to import server functions
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            # Import server functions for TMSL retrieval
            from server import get_model_definition
            from core.bpa_service import BPAService
            
            # Step 1: Get TMSL definition (server-side, not exposed to chat)
            tmsl_definition = get_model_definition(workspace_name, dataset_name)
            
            if not tmsl_definition or tmsl_definition.startswith("Error:"):
                return json.dumps({
                    'success': False,
                    'error': f'Failed to retrieve model definition: {tmsl_definition}',
                    'error_type': 'model_retrieval_error'
                })
            
            # Step 2: Run BPA analysis (server-side)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            analysis_result = bpa_service.analyze_model_from_tmsl(tmsl_definition)
            
            # Step 3: Add optimization metrics for transparency
            tmsl_size_kb = len(tmsl_definition) / 1024
            analysis_result['optimization_info'] = {
                'tmsl_size_kb': round(tmsl_size_kb, 2),
                'processed_server_side': True,
                'chat_context_saved': f"~{round(tmsl_size_kb)}KB of TMSL data kept server-side"
            }
            
            return json.dumps(analysis_result, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'BPA analysis failed: {str(e)}',
                'error_type': 'bpa_analysis_error'
            })

    @mcp.tool  
    def analyze_tmsl_bpa(tmsl_definition: str) -> str:
        """Analyze a TMSL definition directly against Best Practice Analyzer (BPA) rules.

        This tool takes a TMSL JSON string and analyzes it against a comprehensive
        set of best practice rules to identify potential issues.
        
        The tool automatically handles JSON formatting issues and enhances analysis through:
        - Carriage returns and line ending normalization
        - Escaped quotes and backslashes handling
        - Nested JSON string decoding
        - **Enhanced JSON formatting and tidying for better BPA rule analysis**
        - Consistent property ordering and structure standardization
        - Data type normalization and boolean property standardization

        Args:
            tmsl_definition: TMSL JSON string (raw or escaped format)

        Returns:
            JSON string with BPA analysis results including violations and summary
        """
        try:
            # Get the server directory (parent of tools directory)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            result = bpa_service.analyze_model_from_tmsl(tmsl_definition)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'TMSL BPA analysis failed: {str(e)}',
                'error_type': 'tmsl_bpa_analysis_error'
            })

    @mcp.tool
    def get_bpa_violations_by_severity(severity: str) -> str:
        """Get BPA violations filtered by severity level.

        Note: You must run analyze_model_bpa or analyze_tmsl_bpa first to generate violations.

        Args:
            severity: Severity level to filter by (INFO, WARNING, ERROR)

        Returns:
            JSON string with filtered violations
        """
        try:
            # Get the server directory (parent of tools directory)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            violations = bpa_service.get_violations_by_severity(severity)
            
            return json.dumps({
                'success': True,
                'severity_filter': severity,
                'violation_count': len(violations),
                'violations': violations
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Error filtering BPA violations by severity: {str(e)}',
                'error_type': 'bpa_filter_error'
            })

    @mcp.tool
    def get_bpa_violations_by_category(category: str) -> str:
        """Get BPA violations filtered by category.

        Note: You must run analyze_model_bpa or analyze_tmsl_bpa first to generate violations.

        Args:
            category: Category to filter by (Performance, DAX Expressions, Maintenance, Naming Conventions, Formatting)

        Returns:
            JSON string with filtered violations
        """
        try:
            # Get the server directory (parent of tools directory)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            violations = bpa_service.get_violations_by_category(category)
            
            return json.dumps({
                'success': True,
                'category_filter': category,
                'violation_count': len(violations),
                'violations': violations
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Error filtering BPA violations by category: {str(e)}',
                'error_type': 'bpa_filter_error'
            })

    @mcp.tool
    def get_bpa_rules_summary() -> str:
        """Get summary information about loaded BPA rules.

        Returns:
            JSON string with rules summary including counts by category and severity
        """
        try:
            # Get the server directory (parent of tools directory)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            summary = bpa_service.get_rules_summary()
            
            return json.dumps({
                'success': True,
                'rules_summary': summary
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Error getting BPA rules summary: {str(e)}',
                'error_type': 'bpa_rules_error'
            })

    @mcp.tool
    def analyze_model_bpa_summary(workspace_name: str, dataset_name: str) -> str:
        """Get a lightweight BPA summary for a semantic model without detailed violation data.
        
        OPTIMIZED: Returns only key metrics and counts to minimize chat context usage.
        Use this when you only need overview information, not detailed violation lists.

        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to analyze

        Returns:
            JSON string with lightweight BPA summary (counts, top issues, recommendations)
        """
        try:
            # Import required modules
            import sys
            import os
            
            # Add the parent directory to sys.path to import server functions
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            # Import server functions for TMSL retrieval
            from server import get_model_definition
            from core.bpa_service import BPAService
            
            # Step 1: Get TMSL definition (server-side)
            tmsl_definition = get_model_definition(workspace_name, dataset_name)
            
            if not tmsl_definition or tmsl_definition.startswith("Error:"):
                return json.dumps({
                    'success': False,
                    'error': f'Failed to retrieve model definition: {tmsl_definition}',
                    'error_type': 'model_retrieval_error'
                })
            
            # Step 2: Run BPA analysis (server-side)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            analysis_result = bpa_service.analyze_model_from_tmsl(tmsl_definition)
            
            if not analysis_result.get('success'):
                return json.dumps(analysis_result)
            
            # Step 3: Extract only summary information (no detailed violations)
            violations = analysis_result.get('violations', [])
            summary = analysis_result.get('summary', {})
            
            # Count by severity
            severity_counts = {'ERROR': 0, 'WARNING': 0, 'INFO': 0}
            category_counts = {}
            top_issues = []
            
            for violation in violations:
                severity = violation.get('severity', 'INFO')
                if severity in severity_counts:
                    severity_counts[severity] += 1
                
                category = violation.get('category', 'Unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Collect top ERROR violations
                if severity == 'ERROR' and len(top_issues) < 5:
                    top_issues.append({
                        'rule_name': violation.get('rule_name'),
                        'object_type': violation.get('object_type'),
                        'object_name': violation.get('object_name'),
                        'category': violation.get('category')
                    })
            
            # Create lightweight summary
            lightweight_summary = {
                'success': True,
                'workspace_name': workspace_name,
                'dataset_name': dataset_name,
                'total_violations': len(violations),
                'severity_breakdown': severity_counts,
                'category_breakdown': category_counts,
                'top_critical_issues': top_issues,
                'recommendations': [],
                'optimization_info': {
                    'tmsl_size_kb': round(len(tmsl_definition) / 1024, 2),
                    'violations_summarized': len(violations),
                    'data_reduction': f"Reduced {len(violations)} violations to summary format"
                }
            }
            
            # Add recommendations based on counts
            if severity_counts['ERROR'] > 0:
                lightweight_summary['recommendations'].append(
                    f"CRITICAL: Fix {severity_counts['ERROR']} ERROR-level issues first"
                )
            if severity_counts['WARNING'] > 5:
                lightweight_summary['recommendations'].append(
                    f"Review {severity_counts['WARNING']} WARNING-level performance/maintainability issues"
                )
            if category_counts.get('Performance', 0) > 0:
                lightweight_summary['recommendations'].append(
                    f"Address {category_counts['Performance']} performance optimization opportunities"
                )
            
            return json.dumps(lightweight_summary, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'BPA summary analysis failed: {str(e)}',
                'error_type': 'bpa_summary_error'
            })

    @mcp.tool
    def get_bpa_categories() -> str:
        """Get list of available BPA rule categories.

        Returns:
            JSON string with list of available categories
        """
        try:
            # Get the server directory (parent of tools directory)
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            categories = bpa_service.get_available_categories()
            
            return json.dumps({
                'success': True,
                'available_categories': categories
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Error getting BPA categories: {str(e)}',
                'error_type': 'bpa_categories_error'
            })

    @mcp.tool
    def generate_bpa_report(workspace_name: str, dataset_name: str, format_type: str = 'summary') -> str:
        """Generate a comprehensive Best Practice Analyzer report for a semantic model.

        Args:
            workspace_name: The Power BI workspace name
            dataset_name: The dataset/model name to analyze  
            format_type: Report format ('summary', 'detailed', 'by_category')

        Returns:
            JSON string with comprehensive BPA report
        """
        try:
            # Import required modules for PowerBI connection
            import urllib.parse
            import sys
            import os
            
            # Add .NET assemblies path
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dotnet_dir = os.path.join(script_dir, "dotnet")
            
            sys.path.append(script_dir)
            import clr
            clr.AddReference(os.path.join(dotnet_dir, "Microsoft.AnalysisServices.Tabular.dll"))
            clr.AddReference(os.path.join(dotnet_dir, "Microsoft.Identity.Client.dll"))
            clr.AddReference(os.path.join(dotnet_dir, "Microsoft.IdentityModel.Abstractions.dll"))
            
            from Microsoft.AnalysisServices.Tabular import Server, Database, JsonSerializer, SerializeOptions # type: ignore
            
            # Import auth function from core
            from core.auth import get_access_token
            
            # Get access token
            access_token = get_access_token()
            if not access_token:
                return json.dumps({
                    'success': False,
                    'error': "No valid access token available",
                    'error_type': 'auth_error'
                })

            # Connect to Power BI and get TMSL definition
            workspace_name_encoded = urllib.parse.quote(workspace_name)
            connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token}"

            server = Server()
            server.Connect(connection_string)
            
            # Find the database/dataset
            database = None
            for db in server.Databases:
                if db.Name == dataset_name:
                    database = db
                    break
            
            if not database:
                server.Disconnect()
                return json.dumps({
                    'success': False,
                    'error': f"Dataset '{dataset_name}' not found in workspace '{workspace_name}'",
                    'error_type': 'dataset_not_found'
                })
            
            # Get TMSL definition
            options = SerializeOptions()
            options.IgnoreInferredObjects = True
            options.IgnoreInferredProperties = True
            options.IgnoreTimestamps = True
            options.SplitMultilineStrings = True
            
            tmsl_definition = JsonSerializer.SerializeDatabase(database, options)
            server.Disconnect()
            
            # Generate BPA report
            server_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bpa_service = BPAService(server_directory)
            report = bpa_service.generate_bpa_report(tmsl_definition, format_type)
            
            return json.dumps({
                'success': True,
                'workspace_name': workspace_name,
                'dataset_name': dataset_name,
                'format_type': format_type,
                'report': report
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Error generating BPA report: {str(e)}',
                'error_type': 'bpa_report_error'
            })
