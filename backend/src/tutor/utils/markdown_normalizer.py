"""Markdown output normalizer for LLM tutor agent responses.

Converts non-standard heading formats produced by LLMs (bold text,
wrong heading levels, plain text with colons) to the required structure:
- Reading/Grammar agents: ### 문장 N + #### subheadings
- Vocabulary agent: ## [word] + ### N. subheadings

Applied after LLM call, before storing results in state.
If normalization raises an exception the original content is returned unchanged.
"""

from __future__ import annotations

import re


def normalize_reading_output(content: str) -> str:
    """Normalize reading agent markdown output.

    Ensures:
    - Sentence headings use ### 문장 N
    - Sub-headings use #### 단위별 해석 / 자연스러운 해석 / 읽기 지시
    - Every heading is followed by a blank line
    """
    try:
        content = _normalize_sentence_headings(content)
        content = _normalize_reading_subheadings(content)
        content = _ensure_heading_blank_lines(content)
        return content
    except Exception:
        return content


def normalize_grammar_output(content: str) -> str:
    """Normalize grammar agent markdown output.

    Ensures:
    - Sentence headings use ### 문장 N
    - Sub-headings use #### 문법 포인트 / 왜 이 구조? / 한국어와의 차이 / 시험 포인트
    - Every heading is followed by a blank line
    """
    try:
        content = _normalize_sentence_headings(content)
        content = _normalize_grammar_subheadings(content)
        content = _ensure_heading_blank_lines(content)
        return content
    except Exception:
        return content


def normalize_vocabulary_output(content: str) -> str:
    """Normalize vocabulary agent markdown output.

    Ensures:
    - English word headings use ## [word]
    - Numbered sub-headings use ### N. name format
    - Every heading is followed by a blank line
    """
    try:
        content = _normalize_vocab_word_headings(content)
        content = _normalize_vocab_subheadings(content)
        content = _ensure_heading_blank_lines(content)
        return content
    except Exception:
        return content


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_sentence_headings(content: str) -> str:
    """Normalize '### 문장 N' headings from various malformed patterns."""
    # **문장 N**: or **문장 N**
    content = re.sub(r"^\*\*문장\s+(\d+)\*\*:?\s*$", r"### 문장 \1", content, flags=re.MULTILINE)
    # 문장 N: (plain text with colon)
    content = re.sub(r"^문장\s+(\d+)\s*:\s*$", r"### 문장 \1", content, flags=re.MULTILINE)
    # 문장 N (plain text, standalone line, no colon, no bold, no #)
    content = re.sub(r"^문장\s+(\d+)\s*$", r"### 문장 \1", content, flags=re.MULTILINE)
    # Wrong heading levels: # ## (too shallow) or #### ##### ###### (too deep)
    content = re.sub(r"^#{1,2}\s+문장\s+(\d+)\s*$", r"### 문장 \1", content, flags=re.MULTILINE)
    content = re.sub(r"^#{4,6}\s+문장\s+(\d+)\s*$", r"### 문장 \1", content, flags=re.MULTILINE)
    return content


def _fix_korean_subheading(content: str, name: str, target: str) -> str:
    """Convert a single Korean subheading name to the target #### format."""
    escaped = re.escape(name)
    # **name**: or **name**
    content = re.sub(r"^\*\*" + escaped + r"\*\*:?\s*$", target, content, flags=re.MULTILINE)
    # name: (plain text with colon, no #)
    content = re.sub(r"^" + escaped + r"\s*:\s*$", target, content, flags=re.MULTILINE)
    # name (plain text, standalone line, no colon, no bold, no #)
    content = re.sub(r"^" + escaped + r"\s*$", target, content, flags=re.MULTILINE)
    # Wrong heading levels: ### (too shallow) or ##### ###### (too deep)
    content = re.sub(r"^#{1,3}\s+" + escaped + r"\s*$", target, content, flags=re.MULTILINE)
    content = re.sub(r"^#{5,6}\s+" + escaped + r"\s*$", target, content, flags=re.MULTILINE)
    return content


def _normalize_reading_subheadings(content: str) -> str:
    """Normalize #### subheadings for reading agent."""
    for name, target in [
        ("단위별 해석", "#### 단위별 해석"),
        ("자연스러운 해석", "#### 자연스러운 해석"),
        ("읽기 지시", "#### 읽기 지시"),
    ]:
        content = _fix_korean_subheading(content, name, target)
    return content


def _normalize_grammar_subheadings(content: str) -> str:
    """Normalize #### subheadings for grammar agent."""
    for name, target in [
        ("문법 포인트", "#### 문법 포인트"),
        ("왜 이 구조?", "#### 왜 이 구조?"),
        ("한국어와의 차이", "#### 한국어와의 차이"),
        ("시험 포인트", "#### 시험 포인트"),
    ]:
        content = _fix_korean_subheading(content, name, target)
    return content


def _normalize_vocab_word_headings(content: str) -> str:
    """Normalize ## [word] headings for vocabulary agent.

    Only converts headings that start with an ASCII letter (English word entries).
    Numbered Korean sub-headings (### 1. 기본 뜻) are left untouched.
    """
    # Wrong heading level: ### word or #### word ... ###### word (English only)
    content = re.sub(
        r"^#{3,6}\s+([A-Za-z][A-Za-z0-9\s\-]*)\s*$",
        r"## \1",
        content,
        flags=re.MULTILINE,
    )
    # **word**: or **word** (English only, no spaces before **)
    content = re.sub(
        r"^\*\*([A-Za-z][A-Za-z0-9\s\-]*)\*\*:?\s*$",
        r"## \1",
        content,
        flags=re.MULTILINE,
    )
    return content


def _normalize_vocab_subheadings(content: str) -> str:
    """Normalize ### N. subheadings for vocabulary agent."""
    numbered = [
        (r"1", r"기본 뜻", "### 1. 기본 뜻"),
        (r"2", r"문장 속 의미", "### 2. 문장 속 의미"),
        (r"3", r"핵심 의미 이미지", "### 3. 핵심 의미 이미지"),
        (r"4", r"어원[^\n*]*", "### 4. 어원 (PIE 어근까지)"),
        (r"5", r"같은 어원 파생 단어[^\n*]*", "### 5. 같은 어원 파생 단어 (최소 3개)"),
        (r"6", r"기억 연결 팁", "### 6. 기억 연결 팁"),
    ]
    for num, name_pattern, target in numbered:
        # **N. name**: or **N. name**
        content = re.sub(
            r"^\*\*" + num + r"\.\s+" + name_pattern + r"\*\*:?\s*$",
            target,
            content,
            flags=re.MULTILINE,
        )
        # N. name: (plain text with colon, no #)
        content = re.sub(
            r"^" + num + r"\.\s+" + name_pattern + r"\s*:\s*$",
            target,
            content,
            flags=re.MULTILINE,
        )
        # N. name (plain text, standalone line, no colon, no bold, no #)
        content = re.sub(
            r"^" + num + r"\.\s+" + name_pattern + r"\s*$",
            target,
            content,
            flags=re.MULTILINE,
        )
        # Wrong heading level: ## N. name (too shallow) or #### ... ###### (too deep)
        content = re.sub(
            r"^#{1,2}\s+" + num + r"\.\s+" + name_pattern + r"\s*$",
            target,
            content,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r"^#{4,6}\s+" + num + r"\.\s+" + name_pattern + r"\s*$",
            target,
            content,
            flags=re.MULTILINE,
        )
    return content


def _ensure_heading_blank_lines(content: str) -> str:
    """Ensure a blank line after every heading line.

    If a heading (# through ######) is immediately followed by non-blank
    content on the next line, a blank line is inserted between them.
    """
    return re.sub(r"(^#{1,6}\s+[^\n]+)\n([^\n])", r"\1\n\n\2", content, flags=re.MULTILINE)
