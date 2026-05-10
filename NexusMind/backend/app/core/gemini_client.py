import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, FunctionDeclaration, Tool
from app.config import settings
import json
import re
import asyncio

genai.configure(api_key=settings.GEMINI_API_KEY)

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


class GeminiClient:
    def __init__(self, temperature: float = 0.7, max_tokens: int = 4096):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            safety_settings=SAFETY_SETTINGS,
        )
        self.config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        # Separate config for JSON mode — forces the model to return valid JSON
        # natively (SKILL.md §9.1: response_mime_type="application/json")
        self.json_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )

        # ── Per-request cost tracking (SKILL.md §17) ─────────────────────────
        # Gemini 1.5 Flash pricing (as of mid-2024):
        #   Input:  $0.075 per 1M tokens (≤128k context)
        #   Output: $0.30  per 1M tokens (≤128k context)
        self._total_input_tokens:  int   = 0
        self._total_output_tokens: int   = 0
        self._total_cost_usd:      float = 0.0
        self._INPUT_COST_PER_TOKEN  = 0.075 / 1_000_000
        self._OUTPUT_COST_PER_TOKEN = 0.30  / 1_000_000

    # ── Cost accounting ───────────────────────────────────────────────────────

    def _record_usage(self, response) -> dict:
        """Extract token counts from the Gemini response and update running totals."""
        usage = getattr(response, "usage_metadata", None)
        input_tokens  = getattr(usage, "prompt_token_count",     0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        cost = (
            input_tokens  * self._INPUT_COST_PER_TOKEN
            + output_tokens * self._OUTPUT_COST_PER_TOKEN
        )
        self._total_input_tokens  += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost_usd      += cost
        return {
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "cost_usd":      round(cost, 6),
        }

    def get_usage_summary(self) -> dict:
        """Return cumulative token usage and cost for this client instance."""
        return {
            "total_input_tokens":  self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens":        self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd":      round(self._total_cost_usd, 6),
        }

    # ── Basic text generation ─────────────────────────────────────────────────

    async def generate(self, system_prompt: str, user_message: str, max_retries: int = 3) -> str:
        """Generate a text response with exponential-backoff retry."""
        full_prompt = f"{system_prompt}\n\n{user_message}"

        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        contents=full_prompt,
                        generation_config=self.config,
                    ),
                )
                self._record_usage(response)
                return response.text
            except Exception as exc:
                if "ResourceExhausted" in type(exc).__name__ or "429" in str(exc):
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError("Gemini rate limit exceeded after retries")

    async def generate_json(self, system_prompt: str, user_message: str) -> dict | list:
        """
        Generate a structured JSON response using Gemini's native JSON mode
        (response_mime_type='application/json') for maximum reliability.
        Falls back to regex-strip parsing if the mime-type config is unsupported.
        """
        full_prompt = f"{system_prompt}\n\n{user_message}"
        loop = asyncio.get_event_loop()

        for attempt in range(3):
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        contents=full_prompt,
                        generation_config=self.json_config,   # ← native JSON mode
                    ),
                )
                self._record_usage(response)
                text = response.text
                text = re.sub(r"```json|```", "", text).strip()
                return json.loads(text)
            except json.JSONDecodeError:
                # Native JSON mode should prevent this, but handle gracefully
                if attempt == 2:
                    raise
            except Exception as exc:
                if "ResourceExhausted" in type(exc).__name__ or "429" in str(exc):
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        raise RuntimeError("JSON generation failed after retries")

    # ── Native Gemini Function Calling ────────────────────────────────────────

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tool_definitions: list[dict],
        max_rounds: int = 5,
    ) -> tuple[str, list[dict]]:
        """
        Call Gemini with native function-calling support.

        Runs a multi-round loop where Gemini can request tool calls and receive
        results until it produces a final text response.

        Args:
            system_prompt:    System instruction for the model.
            user_message:     The user/task message.
            tool_definitions: List of tool dicts with keys:
                              name, description, input_schema (JSON-schema dict),
                              handler (async callable).
            max_rounds:       Maximum tool-call rounds before forcing a text response.

        Returns:
            (final_text, tool_call_log)
            tool_call_log is a list of {"tool": name, "args": dict, "result": any}
        """
        # Build Gemini FunctionDeclaration objects from our tool definitions
        gemini_tools = []
        handler_map: dict[str, any] = {}
        for td in tool_definitions:
            gemini_tools.append(
                FunctionDeclaration(
                    name=td["name"],
                    description=td["description"],
                    parameters={
                        "type": "object",
                        "properties": {
                            k: {"type": v.get("type", "string"), "description": v.get("description", "")}
                            for k, v in td.get("input_schema", {}).items()
                        },
                        "required": list(td.get("input_schema", {}).keys()),
                    },
                )
            )
            handler_map[td["name"]] = td["handler"]

        tool_call_log: list[dict] = []
        model_with_tools = genai.GenerativeModel(
            "gemini-1.5-flash",
            safety_settings=SAFETY_SETTINGS,
            tools=[Tool(function_declarations=gemini_tools)],
        )
        chat = model_with_tools.start_chat()
        full_prompt = f"{system_prompt}\n\n{user_message}"

        loop = asyncio.get_event_loop()

        for _ in range(max_rounds):
            # Send message to Gemini
            response = await loop.run_in_executor(
                None,
                lambda: chat.send_message(
                    full_prompt,
                    generation_config=self.config,
                ),
            )

            # Check if Gemini wants to call a function
            function_calls_in_response = []
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call.name:
                        function_calls_in_response.append(part.function_call)

            if not function_calls_in_response:
                # No more tool calls — return the final text
                return response.text, tool_call_log

            # Execute all requested tool calls
            tool_results = []
            for fc in function_calls_in_response:
                tool_name = fc.name
                tool_args = dict(fc.args)
                handler = handler_map.get(tool_name)

                if handler:
                    try:
                        result = await handler(**tool_args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": f"Tool '{tool_name}' not found"}

                tool_call_log.append({"tool": tool_name, "args": tool_args, "result": result})
                tool_results.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=tool_name,
                            response={"result": json.dumps(result) if not isinstance(result, str) else result},
                        )
                    )
                )

            # Feed results back into the chat
            full_prompt = tool_results  # type: ignore

        # Fallback — force a plain text response
        fallback = await loop.run_in_executor(
            None,
            lambda: chat.send_message(
                "Please summarize what you found so far in plain text.",
                generation_config=self.config,
            ),
        )
        return fallback.text, tool_call_log


# Singleton
gemini = GeminiClient()
