"""RAG: context construction + grounded answer generation.

- `build_context_items` turns retrieved articles/live docs into numbered, citable context.
- `build_context_text` renders a token-budgeted, source-tagged CONTEXT block.
- `generate_answer` produces a grounded answer. With a real LLM it does abstractive generation
  under the grounding prompt; with the local provider it does deterministic extractive synthesis
  over the *same* context — both honour the citation contract and the "insufficient info" rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.ai.llm.base import LLMProvider
from app.ai.llm.local_provider import split_sentences
from app.ai.prompts import GROUNDED_SYSTEM, GROUNDED_USER_TEMPLATE

_WORD = re.compile(r"[a-z0-9\u4e00-\u9fff]+")


@dataclass
class ContextItem:
    index: int
    title: str
    source: str
    url: str
    published_at: datetime | None
    is_official: bool
    is_rumor: bool
    text: str


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD.findall((text or "").lower()) if len(t) > 1}


def build_context_text(items: list[ContextItem], *, max_chars: int = 4000) -> str:
    lines: list[str] = []
    budget = max_chars
    for it in items:
        tag = "official" if it.is_official else ("rumor" if it.is_rumor else "media")
        date = it.published_at.strftime("%Y-%m-%d") if it.published_at else "unknown date"
        body = (it.text or it.title).strip()
        block = f"[{it.index}] ({it.source}, {tag}, {date}) {it.title}\n{body}"
        if len(block) > budget:
            block = block[: max(budget, 0)]
        lines.append(block)
        budget -= len(block)
        if budget <= 0:
            break
    return "\n\n".join(lines)


def _insufficient(language: str) -> str:
    if language == "zh":
        return "根据目前检索到的资讯，暂时没有足够信息来回答这个问题。请尝试更换关键词或稍后再试。"
    return (
        "There isn't enough information in the retrieved sources to answer this confidently. "
        "Try different keywords or check back later."
    )


def extractive_answer(question: str, items: list[ContextItem], language: str) -> str:
    """Deterministic grounded synthesis used in local (no-key) mode."""
    if not items:
        return _insufficient(language)

    q_tokens = _tokens(question)
    scored: list[tuple[float, ContextItem, str]] = []
    for it in items:
        best_sentence = it.title
        best_overlap = -1.0
        for sent in split_sentences(it.text) or [it.title]:
            overlap = len(_tokens(sent) & q_tokens)
            if overlap > best_overlap:
                best_overlap, best_sentence = overlap, sent
        scored.append((best_overlap, it, best_sentence))

    scored.sort(key=lambda x: (x[0], -x[1].index), reverse=True)
    top = scored[: min(4, len(scored))]

    if language == "zh":
        lead = f"以下是围绕「{question.strip()}」检索到的关键进展："
        header = "关键进展"
        note = "注：以上内容均来自已检索来源；标注为 rumor 的为传闻，official 为官方消息。"
    else:
        lead = f"Here is what the retrieved sources say about “{question.strip()}”:"
        header = "Key developments"
        note = (
            "Note: all points above come from retrieved sources; "
            "items marked rumor are unconfirmed."
        )

    bullets = []
    for _, it, sent in top:
        tag = " (official)" if it.is_official else (" (rumor)" if it.is_rumor else "")
        bullets.append(f"- {sent.strip()}{tag} [{it.index}]")

    return f"{lead}\n\n{header}:\n" + "\n".join(bullets) + f"\n\n{note}"


async def generate_answer(
    llm: LLMProvider, question: str, items: list[ContextItem], language: str
) -> str:
    if not items:
        return _insufficient(language)
    if llm.name == "local":
        return extractive_answer(question, items, language)

    context = build_context_text(items)
    user = GROUNDED_USER_TEMPLATE.format(question=question, language=language, context=context)
    answer = await llm.complete(system=GROUNDED_SYSTEM, user=user, temperature=0.2, max_tokens=800)
    return answer or extractive_answer(question, items, language)
