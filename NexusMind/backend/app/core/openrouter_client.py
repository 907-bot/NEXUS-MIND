"""
OpenRouter Client for NexusMind
Supports multiple free models with OpenAI-compatible API
"""
import json
import re
import asyncio
import random
import ssl
import time
from typing import Any, Optional

import aiohttp
from app.config import settings

# Fix Windows SSL certificate issues
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = None


def _retry_after_seconds(response: aiohttp.ClientResponse, attempt: int) -> float:
    """Honor Retry-After when present; otherwise exponential backoff capped at 60s."""
    ra = response.headers.get("Retry-After")
    if ra is not None:
        try:
            sec = float(ra)
            return min(max(sec, 0.5), 120.0)
        except ValueError:
            pass
    return float(min(2**attempt, 60))


def _looks_like_rate_limit_text(message: str) -> bool:
    lower = (message or "").lower()
    return any(
        key in lower
        for key in (
            "rate limit",
            "429",
            "too many requests",
            "throttl",
            "temporarily unavailable",
            "overloaded",
            "resource exhausted",
        )
    )


def _friendly_model_label(model_id: str) -> str:
    mid = (model_id or "").lower()
    if "qwen/qwen-2.5" in mid or "qwen-2.5" in mid:
        return "Qwen 2.5"
    if "qwen/qwen-3" in mid or "qwen-3" in mid:
        return "Qwen 3"
    if "llama-3.3-70b" in mid:
        return "Llama 3.3 70B"
    if "gemma-2" in mid:
        return "Gemma 2"
    if "gemma-3" in mid:
        return "Gemma 3"
    if "mistral-small" in mid:
        return "Mistral Small"
    if "llama-3-8b" in mid:
        return "Llama 3 8B"
    if "gemini-2.0-flash" in mid:
        return "Gemini 2.0 Flash"
    if "gpt-oss" in mid:
        return "GPT-OSS"
    if "openrouter/auto" in mid:
        return "Auto Router"
    if "/" in (model_id or ""):
        return model_id.split("/")[-1].replace(":free", "")
    return model_id or "model"


# Extra free models to try when the primary hits HTTP 429 or fails (diversify providers).
# These are verified working free models as of May 2026.
_JSON_MODEL_FALLBACKS: list[str] = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-32b:free",
    "google/gemma-3-12b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "openrouter/auto",  # Catch-all: OpenRouter picks best available model
]


class OpenRouterClient:
    """
    OpenRouter API client with same interface as GeminiClient.
    Supports model selection per-agent for cost optimization.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Per-agent model assignments (stable free models as of May 2026)
    AGENT_MODELS = {
        "PlannerAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "BackendAgent": "qwen/qwen3-32b:free",
        "FrontendAgent": "qwen/qwen3-32b:free",
        "DataAgent": "google/gemma-3-12b-it:free",
        "ResearchAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "DevOpsAgent": "qwen/qwen3-32b:free",
        "ContentAgent": "mistralai/mistral-small-3.1-24b-instruct:free",
        "CriticAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "AssemblerAgent": "meta-llama/llama-3.3-70b-instruct:free",
    }

    # Custom max_tokens for agents that produce large outputs
    AGENT_MAX_TOKENS = {
        "AssemblerAgent": 8192,
        "BackendAgent": 6144,
        "FrontendAgent": 6144,
        "ResearchAgent": 6144,
        "DataAgent": 6144,
        "PlannerAgent": 4096,  # Usually fine, but keep explicit
    }

    _JSON_MAX_ATTEMPTS = 12

    @staticmethod
    def friendly_model_label(model_id: str) -> str:
        return _friendly_model_label(model_id)

    def __init__(
        self,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize OpenRouter client.
        
        Args:
            agent_name: Name of the agent (to look up default model)
            model: Override model ID (if None, uses agent's default)
            temperature: Sampling temperature
            max_tokens: Max output tokens
        """
        self.api_key = settings.OPENROUTER_API_KEY
        self.agent_name = agent_name
        
        # Determine which model to use
        if model:
            self.model = model
        elif agent_name and agent_name in self.AGENT_MODELS:
            self.model = self.AGENT_MODELS[agent_name]
        else:
            # Fallback if no specific assignment
            self.model = "meta-llama/llama-3.3-70b-instruct:free"
        
        # Determine max_tokens
        if agent_name and agent_name in self.AGENT_MAX_TOKENS:
            self.max_tokens = self.AGENT_MAX_TOKENS[agent_name]
        else:
            self.max_tokens = max_tokens
        
        api_status = "✅ API Key Set" if self.api_key else "❌ No API Key"
        print(f"🔌 [OpenRouter] Client initialized for {agent_name or 'Unknown'}")
        print(f"     Model: {self.model}")
        print(f"     Status: {api_status}")
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Cost tracking (free models = $0, but track for consistency)
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        
        # Headers for OpenRouter
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexusmind.app",  # Required by OpenRouter
            "X-Title": "NexusMind",
        }
    
    def _record_usage(self, usage: dict) -> dict:
        """Record token usage from response."""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        # Free models = $0 cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": 0.0,  # Free models
        }
    
    def get_usage_summary(self) -> dict:
        """Return cumulative token usage."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd": 0.0,
            "model": self.model,
            "agent": self.agent_name,
        }
    
    async def generate(self, system_prompt: str, user_message: str, max_retries: int = 3) -> str:
        """Generate text response."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        for attempt in range(max_retries):
            try:
                connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT) if SSL_CONTEXT else None
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        if response.status == 429:
                            wait = 2 ** attempt
                            await asyncio.sleep(wait)
                            continue
                        
                        response.raise_for_status()
                        data = await response.json()
                        
                        # Record usage
                        usage = data.get("usage", {})
                        self._record_usage(usage)
                        
                        return data["choices"][0]["message"]["content"]
                        
            except aiohttp.ClientResponseError as e:
                if e.status == 429 and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"OpenRouter API error: {e}")
        
        raise RuntimeError("Max retries exceeded")

    def _json_model_candidates(self) -> list[str]:
        """Primary model first, then distinct free fallbacks for 429 rotation."""
        primary = self.model
        chain = [primary]
        for m in _JSON_MODEL_FALLBACKS:
            if m not in chain:
                chain.append(m)
        return chain

    async def _emit_backend_log_stream(
        self,
        memory: Any,
        session_id: str | None,
        message: str,
        **extra: Any,
    ) -> None:
        if not memory or not session_id:
            return
        try:
            await memory.publish_event(
                session_id,
                {
                    "agent": self.agent_name or "System",
                    "type": "BACKEND_LOG",
                    "timestamp": time.time(),
                    "data": {"message": message, **extra},
                },
            )
        except Exception:
            pass

    async def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        *,
        stream_session_id: str | None = None,
        stream_memory: Any = None,
    ) -> dict | list:
        """
        Generate JSON response using prompt-based extraction.

        NOTE: We intentionally do NOT use response_format={"type": "json_object"}
        because most free models on OpenRouter (Llama, Qwen, Gemma) do not support
        that parameter and return a 400/422 error. Instead we instruct the model
        in the prompt to reply with pure JSON and strip any markdown fences.

        Optional ``stream_session_id`` + ``stream_memory`` publish BACKEND_LOG
        events for live UI feedback (model assignment, rate-limit retries).
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        json_instruction = (
            "\n\nIMPORTANT: Your response MUST be valid JSON only. "
            "Do NOT include any text, explanation, or markdown fences outside the JSON. "
            "Output ONLY the raw JSON object or array."
        )

        messages = [
            {"role": "system", "content": system_prompt + json_instruction},
            {"role": "user", "content": user_message},
        ]

        original_model = self.model
        candidates = self._json_model_candidates()
        max_attempts = self._JSON_MAX_ATTEMPTS
        model_idx = 0

        try:
            self.model = candidates[0]

            for attempt in range(max_attempts):
                self.model = candidates[model_idx % len(candidates)]
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }
                try:
                    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT) if SSL_CONTEXT else None
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.post(
                            f"{self.BASE_URL}/chat/completions",
                            headers=self.headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=120),
                        ) as response:
                            if response.status == 429:
                                wait = _retry_after_seconds(
                                    response, attempt // max(1, len(candidates))
                                )
                                next_idx = (model_idx + 1) % len(candidates)
                                next_model = candidates[next_idx]
                                model_idx = next_idx
                                await asyncio.sleep(wait)
                                continue

                            if response.status >= 400:
                                error_text = await response.text()
                                # If 400 Bad Request or 404 Not Found, the model ID is likely invalid or gone.
                                if response.status in (400, 404):
                                    # Log as info/debug instead of error to avoid red lines in UI logs
                                    print(f"ℹ️ [OpenRouter] Skipping unavailable model {self.model} (HTTP {response.status})")
                                    if self.model in candidates:
                                        candidates.remove(self.model)
                                        if model_idx >= len(candidates):
                                            model_idx = 0
                                    await asyncio.sleep(0.1)
                                    if not candidates:
                                        raise RuntimeError("All available models failed with 400/404.")
                                    continue
                                
                                # For other errors (429, 500), print a warning and retry
                                print(f"⚠️ [OpenRouter] HTTP {response.status} using model {self.model}: {error_text}")
                                if attempt < max_attempts - 1:
                                    model_idx = (model_idx + 1) % len(candidates)
                                    await asyncio.sleep(float(min(2 ** (attempt % 6), 60)))
                                    continue
                                else:
                                    response.raise_for_status()
                                    
                            data = await response.json()

                            if "error" in data:
                                err_info = data.get("error", {})
                                err_msg = err_info.get("message", "Unknown error") or ""
                                if _looks_like_rate_limit_text(err_msg):
                                    wait = float(
                                        min(2 ** min(attempt // 2, 6), 90)
                                    )
                                    next_idx = (model_idx + 1) % len(candidates)
                                    next_model = candidates[next_idx]
                                    model_idx = next_idx
                                    await asyncio.sleep(wait)
                                    continue
                                print(f"⚠️ [OpenRouter] API Error: {err_msg}")
                                await asyncio.sleep(
                                    float(min(2 ** ((attempt % 3) + 1), 60))
                                )
                                continue

                            if "choices" not in data or not data["choices"]:
                                print(f"⚠️ [OpenRouter] No choices returned: {data}")
                                await asyncio.sleep(
                                    float(min(2 ** ((attempt % 3) + 1), 60))
                                )
                                continue

                            usage = data.get("usage", {})
                            self._record_usage(usage)

                            raw_content = data["choices"][0]["message"]["content"]
                            text = raw_content

                            # Any ```lang ... ``` fence (models often use ```bash, ```text, etc.)
                            fence_match = re.search(
                                r"```[\w+-]*\s*(.*?)```", text, re.DOTALL
                            )
                            if fence_match:
                                text = fence_match.group(1).strip()
                            else:
                                text = text.strip().strip("`").strip()

                            # ANY text before or after the JSON block is preserved as "TOON" narrative
                            full_raw_text = text
                            
                            start_idx = -1
                            for i, char in enumerate(text):
                                if char in ("{", "["):
                                    start_idx = i
                                    break

                            parsed_json = None
                            if start_idx != -1:
                                end_char = "}" if text[start_idx] == "{" else "]"
                                end_idx = text.rfind(end_char)
                                if end_idx != -1:
                                    json_text = text[start_idx : end_idx + 1]
                                    try:
                                        parsed_json = json.loads(json_text)
                                    except json.JSONDecodeError:
                                        # Try cleanup
                                        repaired = self._repair_json(json_text)
                                        try:
                                            parsed_json = json.loads(repaired)
                                        except:
                                            pass

                            if parsed_json is not None:
                                if isinstance(parsed_json, dict):
                                    # Add the full narrative context for "TOON" support
                                    parsed_json["_toon_narrative"] = full_raw_text
                                return parsed_json
                            
                            # If no valid JSON found but text exists, return it as a narrative
                            if text.strip():
                                return {"_toon_narrative": text, "summary": "Generated narrative (no JSON metadata found)"}

                            print(
                                f"⚠️ [OpenRouter] No JSON object/array in response; retrying. Preview: {(raw_content or '')[:100]}"
                            )
                            model_idx = (model_idx + 1) % len(candidates)
                            await asyncio.sleep(float(min(2 + (attempt % 4), 12)))
                            continue

                except json.JSONDecodeError as e:
                    preview = (text if isinstance(text, str) else "").replace("\n", " ").strip()
                    if len(preview) > 320:
                        preview = preview[:320] + "…"
                    print(f"⚠️ [OpenRouter] JSON parse failed on attempt {attempt+1}: {e}")
                    print(f"📄 RAW TEXT (Attempt {attempt+1}):\n{text}\n")
                    if attempt >= max_attempts - 1:
                        snippet = text[:100] + "..." if len(text) > 100 else text
                        raise RuntimeError(
                            f"JSON generation failed after {max_attempts} attempts. Raw snippet: {snippet}. Error: {e}"
                        )
                    await asyncio.sleep(2)
                except aiohttp.ClientResponseError as e:
                    print(
                        f"⚠️ [OpenRouter] HTTP {e.status} on attempt {attempt+1}: {e.message}"
                    )
                    if e.status in (400, 429) and attempt < max_attempts - 1:
                        model_idx = (model_idx + 1) % len(candidates)
                        await asyncio.sleep(float(min(2 ** (attempt % 6), 60)))
                        continue
                    raise RuntimeError(
                        f"OpenRouter API error {e.status}: {e.message}"
                    )
                except Exception as e:
                    if _looks_like_rate_limit_text(str(e)) and attempt < max_attempts - 1:
                        model_idx = (model_idx + 1) % len(candidates)
                        await asyncio.sleep(float(min(2 ** (attempt % 6), 60)))
                        continue
                    raise RuntimeError(f"OpenRouter JSON generation failed: {e}")

            raise RuntimeError(
                f"OpenRouter failed after {max_attempts} attempts (often HTTP 429 on free models). "
                "Try again in a few minutes, add OpenRouter credits, or use a paid model id."
            )
        finally:
            self.model = original_model

    def _repair_json(self, json_str: str) -> str:
        """
        Attempts to repair a truncated JSON string by closing open strings,
        objects, and arrays.
        """
        json_str = json_str.strip()
        if not json_str:
            return json_str

        # 1. Handle unterminated strings
        # We look for an odd number of unescaped quotes
        in_string = False
        escaped = False
        for char in json_str:
            if char == '"' and not escaped:
                in_string = not in_string
            if char == '\\' and not escaped:
                escaped = True
            else:
                escaped = False
        
        if in_string:
            # Check if it ended with an unescaped backslash
            if json_str.endswith('\\') and not json_str.endswith('\\\\'):
                json_str = json_str[:-1]
            json_str += '"'

        # 2. Handle missing closing braces/brackets
        stack = []
        in_string = False
        escaped = False
        
        # We need to re-scan because we might have added a quote
        for char in json_str:
            if char == '"' and not escaped:
                in_string = not in_string
            if not in_string:
                if char == '{':
                    stack.append('}')
                elif char == '[':
                    stack.append(']')
                elif char == '}' or char == ']':
                    if stack and stack[-1] == char:
                        stack.pop()
            
            if char == '\\' and not escaped:
                escaped = True
            else:
                escaped = False

        # Close everything in reverse order
        while stack:
            json_str += stack.pop()
            
        return json_str

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tool_definitions: list[dict],
        max_rounds: int = 5,
    ) -> tuple[str, list[dict]]:
        """
        Generate with tool calling support.
        OpenRouter supports OpenAI-style function calling.
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        # Convert tool definitions to OpenAI format
        tools = []
        handler_map = {}
        for td in tool_definitions:
            tool = {
                "type": "function",
                "function": {
                    "name": td["name"],
                    "description": td["description"],
                    "parameters": {
                        "type": "object",
                        "properties": td.get("input_schema", {}),
                        "required": list(td.get("input_schema", {}).keys()),
                    },
                },
            }
            tools.append(tool)
            handler_map[td["name"]] = td.get("handler")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        tool_call_log = []
        
        for _ in range(max_rounds):
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "tools": tools if tools else None,
            }
            
            try:
                connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT) if SSL_CONTEXT else None
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
                        # Record usage
                        usage = data.get("usage", {})
                        self._record_usage(usage)
                        
                        message = data["choices"][0]["message"]
                        
                        # Check for tool calls
                        tool_calls = message.get("tool_calls", [])
                        
                        if not tool_calls:
                            # No tool calls, return final text
                            return message.get("content", ""), tool_call_log
                        
                        # Execute tool calls
                        messages.append({
                            "role": "assistant",
                            "content": message.get("content", ""),
                            "tool_calls": tool_calls,
                        })
                        
                        for tc in tool_calls:
                            if tc["type"] == "function":
                                func = tc["function"]
                                tool_name = func["name"]
                                tool_args = json.loads(func["arguments"])
                                
                                handler = handler_map.get(tool_name)
                                if handler:
                                    try:
                                        result = await handler(**tool_args)
                                    except Exception as e:
                                        result = {"error": str(e)}
                                else:
                                    result = {"error": f"Tool '{tool_name}' not found"}
                                
                                tool_call_log.append({
                                    "tool": tool_name,
                                    "args": tool_args,
                                    "result": result,
                                })
                                
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc["id"],
                                    "content": json.dumps(result) if not isinstance(result, str) else result,
                                })
                        
            except Exception as e:
                return f"Error during tool execution: {e}", tool_call_log
        
        # Max rounds reached, return last response
        return "Max tool rounds reached", tool_call_log


# Factory function for creating clients
def create_llm_client(agent_name: str, **kwargs):
    """
    Factory to create appropriate LLM client for an agent.
    ALL agents use OpenRouter free models (Gemini direct API is not used).
    PlannerAgent uses google/gemini-2.0-flash-exp:free via OpenRouter.
    """
    if settings.OPENROUTER_API_KEY:
        return OpenRouterClient(agent_name=agent_name, **kwargs)
    
    # Hard error — no OpenRouter key means nothing will work
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set. All agents require OpenRouter. "
        "Set this environment variable in your Render dashboard."
    )
