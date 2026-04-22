"""Test LLM insights integration."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.code_health import CodeHealthAnalyzer
from app.services.local_models import LocalLLMClient


@pytest.mark.asyncio
async def test_llm_insights_generation():
    """Test that LLM insights are generated correctly."""
    # Create mock clients
    github_client = MagicMock()
    
    mock_llm_response = json.dumps({
        "ranked_findings": [
            {
                "id": "hardcoded-secret:/path/to/file.py:10",
                "impact_priority": 1,
                "business_context": "This is a production API key exposed in version control",
                "remediation_steps": ["Rotate the API key", "Use environment variables"],
                "is_false_positive": False,
                "automation_opportunity": "Use pre-commit hooks to detect secrets"
            }
        ],
        "executive_summary": "Critical: 1 exposed API key detected in production code."
    })
    
    llm_client = AsyncMock(spec=LocalLLMClient)
    llm_client.generate_json = AsyncMock(return_value=mock_llm_response)
    
    # Create analyzer with LLM client
    analyzer = CodeHealthAnalyzer(github_client, llm_client=llm_client)
    
    # Test findings
    findings = [
        {
            "id": "hardcoded-secret:/path/to/file.py:10",
            "category": "security",
            "severity": "High",
            "file_path": "/path/to/file.py",
            "line": 10,
            "message": "Potential secret detected",
            "suggestion": "Move to env var",
            "evidence": 'api_key = "gh_xxxxx"',
        }
    ]
    
    # Generate LLM insights
    insights = await analyzer._generate_llm_insights(findings, primary_language="python")
    
    # Verify results
    assert insights is not None
    assert insights["source"] == "llm"
    assert len(insights["ranked_findings"]) == 1
    assert insights["ranked_findings"][0]["impact_priority"] == 1
    assert insights["executive_summary"] == "Critical: 1 exposed API key detected in production code."
    
    # Verify LLM was called
    llm_client.generate_json.assert_called_once()


@pytest.mark.asyncio
async def test_llm_insights_graceful_fallback():
    """Test graceful fallback when LLM is unavailable."""
    github_client = MagicMock()
    
    findings = [
        {
            "id": "hardcoded-secret:/path/to/file.py:10",
            "category": "security",
            "severity": "High",
            "file_path": "/path/to/file.py",
            "line": 10,
            "message": "Potential secret detected",
            "suggestion": "Move to env var",
            "evidence": 'api_key = "gh_xxxxx"',
        }
    ]
    
    # Create analyzer without LLM client
    analyzer = CodeHealthAnalyzer(github_client, llm_client=None)
    
    # Try to generate insights (should gracefully return None)
    insights = await analyzer._generate_llm_insights(findings)
    
    assert insights is None


@pytest.mark.asyncio
async def test_llm_insights_handles_invalid_json():
    """Test that invalid LLM JSON is handled gracefully."""
    github_client = MagicMock()
    
    llm_client = AsyncMock(spec=LocalLLMClient)
    llm_client.generate_json = AsyncMock(return_value="invalid json {")
    
    analyzer = CodeHealthAnalyzer(github_client, llm_client=llm_client)
    
    findings = [
        {
            "id": "test:file:1",
            "category": "security",
            "severity": "High",
            "file_path": "file.py",
            "line": 1,
            "message": "Test",
            "suggestion": "Test",
            "evidence": "test",
        }
    ]
    
    # Generate insights with invalid JSON (should gracefully return None)
    insights = await analyzer._generate_llm_insights(findings)
    
    assert insights is None


@pytest.mark.asyncio
async def test_detect_primary_language():
    """Test that primary language detection works correctly."""
    from app.services.code_health import CodeHealthAnalyzer
    from unittest.mock import MagicMock

    github_client = MagicMock()
    analyzer = CodeHealthAnalyzer(github_client)

    # Test Python majority
    paths = {"utils.py", "helpers.py", "config.js"}
    lang = analyzer._detect_primary_language(paths)
    assert lang == "python"

    # Test JavaScript/TypeScript
    paths = {"index.ts", "app.tsx", "utils.js"}
    lang = analyzer._detect_primary_language(paths)
    assert lang in ["typescript", "javascript"]

    # Test empty set
    paths = set()
    lang = analyzer._detect_primary_language(paths)
    assert lang == "unknown"

    # Test single language
    paths = {"main.go"}
    lang = analyzer._detect_primary_language(paths)
    assert lang == "go"
