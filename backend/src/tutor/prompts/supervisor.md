# Supervisor LLM Pre-Analysis (SPEC-UPDATE-001)

This document describes the supervisor's pre-analysis behavior.

The supervisor agent uses Claude Haiku to analyze input text before routing to
specialist agents (reading, grammar, vocabulary).

## Analysis Output

The supervisor produces a JSON object with the following structure:

```json
{
  "sentences": [
    {"text": "sentence text", "difficulty": 3, "focus": ["grammar"]},
    ...
  ],
  "overall_difficulty": 3,
  "focus_summary": ["grammar", "vocabulary", "reading"]
}
```

## Fields

- sentences: List of individual sentences with difficulty ratings and focus areas
- overall_difficulty: Overall passage difficulty (1-5, relative to student level)
- focus_summary: Prioritized list of learning focus areas for the passage

## Note

The supervisor builds its prompt inline in code (supervisor.py) because the
prompt contains JSON braces that would conflict with Python str.format() template
substitution. This file serves as documentation only.
