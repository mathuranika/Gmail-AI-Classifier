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
        """
        Classifies an email thread using AWS Bedrock (LLaMA).
        Fully hardened against markdown, empty output, and JSON failures.
        Never raises on bad model output.
        """

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

        # ---------------- BASE PROMPT ----------------
        base_prompt = f"""
You are a JSON-only email classification engine.

STRICT RULES:
- Output ONLY valid JSON
- NO explanations
- NO markdown
- NO backticks
- NO repetition
- ONE JSON object only

Email:
\"\"\"{email_text}\"\"\"

Return exactly this schema:
{{
  "category": "urgent | important | promotional | skip",
  "urgency_reason": "short reason",
  "needs_reply": true or false,
  "suggested_action": "short actionable instruction"
}}
"""

        # ---------------- ATTEMPT 1 ----------------
        try:
            raw = _invoke(base_prompt).strip()
        except Exception:
            raw = ""

        # ---------------- ATTEMPT 2 (HARD FALLBACK) ----------------
        if not raw or raw.startswith("```") or "{" not in raw:
            fallback_prompt = f"""
Return ONLY valid JSON.
No markdown.
No backticks.
No text.

Email:
\"\"\"{email_text}\"\"\"

JSON:
"""
            try:
                raw = _invoke(fallback_prompt).strip()
            except Exception:
                raw = ""

        # ---------------- CLEAN OUTPUT ----------------
        cleaned = raw.strip()

        # Remove any accidental markdown fences
        cleaned = re.sub(r"```[a-zA-Z]*", "", cleaned)
        cleaned = cleaned.replace("```", "").strip()

        # ---------------- PARSE JSON ----------------
        match = re.search(r"\{[\s\S]*?\}", cleaned)

        if not match:
            # Absolute safe fallback — NEVER crash pipeline
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

        # ---------------- TYPE SAFETY ----------------
        parsed["needs_reply"] = bool(parsed.get("needs_reply"))

        return parsed
