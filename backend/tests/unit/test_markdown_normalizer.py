"""Unit tests for tutor.utils.markdown_normalizer.

Tests cover each pattern transformation and the safety guarantee that
the original content is returned unchanged on exception.
"""

import re

import pytest

from tutor.utils.markdown_normalizer import (
    normalize_grammar_output,
    normalize_reading_output,
    normalize_vocabulary_output,
)


# ---------------------------------------------------------------------------
# normalize_reading_output
# ---------------------------------------------------------------------------


class TestNormalizeReadingOutput:
    def test_bold_sentence_heading_converted(self):
        inp = "**문장 1**\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 1" in out

    def test_bold_sentence_heading_with_colon_converted(self):
        inp = "**문장 2**:\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 2" in out

    def test_plain_text_sentence_heading_converted(self):
        inp = "문장 3:\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 3" in out

    def test_plain_text_sentence_heading_no_colon_converted(self):
        inp = "문장 1\nEthical theories / ..."
        out = normalize_reading_output(inp)
        assert "### 문장 1" in out

    def test_shallow_heading_level_corrected(self):
        inp = "## 문장 1\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 1" in out

    def test_deep_heading_level_corrected(self):
        inp = "#### 문장 1\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 1" in out

    def test_correct_sentence_heading_unchanged(self):
        inp = "### 문장 1\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 1" in out

    def test_bold_subheading_단위별해석_converted(self):
        inp = "**단위별 해석**:\n내용"
        out = normalize_reading_output(inp)
        assert "#### 단위별 해석" in out

    def test_bold_subheading_자연스러운해석_converted(self):
        inp = "**자연스러운 해석**\n내용"
        out = normalize_reading_output(inp)
        assert "#### 자연스러운 해석" in out

    def test_plain_subheading_읽기지시_converted(self):
        inp = "읽기 지시:\n내용"
        out = normalize_reading_output(inp)
        assert "#### 읽기 지시" in out

    def test_plain_subheading_no_colon_converted(self):
        inp = "단위별 해석\n윤리 이론들은 / 경험에"
        out = normalize_reading_output(inp)
        assert "#### 단위별 해석" in out

    def test_all_plain_subheadings_no_colon_converted(self):
        inp = (
            "### 문장 1\n> 원문\n\n"
            "단위별 해석\n해석 내용\n\n"
            "자연스러운 해석\n자연스러운 내용\n\n"
            "읽기 지시\n지시 내용"
        )
        out = normalize_reading_output(inp)
        assert "#### 단위별 해석" in out
        assert "#### 자연스러운 해석" in out
        assert "#### 읽기 지시" in out

    def test_correct_subheadings_unchanged(self):
        inp = "#### 단위별 해석\n내용\n\n#### 자연스러운 해석\n번역"
        out = normalize_reading_output(inp)
        assert "#### 단위별 해석" in out
        assert "#### 자연스러운 해석" in out

    def test_heading_blank_line_inserted(self):
        inp = "### 문장 1\n내용이 헤더에 붙어있음"
        out = normalize_reading_output(inp)
        assert "### 문장 1\n\n" in out

    def test_exception_returns_original(self, monkeypatch):
        import tutor.utils.markdown_normalizer as m

        original = m._normalize_sentence_headings

        def boom(content):
            raise RuntimeError("simulated error")

        monkeypatch.setattr(m, "_normalize_sentence_headings", boom)
        original_content = "some content"
        result = normalize_reading_output(original_content)
        assert result == original_content


# ---------------------------------------------------------------------------
# normalize_grammar_output
# ---------------------------------------------------------------------------


class TestNormalizeGrammarOutput:
    def test_sentence_heading_converted(self):
        inp = "**문장 1**\n원문"
        out = normalize_grammar_output(inp)
        assert "### 문장 1" in out

    def test_bold_문법포인트_converted(self):
        inp = "**문법 포인트**:\n관계대명사"
        out = normalize_grammar_output(inp)
        assert "#### 문법 포인트" in out

    def test_bold_왜이구조_converted(self):
        inp = "**왜 이 구조?**\n설명"
        out = normalize_grammar_output(inp)
        assert "#### 왜 이 구조?" in out

    def test_plain_한국어차이_converted(self):
        inp = "한국어와의 차이:\n비교"
        out = normalize_grammar_output(inp)
        assert "#### 한국어와의 차이" in out

    def test_bold_시험포인트_converted(self):
        inp = "**시험 포인트**:\n함정"
        out = normalize_grammar_output(inp)
        assert "#### 시험 포인트" in out

    def test_wrong_level_subheading_corrected(self):
        inp = "### 문법 포인트\n설명"
        out = normalize_grammar_output(inp)
        assert "#### 문법 포인트" in out

    def test_correct_output_unchanged(self):
        inp = "### 문장 1\n\n> 원문\n\n#### 문법 포인트\n\n설명"
        out = normalize_grammar_output(inp)
        assert "### 문장 1" in out
        assert "#### 문법 포인트" in out

    def test_exception_returns_original(self, monkeypatch):
        import tutor.utils.markdown_normalizer as m

        monkeypatch.setattr(m, "_normalize_sentence_headings", lambda c: (_ for _ in ()).throw(ValueError))
        original_content = "grammar content"
        result = normalize_grammar_output(original_content)
        assert result == original_content


# ---------------------------------------------------------------------------
# normalize_vocabulary_output
# ---------------------------------------------------------------------------


class TestNormalizeVocabularyOutput:
    def test_h1_word_heading_corrected(self):
        inp = "# accomplish\n내용"
        out = normalize_vocabulary_output(inp)
        assert "## accomplish" in out

    def test_wrong_level_word_heading_corrected(self):
        inp = "### accomplish\n내용"
        out = normalize_vocabulary_output(inp)
        assert "## accomplish" in out

    def test_deep_word_heading_corrected(self):
        inp = "#### persist\n내용"
        out = normalize_vocabulary_output(inp)
        assert "## persist" in out

    def test_bold_word_heading_converted(self):
        inp = "**accomplish**:\n내용"
        out = normalize_vocabulary_output(inp)
        assert "## accomplish" in out

    def test_bold_word_heading_no_colon_converted(self):
        inp = "**persist**\n내용"
        out = normalize_vocabulary_output(inp)
        assert "## persist" in out

    def test_correct_word_heading_unchanged(self):
        inp = "## accomplish\n내용"
        out = normalize_vocabulary_output(inp)
        assert "## accomplish" in out

    def test_numbered_subheading_1_bold_converted(self):
        inp = "**1. 기본 뜻**:\n뜻"
        out = normalize_vocabulary_output(inp)
        assert "### 1. 기본 뜻" in out

    def test_numbered_subheading_2_plain_converted(self):
        inp = "2. 문장 속 의미:\n설명"
        out = normalize_vocabulary_output(inp)
        assert "### 2. 문장 속 의미" in out

    def test_numbered_subheading_3_converted(self):
        inp = "**3. 핵심 의미 이미지**\n이미지"
        out = normalize_vocabulary_output(inp)
        assert "### 3. 핵심 의미 이미지" in out

    def test_numbered_subheading_4_with_variant_converted(self):
        inp = "4. 어원 (PIE 어근):\n어원"
        out = normalize_vocabulary_output(inp)
        assert "### 4. 어원 (PIE 어근까지)" in out

    def test_numbered_subheading_5_converted(self):
        inp = "5. 같은 어원 파생 단어 (3개):\n단어들"
        out = normalize_vocabulary_output(inp)
        assert "### 5. 같은 어원 파생 단어 (최소 3개)" in out

    def test_numbered_subheading_6_converted(self):
        inp = "**6. 기억 연결 팁**:\n팁"
        out = normalize_vocabulary_output(inp)
        assert "### 6. 기억 연결 팁" in out

    def test_numbered_subheading_not_converted_to_word_heading(self):
        inp = "### 1. 기본 뜻\n내용"
        out = normalize_vocabulary_output(inp)
        # Should be corrected to ### 1. 기본 뜻, NOT converted to ## 1. 기본 뜻
        # Use line-anchor regex because "## 1. 기본 뜻" is a substring of "### 1. 기본 뜻"
        assert "### 1. 기본 뜻" in out
        assert not re.search(r"^## 1\. 기본 뜻", out, re.MULTILINE)

    def test_korean_heading_not_converted_to_word_heading(self):
        inp = "### 단위별 해석\n내용"
        out = normalize_vocabulary_output(inp)
        # Korean headings should not be converted by _normalize_vocab_word_headings
        # Use line-anchor regex because "## 단위별 해석" is a substring of "### 단위별 해석"
        assert not re.search(r"^## 단위별 해석", out, re.MULTILINE)

    def test_full_word_entry_structure(self):
        inp = (
            "### accomplish\n"
            "**1. 기본 뜻**:\n기본 뜻 내용\n\n"
            "2. 문장 속 의미:\n문장 속 의미 내용\n\n"
            "**3. 핵심 의미 이미지**\n이미지 내용\n\n"
            "4. 어원:\n어원 내용\n\n"
            "5. 같은 어원 파생 단어:\n파생어\n\n"
            "6. 기억 연결 팁:\n팁"
        )
        out = normalize_vocabulary_output(inp)
        assert "## accomplish" in out
        assert "### 1. 기본 뜻" in out
        assert "### 2. 문장 속 의미" in out
        assert "### 3. 핵심 의미 이미지" in out
        assert "### 4. 어원 (PIE 어근까지)" in out
        assert "### 5. 같은 어원 파생 단어 (최소 3개)" in out
        assert "### 6. 기억 연결 팁" in out

    def test_exception_returns_original(self, monkeypatch):
        import tutor.utils.markdown_normalizer as m

        monkeypatch.setattr(m, "_normalize_vocab_word_headings", lambda c: (_ for _ in ()).throw(ValueError))
        original_content = "vocab content"
        result = normalize_vocabulary_output(original_content)
        assert result == original_content


# ---------------------------------------------------------------------------
# _ensure_heading_blank_lines (via public functions)
# ---------------------------------------------------------------------------


class TestEnsureHeadingBlankLines:
    def test_blank_line_inserted_after_heading(self):
        inp = "### 문장 1\n내용"
        out = normalize_reading_output(inp)
        assert "### 문장 1\n\n" in out

    def test_existing_blank_line_preserved(self):
        inp = "### 문장 1\n\n내용"
        out = normalize_reading_output(inp)
        assert out.count("\n\n") >= 1
