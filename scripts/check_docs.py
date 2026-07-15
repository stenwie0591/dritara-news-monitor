"""Controllo leggero del project brain, senza dipendenze esterne."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "AGENTS.md",
    "docs/README.md",
    "docs/project-state.md",
    "docs/ai-handoff.md",
    "docs/as-is/codebase-map.md",
    "docs/as-is/workflows.md",
    "docs/as-is/data-model.md",
    "docs/to-be/target-architecture.md",
    "docs/to-be/state-machines.md",
    "docs/to-be/backlog.md",
    "docs/security/threat-model.md",
    "docs/roadmap-to-be.md",
    "docs/governance/delivery-framework.md",
    "docs/governance/definition-of-done.md",
    "docs/governance/framework-assessment.md",
    "docs/governance/adoption-guide.md",
    "docs/governance/macro-task-template.md",
    "docs/governance/micro-task-template.md",
    "docs/governance/macro-review-template.md",
    "docs/governance/risk-register.md",
    "docs/reviews/README.md",
    "docs/adr/004-portable-project-brain.md",
]
STARTER_REQUIRED = [
    "templates/project-brain/README.md",
    "templates/project-brain/AGENTS.md",
    "templates/project-brain/docs/README.md",
    "templates/project-brain/docs/project-state.md",
    "templates/project-brain/docs/architecture-as-is.md",
    "templates/project-brain/docs/roadmap-to-be.md",
    "templates/project-brain/docs/to-be/backlog.md",
    "templates/project-brain/docs/ai-handoff.md",
    "templates/project-brain/docs/governance/delivery-framework.md",
    "templates/project-brain/docs/governance/definition-of-done.md",
    "templates/project-brain/docs/governance/risk-register.md",
    "templates/project-brain/docs/governance/macro-task-template.md",
    "templates/project-brain/docs/governance/micro-task-template.md",
    "templates/project-brain/docs/governance/macro-review-template.md",
    "templates/project-brain/docs/governance/adr-template.md",
    "templates/project-brain/docs/adr/README.md",
    "templates/project-brain/docs/reviews/README.md",
]
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
MICRO_ROW = re.compile(r"^\|\s*(M\d{2}\.\d{2})\s*\|[^\n]+\|$", re.MULTILINE)
MACRO_HEADING = re.compile(r"^##\s+(M\d{2})\s+", re.MULTILINE)


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required document: {relative}")

    for relative in STARTER_REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing project-brain starter file: {relative}")

    for document in [ROOT / "AGENTS.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        text = document.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            clean = target.split("#", 1)[0].strip().strip("<>")
            if not clean or clean.startswith(("http://", "https://", "/")):
                continue
            if not (document.parent / clean).resolve().exists():
                errors.append(
                    f"broken local link: {document.relative_to(ROOT)} -> {target}"
                )

    roadmap = (ROOT / "docs/roadmap-to-be.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/to-be/backlog.md").read_text(encoding="utf-8")
    macro_ids = MACRO_HEADING.findall(roadmap)
    backlog_macro_ids = MACRO_HEADING.findall(backlog)
    micro_ids = MICRO_ROW.findall(backlog)
    if len(macro_ids) != len(set(macro_ids)):
        errors.append("duplicate macro-task ID in roadmap")
    if len(micro_ids) != len(set(micro_ids)):
        errors.append("duplicate micro-task ID in backlog")
    if set(macro_ids) != set(backlog_macro_ids):
        errors.append("roadmap/backlog macro-task IDs do not match")
    orphan_micro = [item for item in micro_ids if item.split(".", 1)[0] not in macro_ids]
    if orphan_micro:
        errors.append(f"micro-task without roadmap parent: {', '.join(orphan_micro)}")
    for macro_id in macro_ids:
        section = roadmap.split(f"## {macro_id}", 1)[1].split("\n## ", 1)[0]
        if "Macro DoD:" not in section:
            errors.append(f"macro-task without Macro DoD: {macro_id}")
    if "DoD specifica" not in backlog or not micro_ids:
        errors.append("backlog has no parseable micro-task DoD registry")

    if errors:
        print("\n".join(errors))
        return 1
    print(
        "Documentation check passed "
        f"({len(REQUIRED)} required documents, {len(STARTER_REQUIRED)} starter files)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
