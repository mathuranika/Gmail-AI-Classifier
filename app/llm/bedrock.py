import boto3
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()


class BedrockClassifier:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION")
        )
        self.model_id = os.getenv("BEDROCK_MODEL_ID")

    def classify_email(self, email_text: str) -> dict:
        prompt = prompt = f"""
You are a strict JSON generator.

Rules (MANDATORY):
- Output ONLY valid JSON
- Output EXACTLY ONE JSON OBJECT
- DO NOT return an array
- DO NOT explain
- DO NOT add text before or after JSON

Classify the following email thread into ONE category:
urgent, important, promotional, or skip.

Email thread:
\"\"\"{email_text}\"\"\"

Return JSON in EXACTLY this format:
{{
  "category": "urgent | important | promotional | skip",
  "urgency_reason": "string",
  "needs_reply": true or false,
  "suggested_action": "string"
}}
"""

        body = {
            "prompt": prompt,
            "max_gen_len": 150,
            "temperature": 0.0,
            "top_p": 0.9
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        raw = json.loads(response["body"].read())["generation"]

        match = re.search(r"\{[\s\S]*?\}", raw)
        if not match:
            raise ValueError(f"Invalid JSON from Bedrock: {raw}")

        return json.loads(match.group())
