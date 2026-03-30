from typing import Any, Dict, List, Optional

from llm_agents.analytics_agent import AnalyticsAgent
from llm_agents.base import BaseAgent
from llm_agents.documentation_agent import DocumentationAgent
from llm_agents.openai_guidance import OpenAIGuidancePlanner
from llm_agents.strategy_agent import StrategyAgent


class GuidanceAgent(BaseAgent):
    name = "guide"

    def __init__(
        self,
        strategy: Optional[StrategyAgent] = None,
        analytics: Optional[AnalyticsAgent] = None,
        documentation: Optional[DocumentationAgent] = None,
        planner: Optional[OpenAIGuidancePlanner] = None,
    ) -> None:
        self.strategy = strategy or StrategyAgent()
        self.analytics = analytics or AnalyticsAgent()
        self.documentation = documentation or DocumentationAgent()
        self.planner = planner or OpenAIGuidancePlanner()

    def _message_updates(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        lower_message = message.lower()

        if "whole facility" in lower_message:
            updates["whole_facility"] = True
            updates["retrofit_scope"] = "whole_facility"
        elif "single system" in lower_message or "single-system" in lower_message:
            updates["whole_facility"] = False
            updates["retrofit_scope"] = "single_system"
        elif "multiple systems" in lower_message:
            updates["whole_facility"] = False
            updates["retrofit_scope"] = "multiple_systems"

        if "simulation" in lower_message:
            updates["simulation_required"] = True

        if any(token in lower_message for token in ["submeter", "metering", "measurement isolation"]):
            updates["measurement_isolation"] = True
        elif "cannot isolate" in lower_message or "no isolation" in lower_message:
            updates["measurement_isolation"] = False

        if "stable" in lower_message and "parameter" in lower_message:
            updates["key_parameter_stable"] = True

        if "facility:" in lower_message:
            facility = message.split(":", 1)[1].strip()
            if facility:
                updates["facility"] = facility

        if "project name:" in lower_message:
            project_name = message.split(":", 1)[1].strip()
            if project_name:
                updates["project_name"] = project_name

        if "yes" == lower_message.strip() and context.get("last_question") == "measurement_isolation":
            updates["measurement_isolation"] = True
        if "no" == lower_message.strip() and context.get("last_question") == "measurement_isolation":
            updates["measurement_isolation"] = False

        return updates

    @staticmethod
    def _current_stage(context: Dict[str, Any]) -> str:
        if not context.get("strategy_output"):
            return "strategy"
        if not context.get("baseline_data") and not context.get("analytics_output"):
            return "analytics"
        if not context.get("analytics_output"):
            return "analytics"
        if not context.get("documentation_output"):
            return "documentation"
        return "complete"

    @staticmethod
    def _strategy_questions(context: Dict[str, Any]) -> List[str]:
        questions: List[str] = []
        if "retrofit_scope" not in context and not context.get("whole_facility"):
            questions.append("Is this a whole-facility, single-system, or multi-system project?")
        if "measurement_boundary" not in context:
            questions.append("What measurement boundary should we document for the project?")
        if "measurement_isolation" not in context and not context.get("whole_facility"):
            questions.append("Can the retrofit be isolated with dedicated metering or submetering?")
        return questions

    @staticmethod
    def _documentation_questions(context: Dict[str, Any]) -> List[str]:
        questions: List[str] = []
        if not context.get("project_name"):
            questions.append("What project name should appear in the final M&V summary?")
        if not context.get("facility"):
            questions.append("Which facility should the report reference?")
        return questions

    def _run_strategy(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        strategy_output = self.strategy.run(message, context)
        questions = self._strategy_questions(context)

        assistant_message = (
            f"Stage 1 is strategy. I recommend `{strategy_output['recommended_option']}` "
            f"with boundary `{strategy_output['measurement_boundary']}`."
        )
        if questions:
            assistant_message += " To firm that up, I still need a few details."
        else:
            assistant_message += " Strategy is ready, so we can move to baseline analytics next."

        return {
            "current_stage": "strategy",
            "next_stage": "analytics",
            "stage_status": "ready" if not questions else "needs_input",
            "assistant_message": assistant_message,
            "action_items": questions or [
                "Upload baseline data or load sample data in the Analytics step.",
                "Confirm the dependent variable and predictor columns for baseline modeling.",
            ],
            "strategy_output": strategy_output,
            "stage_result": strategy_output,
            "context_updates": {
                "strategy_output": strategy_output,
                "last_question": "measurement_isolation" if "measurement_isolation" not in context else "",
            },
        }

    def _run_analytics(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not context.get("baseline_data"):
            return {
                "current_stage": "analytics",
                "next_stage": "analytics",
                "stage_status": "needs_input",
                "assistant_message": (
                    "Stage 2 is analytics. I need baseline data before I can build the regression model."
                ),
                "action_items": [
                    "Upload or load baseline data in the Analytics step.",
                    "Include one dependent variable, such as energy, and one or more numeric drivers.",
                    "Optionally add post-period data if you want savings and uncertainty estimates.",
                ],
                "context_updates": {},
            }

        analytics_output = self.analytics.run(message, context)
        if "error" in analytics_output:
            return {
                "current_stage": "analytics",
                "next_stage": "analytics",
                "stage_status": "needs_input",
                "assistant_message": "I tried to run analytics, but the input data is incomplete.",
                "action_items": [analytics_output["error"]],
                "analytics_output": analytics_output,
                "stage_result": analytics_output,
                "context_updates": {},
            }

        assistant_message = (
            "Stage 2 is complete. "
            f"The baseline model achieved R2 {analytics_output['r2']:.3f} and "
            f"CV(RMSE) {analytics_output['cvrmse_percent']:.2f}%."
        )

        return {
            "current_stage": "analytics",
            "next_stage": "documentation",
            "stage_status": "ready",
            "assistant_message": assistant_message,
            "action_items": [
                "Review the QA/QC checks below.",
                "If the model looks acceptable, continue to documentation.",
            ],
            "analytics_output": analytics_output,
            "stage_result": analytics_output,
            "context_updates": {
                "analytics_output": analytics_output,
            },
        }

    def _run_documentation(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        questions = self._documentation_questions(context)
        documentation_output = self.documentation.run(message, context)

        assistant_message = "Stage 3 is documentation. I generated a draft M&V summary."
        if questions:
            assistant_message += " I can improve it once you provide the missing project details."
        else:
            assistant_message += " The workflow is complete and ready for review."

        return {
            "current_stage": "documentation",
            "next_stage": "complete",
            "stage_status": "ready" if not questions else "needs_input",
            "assistant_message": assistant_message,
            "action_items": questions or [
                "Review the draft summary and export it if it looks right.",
                "If project details change, rerun this stage to refresh the document.",
            ],
            "documentation_output": documentation_output,
            "stage_result": documentation_output,
            "context_updates": {
                "documentation_output": documentation_output,
            },
        }

    @staticmethod
    def _is_followup(message: str) -> bool:
        """Detect if a message is a follow-up/clarification about a previous result."""
        lower = message.lower().strip()
        followup_cues = [
            "why", "how come", "explain", "what do you mean", "tell me more",
            "can you clarify", "elaborate", "reason", "justify", "could you explain",
            "what is", "what are", "what does", "what's the difference",
            "i don't understand", "not sure", "confused",
            "that strategy", "that option", "that recommendation", "that plan",
        ]
        return any(cue in lower for cue in followup_cues)

    def _handle_followup(self, message: str, context: Dict[str, Any], stage: str) -> Optional[Dict[str, Any]]:
        """Use the LLM to answer follow-up questions about previous results."""
        if not self.planner.is_available():
            return None

        answer = self.planner.answer_followup(
            message=message,
            context=context,
            stage=stage,
        )
        if not answer:
            return None

        return {
            "current_stage": stage,
            "next_stage": stage,
            "stage_status": "needs_input",
            "assistant_message": answer,
            "action_items": [],
            "context_updates": {},
        }

    @staticmethod
    def _has_strategy_info(message: str) -> bool:
        """Detect if the user is providing strategy-relevant information."""
        lower = message.lower()
        cues = [
            "whole facility", "single system", "single-system", "multi",
            "cannot isolate", "can't isolate", "no isolation", "can be isolated",
            "not.*isolated", "submeter", "metering",
            "boundary", "option a", "option b", "option c", "option d",
            "chiller", "hvac", "lighting", "boiler", "retrofit",
            "upgrade", "facility", "building", "campus",
        ]
        return any(c in lower for c in cues)

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        working_context = dict(context)
        prev_stage = self._current_stage(working_context)
        context_updates = self._message_updates(message, working_context)
        if self.planner.is_available():
            llm_updates = self.planner.extract_context_updates(
                message=message,
                context=working_context,
                stage=prev_stage,
            )
            if llm_updates:
                context_updates.update(llm_updates)
        working_context.update(context_updates)

        stage = self._current_stage(working_context)

        # Handle follow-up / clarification questions about previous results
        # instead of blindly advancing to the next stage.
        if self._is_followup(message):
            followup_result = self._handle_followup(message, working_context, stage)
            if followup_result:
                followup_result["llm_guidance"] = self.planner.metadata()
                merged = dict(context_updates)
                merged.update(followup_result.get("context_updates", {}))
                followup_result["context_updates"] = merged
                return followup_result

        # If the user is answering strategy questions but stage already advanced,
        # re-run strategy with updated context so they get a proper acknowledgment.
        if (
            stage != "strategy"
            and prev_stage != "strategy"
            and self._has_strategy_info(message)
            and working_context.get("strategy_output")
        ):
            result = self._run_strategy(message, working_context)
            # Keep the stage at the actual next stage after strategy
            result["current_stage"] = stage
        elif stage == "strategy":
            result = self._run_strategy(message, working_context)
        elif stage == "analytics":
            result = self._run_analytics(message, working_context)
        elif stage == "documentation":
            result = self._run_documentation(message, working_context)
        else:
            result = {
                "current_stage": "complete",
                "next_stage": "complete",
                "stage_status": "ready",
                "assistant_message": "All three stages are complete. You can review the outputs or restart the workflow.",
                "action_items": [
                    "Review strategy, analytics, and documentation outputs.",
                    "Reset the workflow if you want to start a new project.",
                ],
                "context_updates": {},
            }

        # Let the LLM rewrite the response to be conversational.
        # Pass the user's message and any pending questions so the LLM
        # can acknowledge what the user said before giving next steps.
        if self.planner.is_available():
            prev_questions = context.get("_pending_questions", [])
            drafted = self.planner.draft_guidance(
                message=message,
                context=working_context,
                result=result,
                previous_questions=prev_questions,
            )
            if drafted.get("assistant_message"):
                result["assistant_message"] = drafted["assistant_message"]
            if drafted.get("action_items"):
                result["action_items"] = drafted["action_items"]

        # Store pending questions for the next turn's context.
        result.setdefault("context_updates", {})
        result["context_updates"]["_pending_questions"] = result.get("action_items", [])

        merged_updates = dict(context_updates)
        merged_updates.update(result.get("context_updates", {}))
        result["context_updates"] = merged_updates
        result["llm_guidance"] = self.planner.metadata()
        return result
