import requests
import pandas as pd
import time

def execute_sql_statement(databricks_host, databricks_token, warehouse_id, sql_statement):
    """
    Executes a SQL statement on a Databricks SQL warehouse.

    Parameters:
    - databricks_host (str): The Databricks host URL 
    - databricks_token (str): The Databricks token for authentication.
    - warehouse_id (str): The ID of the Databricks SQL warehouse.
    - sql_statement (str): The SQL statement to execute.
    
    Returns:
    - dict: The response containing the statement execution result.
    """

    
    # Define the headers
    headers = {
        "Authorization": f"Bearer {databricks_token}",
        "Content-Type": "application/json"
    }

    # Define the payload
    payload = {
        "warehouse_id": warehouse_id,
        "statement": sql_statement,
        "wait_timeout": "0s"
    }

    # Send the POST request to execute the SQL statement
    response = requests.post(
        f"https://{databricks_host}/api/2.0/sql/statements/",
        headers=headers,
        json=payload
    )

    # Check for errors in the response
    if response.status_code != 200:
        raise Exception(f"Error executing SQL statement: {response.text}")

    # Parse the response JSON
    response_data = response.json()

    # Extract and print statement_id and next_chunk_internal_link if available
    sql_statement_id = response_data.get('statement_id')
    try:
        next_chunk_internal_link = response_data.get('result', {}).get('next_chunk_internal_link')
        print(f"NEXT_CHUNK_INTERNAL_LINK={next_chunk_internal_link}")
    except:
        print("No Chunk")

    # Print extracted values
    print(f"SQL_STATEMENT_ID={sql_statement_id}")
    
    # Return the full response data for further processing
    return response_data



def get_statement_results(statement_id, databricks_host, token):
    """
    Fetch results from a Databricks SQL statement execution and convert to a pandas DataFrame
    
    Parameters:
    statement_id (str): The ID of the executed SQL statement
    databricks_host (str): The Databricks workspace URL (without https://)
    token (str): Databricks personal access token
    
    Returns:
    pandas.DataFrame: DataFrame containing the query results
    """
    # Construct the API URL
    url = f"https://{databricks_host}/api/2.0/sql/statements/{statement_id}"
    
    # Set up the headers with authentication
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Make the API request
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    # Parse the JSON response
    result_json = response.json()
    
    # Check if the query succeeded
    count_to_twenty_seconds = 0
    while result_json['status']['state'] != "SUCCEEDED":
        time.sleep(1)
        count_to_twenty_seconds += 1
        if count_to_twenty_seconds > 20:
            raise Exception("Query took too long to complete")
            
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
            result_json = response.json()
            
            # Check for error state
            state = result_json['status']['state']
            if state == "FAILED":
                error_message = result_json['status'].get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Query failed with status {state}: {error_message}")
                
        except Exception as e:
            if "Query failed" in str(e) or "API request failed" in str(e):
                raise
            print("Waiting for query to complete...")
    
    # Extract column names from the schema
    columns = []
    if 'manifest' in result_json and 'schema' in result_json['manifest']:
        columns = [col['name'] for col in result_json['manifest']['schema']['columns']]
    
    # Extract data from the result
    data = []
    if 'result' in result_json and 'data_array' in result_json['result']:
        data = result_json['result']['data_array']
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    # Convert data types if needed
    if 'manifest' in result_json and 'schema' in result_json['manifest']:
        for col in result_json['manifest']['schema']['columns']:
            col_name = col['name']
            type_name = col['type_name']
            
            # Convert common types
            if type_name in ['INTEGER', 'LONG', 'BIGINT']:
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            elif type_name in ['FLOAT', 'DOUBLE', 'DECIMAL']:
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            elif type_name in ['BOOLEAN']:
                df[col_name] = df[col_name].map({'true': True, 'false': False})
    
    return df

