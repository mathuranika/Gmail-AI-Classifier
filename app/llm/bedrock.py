import boto3
import json
import os
import re
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
        def _invoke(prompt: str) -> str:
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

            return json.loads(response["body"].read())["generation"]

        base_prompt = f"""
You are a JSON-only email classification engine.

Rules:
- Output ONLY valid JSON
- No markdown
- No backticks
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

        # ---- Attempt 1 ----
        try:
            raw = _invoke(base_prompt).strip()
        except Exception:
            raw = ""

        # ---- Attempt 2 (fallback) ----
        if not raw or raw.startswith("```") or "{" not in raw:
            fallback_prompt = f"""
Return ONLY valid JSON.
No text.
No markdown.

Email:
\"\"\"{email_text}\"\"\"

JSON:
"""
            try:
                raw = _invoke(fallback_prompt).strip()
            except Exception:
                raw = ""

        # ---- Clean output ----
        cleaned = raw.strip()
        cleaned = re.sub(r"```[a-zA-Z]*", "", cleaned)
        cleaned = cleaned.replace("```", "").strip()

        match = re.search(r"\{[\s\S]*?\}", cleaned)

        if not match:
            return {
                "category": "skip",
                "urgency_reason": "model returned invalid output",
                "needs_reply": False,
                "suggested_action": "ignore"
            }

        try:
            parsed = json.loads(match.group())
        except Exception:
            return {
                "category": "skip",
                "urgency_reason": "json parse failure",
                "needs_reply": False,
                "suggested_action": "ignore"
            }

        parsed["needs_reply"] = bool(parsed.get("needs_reply"))
        return parsed
