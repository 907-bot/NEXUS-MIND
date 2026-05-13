"""
OpenRouter Client for NexusMind
Supports multiple free models with OpenAI-compatible API
"""
import os
import json
import re
import asyncio
import random
import ssl
from typing import Optional
import aiohttp
from app.config import settings

# Fix Windows SSL certificate issues
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = None


# #region agent log
def _agent_debug_log(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict,
    run_id: str = "pre-fix",
) -> None:
    """Append one NDJSON line to workspace debug log (session 1e3d2e). Never log secrets."""
    try:
        import time

        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
        )
        log_path = os.path.join(root, "debug-1e3d2e.log")
        payload = {
            "sessionId": "1e3d2e",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass


# #endregion


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


def _agent_stdout_evidence(payload: dict) -> None:
    """One-line JSON for platform logs (e.g. Render) — no secrets."""
    try:
        print(f"[nexusmind-agent] {json.dumps(payload, default=str)}", flush=True)
    except Exception:
        pass


class OpenRouterClient:
    """
    OpenRouter API client with same interface as GeminiClient.
    Supports model selection per-agent for cost optimization.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Per-agent model assignments (free models)
    AGENT_MODELS = {
        "PlannerAgent": "qwen/qwen3-coder:free", # Back to high-precision Qwen for planning
        "BackendAgent": "qwen/qwen3-coder:free",
        "FrontendAgent": "qwen/qwen3-coder:free",
        
        # Tier 3: Long context / Data analysis (Gemma 4)
        "DataAgent": "google/gemma-4-31b-it:free",
        
        # Tier 4: General purpose (Llama 3.3 70B)
        "ResearchAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "DevOpsAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "ContentAgent": "meta-llama/llama-3.3-70b-instruct:free",
        
        # Tier 5: Reasoning / QA (GPT-OSS 120B)
        "CriticAgent": "openai/gpt-oss-120b:free",
        
        # Tier 6: Complex aggregation (Qwen 3 Coder)
        "AssemblerAgent": "qwen/qwen3-coder:free",
    }

    # On HTTP 429, try an alternate free model once before backoff (spreads load across providers).
    AGENT_FALLBACK_MODELS = {
        "PlannerAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "BackendAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "FrontendAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "AssemblerAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "DataAgent": "meta-llama/llama-3.3-70b-instruct:free",
        "ResearchAgent": "qwen/qwen3-coder:free",
        "DevOpsAgent": "qwen/qwen3-coder:free",
        "ContentAgent": "qwen/qwen3-coder:free",
        "CriticAgent": "meta-llama/llama-3.3-70b-instruct:free",
    }
    
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
            # Fallback to Llama 70B if no specific assignment
            self.model = "meta-llama/llama-3.3-70b-instruct:free"
        
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
    
    async def generate_json(self, system_prompt: str, user_message: str) -> dict | list:
        """
        Generate JSON response using prompt-based extraction.
        
        NOTE: We intentionally do NOT use response_format={"type": "json_object"}
        because most free models on OpenRouter (Llama, Qwen, Gemma) do not support
        that parameter and return a 400/422 error. Instead we instruct the model
        in the prompt to reply with pure JSON and strip any markdown fences.
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        # #region agent log
        _agent_debug_log(
            "H5",
            "openrouter_client.py:generate_json:entry",
            "generate_json started",
            {
                "model": self.model,
                "agent_name": self.agent_name,
                "api_key_configured": bool(self.api_key),
            },
        )
        # #endregion
        
        # Append explicit JSON instruction to ensure model outputs raw JSON
        json_instruction = (
            "\n\nIMPORTANT: Your response MUST be valid JSON only. "
            "Do NOT include any text, explanation, or markdown fences outside the JSON. "
            "Output ONLY the raw JSON object or array."
        )
        
        messages = [
            {"role": "system", "content": system_prompt + json_instruction},
            {"role": "user", "content": user_message},
        ]
        
        # No response_format — not supported by most free models
        original_model = self.model
        fallback_used = False

        # Add a small random jitter to avoid clashing with other agents' requests
        await asyncio.sleep(random.uniform(1.0, 3.0))

        try:
            for attempt in range(3):
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }
                try:
                    # #region agent log
                    _agent_debug_log(
                        "H1-H4",
                        "openrouter_client.py:generate_json:attempt",
                        "attempt begin",
                        {"attempt": attempt, "model": self.model},
                        run_id="post-fix",
                    )
                    # #endregion
                    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT) if SSL_CONTEXT else None
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.post(
                            f"{self.BASE_URL}/chat/completions",
                            headers=self.headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=120),
                        ) as response:
                            # #region agent log
                            _agent_debug_log(
                                "H1-H4",
                                "openrouter_client.py:generate_json:http_status",
                                "response status",
                                {"attempt": attempt, "http_status": response.status},
                                run_id="post-fix",
                            )
                            # #endregion
                            if response.status == 429:
                                fb = self.AGENT_FALLBACK_MODELS.get(self.agent_name or "")
                                if (
                                    fb
                                    and self.model != fb
                                    and not fallback_used
                                    and self.model == original_model
                                ):
                                    fallback_used = True
                                    # #region agent log
                                    _agent_debug_log(
                                        "H1",
                                        "openrouter_client.py:generate_json:branch",
                                        "429 switch fallback model",
                                        {
                                            "attempt": attempt,
                                            "from_model": original_model,
                                            "to_model": fb,
                                        },
                                        run_id="post-fix",
                                    )
                                    # #endregion
                                    _agent_stdout_evidence(
                                        {
                                            "event": "openrouter_429_fallback",
                                            "attempt": attempt,
                                            "from_model": original_model,
                                            "to_model": fb,
                                        }
                                    )
                                    self.model = fb
                                    continue
                                wait = _retry_after_seconds(response, attempt)
                                # #region agent log
                                _agent_debug_log(
                                    "H1",
                                    "openrouter_client.py:generate_json:branch",
                                    "429 backoff",
                                    {
                                        "attempt": attempt,
                                        "sleep_sec": wait,
                                        "retry_after_hdr": response.headers.get(
                                            "Retry-After"
                                        ),
                                    },
                                    run_id="post-fix",
                                )
                                # #endregion
                                _agent_stdout_evidence(
                                    {
                                        "event": "openrouter_429_backoff",
                                        "attempt": attempt,
                                        "sleep_sec": wait,
                                    }
                                )
                                await asyncio.sleep(wait)
                                continue

                            response.raise_for_status()
                            data = await response.json()

                            # Handle OpenRouter error responses (sometimes sent with 200 OK)
                            if "error" in data:
                                err_info = data.get("error", {})
                                err_msg = err_info.get("message", "Unknown error")
                                err_type = err_info.get("type") or err_info.get("code")
                                # #region agent log
                                _agent_debug_log(
                                    "H2",
                                    "openrouter_client.py:generate_json:branch",
                                    "body error object",
                                    {
                                        "attempt": attempt,
                                        "err_type": err_type,
                                        "err_msg_snippet": (err_msg or "")[:300],
                                    },
                                    run_id="post-fix",
                                )
                                # #endregion
                                print(f"⚠️ [OpenRouter] API Error: {err_msg}")
                                await asyncio.sleep(2 ** (attempt + 1))
                                continue

                            if "choices" not in data or not data["choices"]:
                                # #region agent log
                                _agent_debug_log(
                                    "H3",
                                    "openrouter_client.py:generate_json:branch",
                                    "missing or empty choices",
                                    {
                                        "attempt": attempt,
                                        "top_keys": list(data.keys())[:20],
                                    },
                                    run_id="post-fix",
                                )
                                # #endregion
                                print(f"⚠️ [OpenRouter] No choices returned: {data}")
                                await asyncio.sleep(2 ** (attempt + 1))
                                continue

                            # Record usage
                            usage = data.get("usage", {})
                            self._record_usage(usage)

                            text = data["choices"][0]["message"]["content"]

                            # Strip markdown code fences (```json ... ``` or ``` ... ```)
                            # We use a non-greedy match to find the content between fences if they exist
                            fence_match = re.search(
                                r"```(?:json)?\s*(.*?)```", text, re.DOTALL
                            )
                            if fence_match:
                                text = fence_match.group(1).strip()
                            else:
                                # Fallback: strip any remaining backticks and whitespace
                                text = text.strip().strip("`").strip()

                            # Find the first { or [ and the last } or ]
                            # This is very robust against leading/trailing prose
                            start_idx = -1
                            for i, char in enumerate(text):
                                if char in ("{", "["):
                                    start_idx = i
                                    break

                            if start_idx != -1:
                                end_char = "}" if text[start_idx] == "{" else "]"
                                end_idx = text.rfind(end_char)
                                if end_idx != -1:
                                    text = text[start_idx : end_idx + 1]

                            print(
                                f"📩 [OpenRouter/{self.model}] JSON response ({len(text)} chars)"
                            )
                            try:
                                return json.loads(text)
                            except json.JSONDecodeError:
                                # One last try: remove any trailing commas before closing braces/brackets
                                # (Some models output invalid JSON like {"a": 1,})
                                text = re.sub(r",\s*([\]}])", r"\1", text)
                                return json.loads(text)

                except json.JSONDecodeError as e:
                    print(f"⚠️ [OpenRouter] JSON parse failed on attempt {attempt+1}: {e}")
                    print(f"📄 RAW TEXT (Attempt {attempt+1}):\n{text}\n")
                    if attempt == 2:
                        snippet = text[:100] + "..." if len(text) > 100 else text
                        raise RuntimeError(
                            f"JSON generation failed. Raw snippet: {snippet}. Error: {e}"
                        )
                    await asyncio.sleep(2)
                except aiohttp.ClientResponseError as e:
                    # #region agent log
                    _agent_debug_log(
                        "H4",
                        "openrouter_client.py:generate_json:ClientResponseError",
                        "aiohttp ClientResponseError",
                        {
                            "attempt": attempt,
                            "http_status": e.status,
                            "message": (e.message or "")[:200],
                        },
                        run_id="post-fix",
                    )
                    # #endregion
                    print(f"⚠️ [OpenRouter] HTTP {e.status} on attempt {attempt+1}: {e.message}")
                    if e.status == 429:
                        fb = self.AGENT_FALLBACK_MODELS.get(self.agent_name or "")
                        if (
                            fb
                            and self.model != fb
                            and not fallback_used
                            and self.model == original_model
                        ):
                            fallback_used = True
                            self.model = fb
                            _agent_stdout_evidence(
                                {
                                    "event": "openrouter_429_fallback",
                                    "attempt": attempt,
                                    "from_model": original_model,
                                    "to_model": fb,
                                    "via": "ClientResponseError",
                                }
                            )
                            continue
                        if attempt < 2:
                            await asyncio.sleep(float(min(2**attempt, 60)))
                            continue
                    raise RuntimeError(f"OpenRouter API error {e.status}: {e.message}")
                except Exception as e:
                    # #region agent log
                    _agent_debug_log(
                        "H4",
                        "openrouter_client.py:generate_json:Exception",
                        "non-aiohttp exception",
                        {
                            "attempt": attempt,
                            "exc_type": type(e).__name__,
                            "exc_snippet": str(e)[:400],
                        },
                        run_id="post-fix",
                    )
                    # #endregion
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        await asyncio.sleep(float(min(2**attempt, 60)))
                        continue
                    raise RuntimeError(f"OpenRouter JSON generation failed: {e}")

            # #region agent log
            _agent_debug_log(
                "H1-H3",
                "openrouter_client.py:generate_json:exhausted",
                "all attempts exhausted without success",
                {
                    "model": self.model,
                    "agent_name": self.agent_name,
                    "original_model": original_model,
                    "fallback_used": fallback_used,
                },
                run_id="post-fix",
            )
            # #endregion
            _agent_stdout_evidence(
                {
                    "event": "openrouter_exhausted",
                    "model": self.model,
                    "agent_name": self.agent_name,
                    "original_model": original_model,
                    "fallback_used": fallback_used,
                }
            )
            raise RuntimeError(
                "OpenRouter failed after 3 attempts. This is usually due to Rate Limits (429) on free models. "
                "Try again shortly, add OpenRouter credits, or use a non-free model id."
            )
        finally:
            self.model = original_model
    
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
