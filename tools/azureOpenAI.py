import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import json



def askAgriCoverLLM(client, deployment, form_data, county_trends, available_policies, crop_type):
    
    prompt = f"""
    You are an agricultural insurance specialist. Your task is to analyze farm data and select the most appropriate 
    insurance policy from the available options for Illinois farmers.
    
    FARMER DATA:
    ```
    {json.dumps(form_data, indent=2, default=str)}
    ```
    
    COUNTY YIELD TRENDS:
    ```
    {county_trends}
    ```
    
    AVAILABLE POLICY OPTIONS FOR {crop_type.upper()}:
    ```
    {json.dumps(available_policies, indent=2)}
    ```
    
    INSTRUCTIONS:
    1. Analyze the farmer's data and county yield trends.
    2. Assess risk level (low, moderate, high) based on crop type, location, field conditions, and historical trends.
    3. Select ONE policy from the available options that best matches the farmer's risk profile and needs.
    4. Return your selection in the EXACT JSON structure shown below.
    
    REQUIRED OUTPUT FORMAT:
    {{
        "selected_policy": "POLICY_NAME",
        "risk_assessment": {{
            "risk_level": "low/moderate/high",
            "key_factors": [
                "Factor 1: Details",
                "Factor 2: Details",
                "Factor 3: Details"
            ]
        }},
        "recommendation_explanation": "Detailed explanation of why this policy is the best fit...",
        "policy_details": {{
            "coverage_level": 0.XX,
            "premium_per_acre": XX.XX,
            "total_premium": XX.XX
        }}
    }}
    
    IMPORTANT GUIDELINES:
    1. Risk Assessment:
       - Use the actual values from form_data in key_factors
       - Determine risk level based on historical yield data and environmental factors
       - Include at least three key factors that influenced your decision
    
    2. Policy Selection:
       - Select exactly ONE policy from the available options
       - The policy should match the assessed risk level
       - Do not create a new policy or modify the existing options
    
    3. Total Premium Calculation:
       - Calculate total_premium as premium_per_acre * field_size_acres, rounded to 2 decimal places
    
    4. Recommendation Explanation:
       - Provide a detailed explanation (3-5 sentences) that references specific data points
       - Explain why the selected policy is appropriate for this specific farm situation
    
    IMPORTANT:
    - Only include the JSON object in your response with no additional text
    """

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a specialized agricultural insurance expert that provides policy recommendations based on farm data analysis.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=deployment
    )
    
    return json.loads(response.choices[0].message.content)


