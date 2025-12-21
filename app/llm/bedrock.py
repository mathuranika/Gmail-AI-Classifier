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
        prompt = f"""
        You are an email classification engine.

Rules:
- Output ONLY valid JSON
- No explanations
- No text before or after json
- Use the exact keys and value formats as specified below.
- No markdown
- No repetition

Task:
Classify the email thread and determine urgency and required action.

Email:
"{email_text}"
Return JSON in exactly this format:
{{
  "category": "urgent | important | promotional | skip",
  "urgency_reason": "short reason",
  "needs_reply": boolean,
  "suggested_action": "short actionable instruction"
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
