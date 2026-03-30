import json
import os
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience only
    load_dotenv = None


class OpenAIGuidancePlanner:
    """Optional OpenAI-backed helper for interpreting user replies and drafting guidance."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        if load_dotenv is not None:
            load_dotenv()

        # On Streamlit Cloud, secrets are exposed via st.secrets, not env vars.
        st_api_key = None
        st_model = None
        try:
            import streamlit as st

            st_api_key = st.secrets.get("OPENAI_API_KEY")
            st_model = st.secrets.get("OPENAI_MODEL")
        except Exception:
            pass

        self.api_key = api_key or st_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or st_model or os.getenv("OPENAI_MODEL", "gpt-5.4")

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            from openai import OpenAI  # noqa: F401
        except ImportError:
            return False
        return True

    def metadata(self) -> Dict[str, Any]:
        return {
            "provider": "openai",
            "model": self.model,
            "enabled": self.is_available(),
        }

    def _client(self):
        from openai import OpenAI

        return OpenAI(api_key=self.api_key)

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and start < end:
                return json.loads(text[start : end + 1])
        return {}

    def _json_response(self, prompt: str) -> Dict[str, Any]:
        if not self.is_available():
            return {}

        try:
            response = self._client().responses.create(
                model=self.model,
                input=prompt,
            )
            output_text = getattr(response, "output_text", "")
            return self._parse_json(output_text)
        except Exception:
            return {}

    def extract_context_updates(
        self,
        message: str,
        context: Dict[str, Any],
        stage: str,
    ) -> Dict[str, Any]:
        prompt = (
            "You are extracting structured workflow state for an industrial M&V assistant.\n"
            "Return JSON only with this shape:\n"
            "{\n"
            '  "context_updates": {\n'
            '    "whole_facility": true|false,\n'
            '    "retrofit_scope": "whole_facility"|"single_system"|"multiple_systems",\n'
            '    "measurement_boundary": "string",\n'
            '    "measurement_isolation": true|false,\n'
            '    "key_parameter_stable": true|false,\n'
            '    "simulation_required": true|false,\n'
            '    "project_name": "string",\n'
            '    "facility": "string"\n'
            "  }\n"
            "}\n"
            "Only include fields that are strongly supported by the user message.\n"
            f"Current stage: {stage}\n"
            f"Current context: {json.dumps(context, default=str)}\n"
            f"Latest user message: {message}\n"
        )
        parsed = self._json_response(prompt)
        updates = parsed.get("context_updates", {})
        return updates if isinstance(updates, dict) else {}

    def draft_guidance(
        self,
        message: str,
        context: Dict[str, Any],
        result: Dict[str, Any],
        previous_questions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        prev_q_text = ""
        if previous_questions:
            prev_q_text = (
                "\nThe assistant previously asked the user these questions:\n"
                + "\n".join(f"- {q}" for q in previous_questions)
                + "\nThe user's latest message may be answering some or all of them.\n"
            )

        prompt = (
            "You are a friendly, expert M&V workflow assistant having a conversation "
            "with an energy engineer. You must respond CONVERSATIONALLY.\n\n"
            "CRITICAL RULES:\n"
            "1. ALWAYS acknowledge what the user just said before giving next steps.\n"
            "   Example: 'Got it — whole-facility scope with no isolation. "
            "That confirms Option C is the right fit. Next, ...'\n"
            "2. Reference specific details from the user's message in your response.\n"
            "3. Do NOT start with 'Stage N is ...' — speak naturally.\n"
            "4. Connect the user's input to the recommendation or next action.\n"
            "5. Keep it concise (2-4 sentences for the message).\n"
            "6. Action items should be specific next steps, not generic instructions.\n\n"
            "Return JSON only:\n"
            "{\n"
            '  "assistant_message": "your conversational response",\n'
            '  "action_items": ["specific next step"]\n'
            "}\n"
            f"{prev_q_text}"
            f"Workflow context: {json.dumps(context, default=str)}\n"
            f"Latest user message: {message}\n"
            f"Current result: {json.dumps(result, default=str)}\n"
        )
        parsed = self._json_response(prompt)
        assistant_message = parsed.get("assistant_message")
        action_items = parsed.get("action_items")
        output: Dict[str, Any] = {}
        if isinstance(assistant_message, str) and assistant_message.strip():
            output["assistant_message"] = assistant_message.strip()
        if isinstance(action_items, list):
            output["action_items"] = [
                str(item).strip() for item in action_items if str(item).strip()
            ]
        return output

    def answer_followup(
        self,
        message: str,
        context: Dict[str, Any],
        stage: str,
    ) -> Optional[str]:
        """Answer a follow-up or clarification question about previous results."""
        if not self.is_available():
            return None

        prompt = (
            "You are an expert M&V (Measurement and Verification) workflow assistant.\n"
            "The user is asking a follow-up or clarification question about a previous "
            "recommendation or result. Answer their question directly and helpfully.\n\n"
            "Rules:\n"
            "- Answer the specific question the user asked.\n"
            "- Reference the strategy, analytics, or documentation results from context.\n"
            "- If they ask 'why' about a strategy recommendation, explain the IPMVP logic.\n"
            "- Keep the answer concise (2-4 sentences).\n"
            "- Do NOT just repeat the next workflow stage instructions.\n"
            "- Do NOT ignore the question to push the workflow forward.\n\n"
            f"Current stage: {stage}\n"
            f"Workflow context: {json.dumps(context, default=str)}\n"
            f"User question: {message}\n\n"
            "Respond with plain text (not JSON)."
        )
        try:
            response = self._client().responses.create(
                model=self.model,
                input=prompt,
            )
            text = getattr(response, "output_text", "").strip()
            return text if text else None
        except Exception:
            return None
