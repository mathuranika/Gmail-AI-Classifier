import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()


class BedrockClassifier:
    def __init__(self):
        region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "us-east-1"
        )

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region
        )

        self.model_id = os.getenv("BEDROCK_MODEL_ID")
        if not self.model_id:
            raise RuntimeError("BEDROCK_MODEL_ID is not set")

    def classify_email(self, email_text: str) -> dict:
        prompt = f"""
You are a strict JSON-only email classification engine.

Rules:
- Output ONLY valid JSON
- No markdown
- No explanations
- One JSON object only

Email:
\"\"\"{email_text}\"\"\"

Return exactly:
{{
  "category": "urgent | important | promotional | skip",
  "urgency_reason": "short reason",
  "needs_reply": true or false,
  "suggested_action": "short actionable instruction"
}}
"""

        body = body = {
    "prompt": prompt,
    "max_gen_len": 200,
    "temperature": 0.0,
    "top_p": 0.9
}


        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        payload = json.loads(response["body"].read())

        try:
            text = payload["output"]["message"]["content"][0]["text"]
            parsed = json.loads(text)
        except Exception:
            return {
                "category": "skip",
                "urgency_reason": "invalid model output",
                "needs_reply": False,
                "suggested_action": "ignore"
            }

        parsed["needs_reply"] = bool(parsed.get("needs_reply"))
        return parsed
