from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from tools.dbsql import execute_sql_statement, get_statement_results
from tools.azureOpenAI import askAgriCoverLLM
import json

# GLOBAL SETTINGS & VALUES

load_dotenv()
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_WAREHOUSE_ID = os.getenv('DATABRICKS_WAREHOUSE_ID')
DATABRICKS_PAT = os.getenv('DATABRICKS_PAT')
AZURE_OPENAI_ENDPOINT_KEY = os.getenv('AZURE_OPENAI_ENDPOINT_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')


model_name = "gpt-4o-mini"
deployment = "gpt-4o-mini"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_ENDPOINT_KEY,
)


with open("./data/policies.json", "r") as file:
    CROP_INSURANCE_POLICIES = json.loads(file.read())



######################
## AGRICOVER FLASK APP
######################


app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process_form', methods=['POST'])
def process_form():
    # Extract form data
    form_data = {
        'crop_type': request.form.get('crop_type'),
        'county': request.form.get('county'),
        'field_size_acres': float(request.form.get('field_size_acres')),
        'planting_date': datetime.strptime(request.form.get('planting_date'), '%Y-%m-%d'),
        'drainage': request.form.get('drainage'),
        'tile_drained': request.form.get('tile_drained') == 'true',
        'tillage': request.form.get('tillage'),
        'nitrogen_rate': float(request.form.get('nitrogen_rate')),
        'previous_crop': request.form.get('previous_crop'),
        'coverage_level': float(request.form.get('coverage_level')),
        'unit_structure': request.form.get('unit_structure')
    }
    
    # For demonstration, create a sample response
    # In a real application, this would be calculated based on the form_data
    # get county trends
    county = form_data['county']
    sql_statement = f"SELECT * FROM maxf_demos.crop_insurance.illinois_yield_data WHERE county = '{county}' LIMIT 10"
    statement_id = execute_sql_statement(DATABRICKS_HOST, DATABRICKS_PAT, DATABRICKS_WAREHOUSE_ID, sql_statement)["statement_id"]
    try:
        county_trends = get_statement_results(statement_id, DATABRICKS_HOST, DATABRICKS_PAT).head(10).to_string()
    except Exception as e:
        print(e)
    

    available_policies = CROP_INSURANCE_POLICIES[form_data['crop_type'].lower()]
    crop_type = form_data['crop_type'].lower()


    policy_recommendation = askAgriCoverLLM(client, deployment, form_data, county_trends, available_policies, crop_type)


    return render_template('index.html', results=policy_recommendation)

if __name__ == '__main__':
    app.run(debug=True) 