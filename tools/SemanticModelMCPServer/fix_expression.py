from tools.tom_semantic_model_tools_python import TOMSemanticModelManager
from core.auth import get_access_token
import urllib.parse

# Get authentication token
access_token = get_access_token()
workspace_name = 'DAX Performance Tuner Testing'
workspace_name_encoded = urllib.parse.quote(workspace_name)
connection_string = f'Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name_encoded};Password={access_token};'

print('Updating existing DatabaseQuery expression...')

try:
    from Microsoft.AnalysisServices.Tabular import Server  # type: ignore
    
    # Connect to server
    server = Server()
    server.Connect(connection_string)
    
    # Get database
    database_name = 'Complete Adventure Works DirectLake Model'
    database = server.Databases.GetByName(database_name)
    
    # Find and update existing expression
    expression = database.Model.Expressions.Find('DatabaseQuery')
    if expression:
        print('Found existing expression:')
        print(f'Current: {expression.Expression}')
        
        # CORRECTED M expression with proper case and endpoint ID
        server_name = 'X6EPS4XRQ2XUDENLFV6NAEO3I4-7334LQXNGLFURIJ7LVEZIWSJDU.msit-datawarehouse.fabric.microsoft.com'
        endpoint_id = 'c1a9f62a-3a88-4732-b0ee-eae6830723e7'
        
        new_expression = f'''let
    database = Sql.Database("{server_name}", "{endpoint_id}")
in
    database'''
        
        # Update expression
        expression.Expression = new_expression
        
        # Save changes
        database.Model.SaveChanges()
        
        print('Updated expression to:')
        print(f'New: {expression.Expression}')
        print('SUCCESS: Expression updated with correct server case and endpoint ID!')
    else:
        print('No DatabaseQuery expression found')
        
except Exception as e:
    print(f'Error: {e}')
finally:
    try:
        server.Disconnect()
    except:
        pass
