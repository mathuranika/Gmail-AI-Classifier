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
- No text before or after JSON
- No markdown
- No repetition
- Use exact key names and value types

Task:
Classify the email thread and determine urgency and required action.

Email:
\"\"\"{email_text}\"\"\"

Return JSON in exactly this format:
{{
  "category": "urgent | important | promotional | skip",
  "urgency_reason": "short reason",
  "needs_reply": true or false,
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

        # -------- FIX STARTS HERE --------

        cleaned = raw.strip()

        # Remove markdown fences if model adds them
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned)
            cleaned = re.sub(r"```$", "", cleaned)
            cleaned = cleaned.strip()

        # Extract first JSON object only
        match = re.search(r"\{[\s\S]*?\}", cleaned)
        if not match:
            raise ValueError(f"Invalid JSON from Bedrock: {raw}")

        parsed = json.loads(match.group())

        # Enforce correct boolean type
        parsed["needs_reply"] = bool(parsed.get("needs_reply"))

        return parsed
