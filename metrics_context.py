"""비즈니스 메트릭 YAML 로드 및 SQL 프롬프트용 텍스트 변환."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

METRICS_PATH = Path(__file__).resolve().parent / "metrics.yml"


def _load_metrics(path: Path = METRICS_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    metrics = data.get("metrics") or []
    if not isinstance(metrics, list):
        raise ValueError("metrics.yml: 'metrics' must be a list")
    return metrics


def _format_metric(metric: dict[str, Any]) -> str:
    metric_id = metric.get("id", "unknown")
    aliases = metric.get("aliases") or []
    alias_text = ", ".join(str(a) for a in aliases) if aliases else "(none)"

    definition = metric.get("definition") or {}
    numerator = definition.get("numerator")
    denominator = definition.get("denominator")

    lines = [
        f"### {metric_id}",
        f"- aliases: {alias_text}",
    ]
    if numerator is not None:
        lines.append(f"- numerator: {numerator}")
    if denominator is not None:
        lines.append(f"- denominator: {denominator}")

    guidance = (metric.get("sql_guidance") or "").strip()
    if guidance:
        lines.append("- sql_guidance:")
        for guide_line in guidance.splitlines():
            lines.append(f"  {guide_line}")

    return "\n".join(lines)


def format_business_metrics(question: str | None = None) -> str:
    """질문에 매칭되는 메트릭을 프롬프트 텍스트로 반환.

    aliases가 질문에 포함되면 해당 메트릭만 넣고,
    매칭이 없으면 전체 메트릭을 넣는다.
    """
    metrics = _load_metrics()
    if not metrics:
        return "(no business metrics defined)"

    selected = metrics
    if question:
        q = question.casefold()
        matched = [
            m
            for m in metrics
            if any(str(alias).casefold() in q for alias in (m.get("aliases") or []))
        ]
        if matched:
            selected = matched

    body = "\n\n".join(_format_metric(m) for m in selected)
    return (
        "When the question mentions these metrics/aliases, "
        "follow the definitions and sql_guidance exactly.\n\n"
        f"{body}"
    )


# 모듈 로드 시 파일 존재·형식 검증 (시작 시 실패를 빠르게 드러냄)
_load_metrics()
