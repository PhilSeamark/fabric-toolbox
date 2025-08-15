"""
Debug script to test TOM database selection with Power BI Service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.tom_semantic_model_tools_python import tom_list_tables_by_database_name
from core.auth import get_access_token
import urllib.parse

def test_database_selection():
    """Test explicit database selection with TOM"""
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token available")
        return
    
    # Construct server connection string (without catalog)
    workspace_name = "DAX Performance Tuner Testing"
    workspace_name_encoded = urllib.parse.quote(workspace_name)
    server_connection_string = f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};"
    
    print("🔍 Testing TOM database selection...")
    print(f"Server: {server_connection_string[:50]}...")
    
    # Test 1: Try to connect to Adventure Works Sales Analytics
    print("\n📊 Test 1: Adventure Works Sales Analytics")
    result1 = tom_list_tables_by_database_name(
        server_connection_string=server_connection_string,
        database_name="Adventure Works Sales Analytics"
    )
    print("Result:", result1[:500] + "..." if len(result1) > 500 else result1)
    
    # Test 2: Try to connect to Contoso 100M
    print("\n📊 Test 2: Contoso 100M")
    result2 = tom_list_tables_by_database_name(
        server_connection_string=server_connection_string,
        database_name="Contoso 100M"
    )
    print("Result:", result2[:500] + "..." if len(result2) > 500 else result2)

if __name__ == "__main__":
    test_database_selection()
