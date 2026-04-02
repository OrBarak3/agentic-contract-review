from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from contract_review_langgraph.config import env_flag
from contract_review_langgraph.models import ClauseExtraction
from contract_review_langgraph.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_user_prompt


class ProviderError(RuntimeError):
    """Raised when a provider call cannot be completed successfully."""


class BaseProvider(ABC):
    provider_name: str

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 45.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def extract(self, clauses: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Return normalized clause extraction payloads plus provider metadata."""


class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, provider_name: str, base_url: str, api_key: str, model: str) -> None:
        super().__init__(api_key=api_key, model=model)
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")

    def extract(self, clauses: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": build_extraction_user_prompt(clauses)},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        data = _coerce_json(content)
        return _normalize_extractions(
            clauses,
            data,
            provider_name=self.provider_name,
            model=self.model,
            fallback_used=False,
        )


class GeminiProvider(BaseProvider):
    provider_name = "gemini"

    def extract(self, clauses: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        prompt = EXTRACTION_SYSTEM_PROMPT + "\n\n" + build_extraction_user_prompt(clauses)
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(endpoint, json=payload)
        response.raise_for_status()
        body = response.json()
        try:
            content = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"Unexpected Gemini response shape: {body}") from exc
        data = _coerce_json(content)
        return _normalize_extractions(
            clauses,
            data,
            provider_name=self.provider_name,
            model=self.model,
            fallback_used=False,
        )


def extract_contract_details(
    clauses: list[dict[str, Any]],
    provider_name: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    provider_name = provider_name.lower().strip()
    try:
        provider = _build_provider(provider_name)
        return provider.extract(clauses)
    except Exception as exc:
        if not env_flag("ALLOW_HEURISTIC_FALLBACK", default=True):
            raise
        fallback, metadata = heuristic_extract_contract(clauses)
        metadata["fallback_reason"] = str(exc)
        metadata["requested_provider"] = provider_name
        return fallback, metadata


def _build_provider(provider_name: str) -> BaseProvider:
    if provider_name == "openai":
        api_key = _required_env("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAICompatibleProvider("openai", base_url, api_key, model)
    if provider_name == "grok":
        api_key = _required_env("GROK_API_KEY")
        model = os.getenv("GROK_MODEL", "grok-3-mini")
        base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
        return OpenAICompatibleProvider("grok", base_url, api_key, model)
    if provider_name == "gemini":
        api_key = _required_env("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        return GeminiProvider(api_key=api_key, model=model)
    raise ProviderError(f"Unsupported provider: {provider_name}")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ProviderError(f"Missing required environment variable: {name}")
    return value


def _normalize_extractions(
    clauses: list[dict[str, Any]],
    payload: dict[str, Any],
    provider_name: str,
    model: str,
    fallback_used: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_items = payload.get("clauses", [])
    by_id = {item.get("clause_id"): item for item in raw_items if isinstance(item, dict)}
    results: list[dict[str, Any]] = []
    for clause in clauses:
        raw_item = by_id.get(clause["clause_id"]) or heuristic_extract_clause(clause)
        merged = {
            "clause_id": clause["clause_id"],
            "clause_type": raw_item.get("clause_type", "general"),
            "summary": raw_item.get("summary", clause["text"][:180]),
            "obligations": raw_item.get("obligations", []),
            "key_dates": raw_item.get("key_dates", []),
            "amounts": raw_item.get("amounts", []),
            "jurisdiction": raw_item.get("jurisdiction"),
            "risk_level": raw_item.get("risk_level", "medium"),
            "confidence": raw_item.get("confidence", 0.65),
            "evidence_spans": raw_item.get("evidence_spans", []),
        }
        results.append(ClauseExtraction.model_validate(merged).model_dump())
    metadata = {
        "provider": provider_name,
        "model": model,
        "fallback_used": fallback_used,
    }
    return results, metadata


def _coerce_json(content: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return json.loads(stripped)


def heuristic_extract_contract(clauses: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = [ClauseExtraction.model_validate(heuristic_extract_clause(clause)).model_dump() for clause in clauses]
    metadata = {
        "provider": "heuristic",
        "model": "local-rules",
        "fallback_used": True,
    }
    return results, metadata


def heuristic_extract_clause(clause: dict[str, Any]) -> dict[str, Any]:
    text = clause["text"]
    lowered = text.lower()

    clause_type = "general"
    type_keywords = {
        "payment": "payment",
        "fee": "payment",
        "invoice": "payment",
        "liability": "liability",
        "indemn": "indemnity",
        "termination": "termination",
        "renewal": "renewal",
        "governing law": "governing_law",
        "jurisdiction": "governing_law",
        "confidential": "confidentiality",
        "security": "security",
    }
    for keyword, mapped_type in type_keywords.items():
        if keyword in lowered:
            clause_type = mapped_type
            break

    risk_level = "low"
    confidence = 0.9
    high_risk_terms = (
        "unlimited liability",
        "indemnify",
        "hold harmless",
        "sole discretion",
        "automatic renewal",
        "perpetual",
    )
    medium_risk_terms = (
        "terminate for convenience",
        "penalty",
        "exclusive jurisdiction",
    )

    if any(term in lowered for term in high_risk_terms) or clause_type in {"liability", "indemnity"}:
        risk_level = "high"
        confidence = 0.92
    elif any(term in lowered for term in medium_risk_terms) or clause_type in {"termination", "renewal"}:
        risk_level = "medium"
        confidence = 0.82

    obligations = []
    if "shall" in lowered:
        obligations.append("Contains affirmative obligations")
    if "must" in lowered:
        obligations.append("Contains mandatory requirements")

    amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)
    key_dates = re.findall(r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|[A-Z][a-z]+ \d{1,2}, \d{4})\b", text)
    jurisdiction_match = re.search(r"governed by the laws of ([A-Za-z ,]+)", text, re.IGNORECASE)

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    summary = sentences[0] if sentences and sentences[0] else text[:180]
    evidence = [summary[:160]]
    if risk_level != "low":
        evidence.append(text[:160])

    return {
        "clause_id": clause["clause_id"],
        "clause_type": clause_type,
        "summary": summary,
        "obligations": obligations,
        "key_dates": key_dates,
        "amounts": amounts,
        "jurisdiction": jurisdiction_match.group(1).strip() if jurisdiction_match else None,
        "risk_level": risk_level,
        "confidence": confidence,
        "evidence_spans": evidence,
    }
