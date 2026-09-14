#!/usr/bin/env python3
"""Render the canonical Agent Skills sources for WorkBuddy."""

from __future__ import annotations

import json
import re


AUTHOR = "songgoldenwind-crypto"

WORKBUDDY_METADATA = {
    "ziwei-skills": {
        "display_name": "紫微斗数全平台套装",
        "display_name_en": "Ziwei Doushu Complete Suite",
        "description_zh": "一个入口安装紫微斗数排盘、命盘核对与分层断盘完整能力。",
        "description_en": (
            "One install for Ziwei Doushu chart generation, verification, "
            "and layered interpretation."
        ),
    },
    "ziwei": {
        "display_name": "紫微斗数",
        "display_name_en": "Ziwei Doushu",
        "description_zh": (
            "生成并核对真太阳时命盘，按原局、专题或限运模式给出有盘面依据的紫微斗数解读。"
        ),
        "description_en": (
            "Generate and verify true-solar-time charts, then provide evidence-based "
            "natal, topic-focused, or timing interpretations."
        ),
    },
}

FRONTMATTER = re.compile(r"\A---\n(?P<header>[\s\S]*?)\n---\n(?P<body>[\s\S]*)\Z")
REFERENCE_LINK = re.compile(r"\[[^\]]+\]\((references/[^)]+)\)")


def yaml_string(value: str) -> str:
    """Return a JSON string, which is also a valid YAML scalar."""
    return json.dumps(value, ensure_ascii=False)


def frontmatter_value(header: str, field: str) -> str:
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", header, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"canonical SKILL.md is missing {field}")
    return match.group(1).strip()


def render_workbuddy_skill(skill_name: str, canonical: str, version: str) -> str:
    """Add WorkBuddy metadata and its explicit @references syntax."""
    if skill_name not in WORKBUDDY_METADATA:
        raise ValueError(f"unsupported WorkBuddy skill: {skill_name}")

    parsed = FRONTMATTER.fullmatch(canonical)
    if not parsed:
        raise ValueError(f"{skill_name}: malformed SKILL.md frontmatter")

    header = parsed.group("header")
    if frontmatter_value(header, "name") != skill_name:
        raise ValueError(f"{skill_name}: frontmatter name does not match directory")

    description = frontmatter_value(header, "description")
    metadata = WORKBUDDY_METADATA[skill_name]
    body = REFERENCE_LINK.sub(lambda match: f"@{match.group(1)}", parsed.group("body"))

    fields = (
        ("name", skill_name),
        ("display_name", metadata["display_name"]),
        ("display_name_en", metadata["display_name_en"]),
        ("description", description),
        ("description_zh", metadata["description_zh"]),
        ("description_en", metadata["description_en"]),
        ("version", version),
        ("author", AUTHOR),
        ("allowed-tools", "Read, Bash"),
    )
    rendered_header = "\n".join(f"{key}: {yaml_string(value)}" for key, value in fields)
    return f"---\n{rendered_header}\n---\n{body}"


def render_workbuddy_method(skill_name: str, canonical: str) -> str:
    """Turn a canonical Skill into a suite reference without a nested Skill entry."""
    if skill_name not in WORKBUDDY_METADATA or skill_name == "ziwei-skills":
        raise ValueError(f"unsupported WorkBuddy method: {skill_name}")

    parsed = FRONTMATTER.fullmatch(canonical)
    if not parsed:
        raise ValueError(f"{skill_name}: malformed SKILL.md frontmatter")
    if frontmatter_value(parsed.group("header"), "name") != skill_name:
        raise ValueError(f"{skill_name}: frontmatter name does not match directory")

    body = REFERENCE_LINK.sub(
        lambda match: f"@references/{skill_name}/{match.group(1).removeprefix('references/')}",
        parsed.group("body"),
    )
    body = body.replace(
        "python scripts/run_paipan.py",
        f"python scripts/{skill_name}/run_paipan.py",
    )
    body = body.replace("`scripts/", f"`scripts/{skill_name}/")
    return body
