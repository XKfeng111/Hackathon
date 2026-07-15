from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable


@dataclass(frozen=True)
class PromptArtifact:
    mode: str
    label: str
    filename: str
    content: str
    source_files: list[str]
    record_count: int


MODE_DEFINITIONS = {
    "meeting_research_pi": {
        "label": "Research Ideas / Meeting Minutes",
        "fallback_focus": [
            "research question clarity",
            "hypothesis logic",
            "missing controls",
            "feasibility",
            "next experiment",
            "whether a real decision was made",
        ],
        "instruction": (
            "You are reviewing research ideas, meeting notes, experiment plans, and lab discussion "
            "records in a strict PI style. Focus on research logic, feasibility, missing controls, "
            "decision clarity, and concrete next experiments."
        ),
    },
    "slides_talk_pi": {
        "label": "Talks / Presentations / Slides",
        "fallback_focus": [
            "slide layout",
            "visual hierarchy",
            "title and takeaway alignment",
            "duplicate panels",
            "figure clarity",
            "storyline",
        ],
        "instruction": (
            "You are reviewing talks, presentation slides, figure sets, and visual scientific stories "
            "in a strict PI style. Focus on layout, figure clarity, visual hierarchy, duplicated panels, "
            "and whether each slide supports one message."
        ),
    },
    "paper_proposal_pi": {
        "label": "Papers / Proposals",
        "fallback_focus": [
            "claim strength",
            "evidence quality",
            "novelty",
            "logic gaps",
            "overclaiming",
            "mechanism support",
            "citation or comparison needs",
        ],
        "instruction": (
            "You are reviewing papers, proposals, manuscripts, and written scientific arguments in a "
            "strict PI style. Focus on claim strength, evidence quality, novelty, logical gaps, "
            "overclaiming, mechanism support, and missing comparisons."
        ),
    },
}

ACTION_VERBS = {
    "add", "remove", "revise", "change", "clarify", "show", "include", "move",
    "compare", "explain", "support", "strengthen", "define", "separate", "cite",
}
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are", "was",
    "were", "have", "has", "not", "but", "into", "more", "than", "then", "they", "their",
    "current", "should", "could", "would", "about", "when", "where", "which", "what",
}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text.strip())
    return [part.strip(" -•\t") for part in parts if len(part.strip()) >= 8]


def _iter_chunks(grouped_chunks: dict[str, list[dict]]) -> Iterable[tuple[str, str, str]]:
    for mode, file_groups in grouped_chunks.items():
        for group in file_groups:
            source_file = str(group.get("source_file", "unknown"))
            for chunk in group.get("chunks", []):
                if str(chunk).strip():
                    yield mode, source_file, str(chunk).strip()


def extract_keywords(chunks: list[str], limit: int = 12) -> list[str]:
    counts: dict[str, int] = {}
    for chunk in chunks:
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", chunk.lower()):
            if word in STOPWORDS:
                continue
            counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _count in ranked[:limit]]


def extract_key_sentences(chunks: list[str], limit: int = 6) -> list[str]:
    selected: list[str] = []
    for chunk in chunks:
        for sentence in _sentences(chunk):
            lower = sentence.lower()
            if any(verb in lower for verb in ACTION_VERBS) or len(selected) < 2:
                selected.append(sentence[:280])
            if len(selected) >= limit:
                return selected
    return selected


def build_prompt_content(mode: str, source_files: list[str], chunks: list[str]) -> str:
    definition = MODE_DEFINITIONS[mode]
    keywords = extract_keywords(chunks)
    key_sentences = extract_key_sentences(chunks)
    focus_items = definition["fallback_focus"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    reference_lines = key_sentences or [
        "Use the uploaded reference materials to infer concise, concrete PI-style criticism."
    ]
    keyword_lines = keywords or focus_items

    return "\n".join(
        [
            f"MODE: {mode}",
            f"SOURCE CATEGORY: {definition['label']}",
            f"SOURCE FILES: {'; '.join(source_files) if source_files else 'No uploaded references; using default mode prompt.'}",
            f"CREATED AT: {created_at}",
            "",
            definition["instruction"],
            "",
            "Focus on:",
            *[f"- {item}" for item in focus_items],
            "",
            "Keywords extracted from uploaded raw materials:",
            *[f"- {item}" for item in keyword_lines],
            "",
            "Reference patterns extracted from uploaded raw materials:",
            *[f"- {item}" for item in reference_lines],
            "",
            "PI-style response rules:",
            "- Be direct, concise, critical, and specific.",
            "- Use short sentences and concrete edits.",
            "- Prefer commands such as change, remove, add, move, show, clarify, and do not show.",
            "- Focus on clarity, evidence quality, plausibility, structure, technical consistency, and actionable next steps.",
            "- Do not sound generic or overly polite.",
            "",
            "Required response structure:",
            "PI: <one concise assessment sentence>",
            "",
            "Technical corrections needed:",
            "- <bullet>",
            "- <bullet>",
            "- <bullet>",
            "",
            "Implementation issues:",
            "- <bullet>",
            "- <bullet>",
            "- <bullet>",
            "",
            "Critical questions:",
            "- <bullet>",
        ]
    ) + "\n"


def build_mode_prompt_artifacts(grouped_chunks: dict[str, list[dict]]) -> dict[str, PromptArtifact]:
    artifacts: dict[str, PromptArtifact] = {}
    for mode, definition in MODE_DEFINITIONS.items():
        file_groups = grouped_chunks.get(mode, [])
        source_files: list[str] = []
        chunks: list[str] = []
        for group in file_groups:
            source_file = str(group.get("source_file", "unknown"))
            if source_file not in source_files:
                source_files.append(source_file)
            chunks.extend(str(chunk).strip() for chunk in group.get("chunks", []) if str(chunk).strip())
        content = build_prompt_content(mode, source_files, chunks)
        artifacts[mode] = PromptArtifact(
            mode=mode,
            label=str(definition["label"]),
            filename=f"{mode}_prompt.txt",
            content=content,
            source_files=source_files,
            record_count=len(chunks),
        )
    return artifacts


def build_combined_prompt_text(artifacts: dict[str, PromptArtifact]) -> str:
    sections: list[str] = []
    for mode in MODE_DEFINITIONS:
        artifact = artifacts[mode]
        sections.append("=" * 80)
        sections.append(artifact.content.strip())
    return "\n\n".join(sections) + "\n"
