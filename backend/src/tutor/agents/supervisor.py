"""
Supervisor agent - LLM-powered pre-analyzer.

Uses Claude Haiku to pre-analyze input text:
- Sentence segmentation
- Difficulty scoring per sentence (1-5)
- Learning focus recommendation
- Overall difficulty summary

Falls back to basic period-based splitting if LLM fails.
"""

from __future__ import annotations

import json
import logging

from tutor.config import get_settings
from tutor.models.llm import get_llm
from tutor.schemas import SentenceEntry, SupervisorAnalysis
from tutor.state import TutorState

logger = logging.getLogger(__name__)


def _fallback_analysis(text: str, level: int) -> SupervisorAnalysis:
    """Basic fallback when LLM fails - split by period."""
    sentences = [s.strip() + "." for s in text.split(".") if s.strip()]
    entries = [SentenceEntry(text=s, difficulty=level, focus=["reading"]) for s in sentences if s]
    return SupervisorAnalysis(
        sentences=entries,
        overall_difficulty=level,
        focus_summary=["reading", "grammar", "vocabulary"],
    )


async def supervisor_node(state: TutorState) -> dict:
    """
    LLM-powered pre-analysis of input text using Claude Haiku.

    Analyzes text to extract sentences, rate difficulty, and recommend
    learning focus areas. Results stored in supervisor_analysis for
    downstream agents to use.

    Routing still happens via route_by_task() in graph.py using task_type.

    Args:
        state: TutorState containing task_type, input_text, and level

    Returns:
        Dictionary with "supervisor_analysis" key containing SupervisorAnalysis
        or empty dict if task does not require pre-analysis
    """
    task_type = state.get("task_type", "analyze")
    input_text = state.get("input_text", "")
    level = state.get("level", 3)

    # For non-analyze tasks, skip pre-analysis
    if task_type not in ("analyze", "image_process") or not input_text:
        return {}

    try:
        settings = get_settings()
        llm = get_llm(settings.SUPERVISOR_MODEL, max_tokens=1024, timeout=30)

        prompt = f"""다음 영어 지문을 분석하여 JSON 형식으로 응답하라.

지문:
{input_text}

학생 레벨: {level}/5

다음 JSON 구조로만 응답하라 (다른 텍스트 없이):
{{
  "sentences": [
    {{"text": "문장1", "difficulty": 3, "focus": ["grammar"]}},
    {{"text": "문장2", "difficulty": 2, "focus": ["vocabulary", "reading"]}}
  ],
  "overall_difficulty": 3,
  "focus_summary": ["grammar", "vocabulary", "reading"]
}}

규칙:
- sentences: 지문을 개별 문장으로 분리 (마침표, 느낌표, 물음표 기준)
- difficulty: 각 문장 난이도 1-5 (학생 레벨 {level} 기준으로 상대 평가)
- focus: 각 문장의 학습 포인트 (grammar/vocabulary/reading/structure 중 선택)
- overall_difficulty: 전체 지문 난이도 1-5
- focus_summary: 전체 학습 포커스 우선순위"""

        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")

        data = json.loads(content[start:end])

        sentences = [
            SentenceEntry(
                text=s.get("text", ""),
                difficulty=max(1, min(5, s.get("difficulty", level))),
                focus=s.get("focus", ["reading"]),
            )
            for s in data.get("sentences", [])
            if s.get("text", "").strip()
        ]

        analysis = SupervisorAnalysis(
            sentences=sentences,
            overall_difficulty=max(1, min(5, data.get("overall_difficulty", level))),
            focus_summary=data.get("focus_summary", ["reading", "grammar", "vocabulary"]),
        )

        logger.info(
            f"Supervisor pre-analysis: {len(sentences)} sentences, "
            f"overall difficulty {analysis.overall_difficulty}"
        )
        return {"supervisor_analysis": analysis}

    except Exception as e:
        logger.warning(f"Supervisor LLM failed, using fallback: {e}")
        return {"supervisor_analysis": _fallback_analysis(input_text, level)}
