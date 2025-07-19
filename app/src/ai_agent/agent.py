import boto3
import os
import json
import requests

class IncidentAIAgent:
    # Supported models
    SUPPORTED_MODELS = {
        "gpt-3.5-turbo-instruct": "openai/gpt-3.5-turbo-instruct",
        "deepseek-r1": "deepseek/deepseek-r1:free",
        "claude-sonnet-4": "anthropic/claude-sonnet-4"
    }

    def __init__(self, model=None):
        secret_arn = os.environ.get("OPENROUTER_API_KEY_SECRET_ARN")
        self.api_key = self._get_openrouter_api_key(secret_arn)
        self.endpoint = "https://openrouter.ai/api/v1/completions"
        self.model = self.SUPPORTED_MODELS.get(model, "deepseek/deepseek-r1:free")  # Default to DeepSeek R1

    def _get_openrouter_api_key(self, secret_arn):
        region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
        session = boto3.session.Session(region_name=region)
        client = session.client(service_name='secretsmanager')
        get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret) if secret.startswith('{') else secret

    def analyze_incident(self, incident_context):
        prompt = f"Analyze this incident and suggest remediation:\n{incident_context}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 150
        }
        response = requests.post(self.endpoint, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["text"].strip()
        else:
            return f"Error from OpenRouter: {response.status_code} - {response.text}"