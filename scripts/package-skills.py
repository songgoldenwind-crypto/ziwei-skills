#!/usr/bin/env python3
"""Build reproducible upload archives for skills and plugin channels."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from workbuddy_compat import render_workbuddy_method, render_workbuddy_skill


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("ziwei",)
PAIPAN_DIR = "ziwei-paipan-code"
FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package Ziwei skills for upload and plugins.")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "dist",
        help="Output directory (default: ./dist).",
    )
    return parser.parse_args()


def files_under(directory: Path) -> list[Path]:
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file()
        and path.name != ".DS_Store"
        and not any(part in {".git", ".venv", "venv", "node_modules"} for part in path.parts)
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )


def write_archive(
    path: Path,
    entries: list[tuple[Path, str]],
    *,
    overrides: dict[str, bytes] | None = None,
) -> None:
    overrides = overrides or {}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, archive_name in sorted(entries, key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_name, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if source.stat().st_mode & 0o111 else 0o644) << 16
            archive.writestr(info, overrides.get(archive_name, source.read_bytes()))


def skill_entries(skill_name: str, *, wrapper: bool) -> list[tuple[Path, str]]:
    skill_root = REPO_ROOT / "skills" / skill_name
    prefix = f"{skill_name}/" if wrapper else ""
    entries = [
        (path, prefix + path.relative_to(skill_root).as_posix())
        for path in files_under(skill_root)
    ]
    entries.append((REPO_ROOT / "LICENSE", prefix + "LICENSE"))
    return entries


def plugin_entries() -> list[tuple[Path, str]]:
    included = [
        REPO_ROOT / ".codex-plugin" / "plugin.json",
        REPO_ROOT / ".claude-plugin" / "plugin.json",
        REPO_ROOT / "README.md",
        REPO_ROOT / "LICENSE",
    ]
    included.extend(path for name in SKILLS for path in files_under(REPO_ROOT / "skills" / name))
    return [(path, path.relative_to(REPO_ROOT).as_posix()) for path in included]


def workbuddy_suite_entries() -> tuple[list[tuple[Path, str]], dict[str, bytes]]:
    """Build one WorkBuddy SkillHub card containing the method and the paipan code."""
    suite_prefix = "ziwei-skills/"
    suite_skill = REPO_ROOT / "workbuddy" / "ziwei-skills" / "SKILL.md"
    entries: list[tuple[Path, str]] = [
        (suite_skill, suite_prefix + "SKILL.md"),
        (REPO_ROOT / "README.md", suite_prefix + "README.md"),
        (REPO_ROOT / "CHANGELOG.md", suite_prefix + "CHANGELOG.md"),
        (REPO_ROOT / "LICENSE", suite_prefix + "LICENSE"),
    ]
    overrides = {
        suite_prefix + "SKILL.md": render_workbuddy_skill(
            "ziwei-skills",
            suite_skill.read_text(encoding="utf-8"),
            plugin_version(),
        ).encode("utf-8")
    }

    for skill_name in SKILLS:
        skill_root = REPO_ROOT / "skills" / skill_name
        method_source = skill_root / "SKILL.md"
        method_target = suite_prefix + f"references/{skill_name}/method.md"
        entries.append((method_source, method_target))
        overrides[method_target] = render_workbuddy_method(
            skill_name,
            method_source.read_text(encoding="utf-8"),
        ).encode("utf-8")
        for source in files_under(skill_root):
            if source == method_source:
                continue
            relative = source.relative_to(skill_root)
            if relative.parts[0] == "references":
                target = Path("references") / skill_name / Path(*relative.parts[1:])
            elif relative.parts[0] == "scripts":
                target = Path("scripts") / skill_name / Path(*relative.parts[1:])
            else:
                target = Path("references") / skill_name / relative
            entries.append((source, suite_prefix + target.as_posix()))

    paipan_root = REPO_ROOT / PAIPAN_DIR
    entries.extend(
        (source, suite_prefix + "scripts/ziwei-paipan/" + source.relative_to(paipan_root).as_posix())
        for source in files_under(paipan_root)
    )
    return entries, overrides


def plugin_version() -> str:
    manifest = REPO_ROOT / ".codex-plugin" / "plugin.json"
    return json.loads(manifest.read_text(encoding="utf-8"))["version"]


def main() -> None:
    args = parse_args()
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    built: list[Path] = []
    version = plugin_version()
    for skill_name in SKILLS:
        # Portable/OpenAI skill bundles expose SKILL.md at the archive root.
        skill_path = output / f"{skill_name}.skill"
        write_archive(skill_path, skill_entries(skill_name, wrapper=False))
        agent_zip_path = output / f"{skill_name}-agent.zip"
        write_archive(agent_zip_path, skill_entries(skill_name, wrapper=False))
        # Claude upload ZIPs contain the named skill folder at the archive root.
        zip_path = output / f"{skill_name}.zip"
        write_archive(zip_path, skill_entries(skill_name, wrapper=True))
        # WorkBuddy upload archives use a named wrapper directory, platform
        # metadata, and explicit @references paths.
        workbuddy_path = output / f"{skill_name}-workbuddy.zip"
        workbuddy_skill_name = f"{skill_name}/SKILL.md"
        canonical = (REPO_ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        write_archive(
            workbuddy_path,
            skill_entries(skill_name, wrapper=True),
            overrides={
                workbuddy_skill_name: render_workbuddy_skill(
                    skill_name, canonical, version
                ).encode("utf-8")
            },
        )
        built.extend((skill_path, agent_zip_path, zip_path, workbuddy_path))

    plugin_path = output / "ziwei-skills-plugin.zip"
    write_archive(plugin_path, plugin_entries())
    built.append(plugin_path)

    workbuddy_suite_path = output / "ziwei-skills-workbuddy.zip"
    suite_entries, suite_overrides = workbuddy_suite_entries()
    write_archive(workbuddy_suite_path, suite_entries, overrides=suite_overrides)
    built.append(workbuddy_suite_path)

    for path in built:
        print(path)


if __name__ == "__main__":
    main()
