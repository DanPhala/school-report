from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
import json
import logging
import re

from translation import client as llm_client

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#TODO: Refactor and move the models (prompt as well)
# -- Schema models --
class StudentInfo(BaseModel):
    student_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    grade_level: Optional[str] = None
    class_name: Optional[str] = None
    school_name: Optional[str] = None


class SubjectGrade(BaseModel):
    subject: str
    term: Optional[str] = None
    numeric_grade: Optional[float] = None
    letter_grade: Optional[str] = None
    teacher_comments: Optional[str] = None
    competencies: Optional[Dict[str, Any]] = None


class Attendance(BaseModel):
    days_present: Optional[int] = None
    days_absent: Optional[int] = None
    tardies: Optional[int] = None


class BehaviorNote(BaseModel):
    date: Optional[str] = None
    note: str
    teacher: Optional[str] = None


class ReportCard(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict)
    student: StudentInfo
    summary: Optional[str] = None
    subjects: List[SubjectGrade] = Field(default_factory=list)
    attendance: Optional[Attendance] = None
    behavior: Optional[List[BehaviorNote]] = None
    overall_gpa: Optional[float] = None
    recommendations: Optional[List[str]] = None


_PROMPT_PATHS = [
    Path(__file__).parent / "prompts" / "report_prompt.json",
    Path(__file__).parent.parent / "prompts" / "report_prompt.json",
]

_DEFAULT_PROMPT = """
You are a data normalizer. Given the input text or extracted fields from a report card, produce a JSON object that exactly matches the following schema (no extra fields):

Schema:
{{
  "meta": {{ "source": "<string>", "raw_format": "<string>", "extraction_confidence": "<0-1>" }},
  "student": {{
    "student_id": "<string|null>",
    "first_name": "<string|null>",
    "last_name": "<string|null>",
    "date_of_birth": "<ISO date|null>",
    "grade_level": "<string|null>",
    "class_name": "<string|null>",
    "school_name": "<string|null>"
  }},
  "summary": "<short human-readable summary|null>",
  "subjects": [
    {{
      "subject": "<string>",
      "term": "<string|null>",
      "quarter_grades": {{
          "Q1": <number|null>,
          "Q2": <number|null>,
          "Q3": <number|null>,
          "Q4": <number|null>
      }},
      "numeric_grade": <number|null>,
      "letter_grade": "<string|null>",
      "teacher_comments": "<string|null>",
      "competencies": {{ "<competency_name>": "<level>" }}
    }}
  ],
  "attendance": {{
    "days_present": <int|null>,
    "days_absent": <int|null>,
  }},
  "behavior": [
    {{ "date": "<date|null>", "note": "<string>", "teacher": "<string|null>" }}
  ],
  "overall_gpa": <number|null>,
  "recommendations": ["<string>"],
}}

Rules:
1. Output must be valid JSON only (no explanations).
2. When a value is missing use null.
3. Use the numeric values in the raw text **exactly as they appear** for each subject and map them to Q1, Q2, Q3, Q4 based on order.
4. If a subject has only one grade, place it in Q4 and set other quarters to null.
5. Compute 'numeric_grade' as the average of all quarters that are present.
6. Compute 'letter_grade' based on numeric_grade (A: 85-100, B: 70-84, C: 50-69, D: <50).
7. Include any free-text comments under 'teacher_comments'.
8. For recommendations, provide detailed, actionable, analytics-based advice.
9. Fill 'pass_or_fail' based on school passing rules and explain in 'pass_fail_reason'.

Input:
{input_text}

Return only the JSON.
"""



def _load_external_prompt() -> Optional[str]:
    for p in _PROMPT_PATHS:
        if p.exists():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    return raw.get("prompt") or raw.get("template") or None
                if isinstance(raw, str):
                    return raw
            except Exception as e:
                logger.warning("failed loading prompt %s: %s", p, e)
    return None


def build_llm_prompt(input_text: str, source: str = "unknown", raw_format: str = "text") -> str:
    template = _load_external_prompt() or _DEFAULT_PROMPT
    if input_text is None:
        input_text = ""
    prompt = template.replace("{input_text}", input_text)
    prompt += f"\n\nMeta: source={source}, raw_format={raw_format}\n"
    return prompt


def _extract_json_candidate(s: str) -> Optional[str]:
    match = re.search(r"(\{|\[)", s)
    if not match:
        return None
    start = match.start(1)
    for end in range(len(s), start, -1):
        candidate = s[start:end]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            continue
    return None


def call_llm(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.0, max_tokens: int = 4000) -> str:
    """
    Call the LLM and return raw text content.
    Uses the OpenAI client exported from translation.py.
    """
    try:
        resp = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        logger.exception("LLM call failed: %s", e)
        raise


def parse_llm_json(output: Union[str, Dict[str, Any]]) -> ReportCard:
    if isinstance(output, dict):
        parsed = output
    else:
        try:
            parsed = json.loads(output)
        except Exception:
            candidate = _extract_json_candidate(output)
            if not candidate:
                logger.error("LLM output is not valid JSON and no candidate was found")
                raise ValueError("LLM output is not valid JSON")
            parsed = json.loads(candidate)

    try:
        return ReportCard.parse_obj(parsed)
    except ValidationError as ve:
        logger.error("LLM output failed schema validation: %s", ve)
        raise


def normalize_with_llm(raw: Union[str, Dict[str, Any]],
                       source: str = "unknown",
                       raw_format: str = "text",
                       model: str = "gpt-4o-mini",
                       temperature: float = 0.0) -> ReportCard:
    """
    Always use the LLM:
     - build the prompt from raw (string or dict)
     - call the LLM
     - parse and validate the JSON into a ReportCard and return it
    """
    if isinstance(raw, dict):
        try:
            input_text = json.dumps(raw, ensure_ascii=False, indent=2)
        except Exception:
            input_text = str(raw)
    else:
        input_text = str(raw or "")

    prompt = build_llm_prompt(input_text, source=source, raw_format=raw_format)
    raw_output = call_llm(prompt, model=model, temperature=temperature)
    return parse_llm_json(raw_output)