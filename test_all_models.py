#!/usr/bin/env python3
"""
Comprehensive test for all OpenRouter models used by NexusMind agents.
Tests each model with a sample task appropriate for that agent.
"""
import os
import sys
import asyncio
import json

# Add backend to path
sys.path.insert(0, "NexusMind/backend")

# Load environment
from dotenv import load_dotenv
load_dotenv("NexusMind/backend/.env")

from app.config import settings
from app.core.openrouter_client import OpenRouterClient, create_llm_client

# Test configurations for each agent
AGENT_TESTS = {
    "BackendAgent": {
        "model": "qwen/qwen3-coder:free",
        "system": """You are an expert backend engineer specializing in Python, FastAPI, PostgreSQL, and REST APIs.
Given a task description, produce production-ready backend code.
Respond ONLY with valid JSON in this exact format:
{
  "files": [
    {"filename": "path/to/file.py", "content": "...full code..."}
  ],
  "summary": "Brief description of what was built",
  "api_contracts": [],
  "dependencies": []
}""",
        "prompt": "Create a simple FastAPI endpoint that returns a list of users from a mock database.",
        "validate": lambda r: "files" in r and isinstance(r.get("files"), list),
    },
    "FrontendAgent": {
        "model": "qwen/qwen3-coder:free",
        "system": """You are an expert frontend engineer specializing in React, Next.js 14, TypeScript, and Tailwind CSS.
Given a task description, produce production-ready frontend code.
Respond ONLY with valid JSON in this exact format:
{
  "files": [
    {"filename": "components/ComponentName.tsx", "content": "...full code..."}
  ],
  "summary": "Brief description of what was built",
  "dependencies": []
}""",
        "prompt": "Create a React component that displays a user profile card with name, email, and avatar.",
        "validate": lambda r: "files" in r and isinstance(r.get("files"), list),
    },
    "DataAgent": {
        "model": "google/gemma-4-31b-it:free",
        "system": """You are an expert data scientist and analyst.
Respond ONLY with valid JSON:
{
  "analysis": "Detailed written analysis",
  "insights": ["insight 1"],
  "sql_queries": [],
  "summary": "Executive summary"
}""",
        "prompt": "Analyze this sales data trend: Q1: $100K, Q2: $150K, Q3: $120K, Q4: $200K",
        "validate": lambda r: "analysis" in r and "insights" in r,
    },
    "ResearchAgent": {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "system": """You are a senior research analyst.
Respond ONLY with valid JSON:
{
  "findings": ["key insight 1"],
  "sources": ["reference 1"],
  "summary": "2-3 sentence synthesis",
  "recommendations": []
}""",
        "prompt": "Research the benefits of microservices architecture vs monolithic architecture.",
        "validate": lambda r: "findings" in r and "summary" in r,
    },
    "DevOpsAgent": {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "system": """You are a senior DevOps engineer specializing in Docker, CI/CD, and cloud infrastructure.
Respond ONLY with valid JSON:
{
  "files": [{"filename": "path", "content": "..."}],
  "summary": "Brief description",
  "tools_used": []
}""",
        "prompt": "Create a Dockerfile for a Python FastAPI application",
        "validate": lambda r: "files" in r and isinstance(r.get("files"), list),
    },
    "ContentAgent": {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "system": """You are a professional content creator and technical writer.
Respond ONLY with valid JSON:
{
  "content": "Full markdown content",
  "summary": "Brief description",
  "tags": []
}""",
        "prompt": "Write a blog post introduction about the benefits of AI in software development.",
        "validate": lambda r: "content" in r and "summary" in r,
    },
    "CriticAgent": {
        "model": "openai/gpt-oss-120b:free",
        "system": """You are a strict quality assurance reviewer and critic.
Respond ONLY with valid JSON:
{
  "score": 85,
  "issues": [],
  "approved": true,
  "feedback": "Overall feedback"
}""",
        "prompt": "Review this code quality: The function uses descriptive variable names, has error handling, and includes docstrings.",
        "validate": lambda r: "score" in r and "approved" in r,
    },
    "AssemblerAgent": {
        "model": "nvidia/nemotron-3-super-120b-a3b:free",
        "system": """You are a master architect and system integrator.
Respond ONLY with valid JSON:
{
  "final_content": "# Project Report",
  "summary": "Unified components",
  "file_manifest": []
}""",
        "prompt": "Summarize these components: Backend (FastAPI API), Frontend (React app), Database (PostgreSQL)",
        "validate": lambda r: "final_content" in r and "summary" in r,
    },
}


async def test_model(agent_name: str, config: dict) -> dict:
    """Test a single model."""
    print(f"\n{'='*60}")
    print(f"Testing {agent_name}")
    print(f"Model: {config['model']}")
    print(f"{'='*60}")
    
    try:
        # Create client
        client = OpenRouterClient(agent_name=agent_name, model=config["model"])
        
        # Test generate_json
        result = await client.generate_json(config["system"], config["prompt"])
        
        # Validate result structure
        is_valid = config["validate"](result)
        
        # Get usage
        usage = client.get_usage_summary()
        
        print(f"[OK] Response received")
        print(f"     Input tokens: {usage['total_input_tokens']}")
        print(f"     Output tokens: {usage['total_output_tokens']}")
        print(f"     Validation: {'PASSED' if is_valid else 'FAILED'}")
        print(f"     Summary: {result.get('summary', 'N/A')[:80]}...")
        
        return {
            "agent": agent_name,
            "model": config["model"],
            "success": True,
            "valid": is_valid,
            "usage": usage,
            "error": None,
        }
        
    except Exception as e:
        print(f"[X] FAILED: {type(e).__name__}: {e}")
        return {
            "agent": agent_name,
            "model": config["model"],
            "success": False,
            "valid": False,
            "usage": None,
            "error": str(e),
        }


async def test_all_models():
    """Test all configured models."""
    print("\n" + "="*60)
    print("NEXUSMIND OPENROUTER MODEL TEST SUITE")
    print("="*60)
    print(f"OpenRouter API Key: {'Set' if settings.OPENROUTER_API_KEY else 'NOT SET'}")
    
    if not settings.OPENROUTER_API_KEY:
        print("\n[X] ERROR: OPENROUTER_API_KEY not configured in .env")
        print("    Add: OPENROUTER_API_KEY=sk-or-v1-...")
        sys.exit(1)
    
    print(f"Testing {len(AGENT_TESTS)} models...\n")
    
    results = []
    for agent_name, config in AGENT_TESTS.items():
        result = await test_model(agent_name, config)
        results.append(result)
        
        # Rate limit: 20 requests/minute for free models
        print("     (Waiting 3s for rate limit...)")
        await asyncio.sleep(3)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r["success"] and r["valid"])
    failed = len(results) - passed
    
    for r in results:
        status = "[OK]" if r["success"] and r["valid"] else "[X]"
        error = f" - {r['error'][:40]}" if r["error"] else ""
        print(f"{status} {r['agent']:<20} ({r['model'][:30]:<30}){error}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")
    print(f"{'='*60}")
    
    # Save detailed results
    with open("model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed results saved to: model_test_results.json")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(test_all_models())
    sys.exit(0 if success else 1)
