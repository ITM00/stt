from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from re import Match

DEV_DIALECT_TEMPLATE_PATH = "app/templates/dev_dialect.json"


@dataclass(slots=True)
class RegexTemplate:
    pattern: str
    replacement: str | None = None
    handler: str | None = None


class TextPostProcessor:
    def __init__(self, template_path: str) -> None:
        self.template_path = template_path
        self.templates = self._load_templates(template_path)
        self.dev_dialect_templates = self._load_templates_optional(DEV_DIALECT_TEMPLATE_PATH)

    def _load_templates(self, template_path: str) -> list[RegexTemplate]:
        raw = json.loads(Path(template_path).read_text(encoding="utf-8"))
        return [RegexTemplate(**item) for item in raw]

    def _load_templates_optional(self, template_path: str) -> list[RegexTemplate]:
        path = Path(template_path)
        if not path.exists():
            return []
        return self._load_templates(template_path)

    def _apply_templates(self, text: str, templates: list[RegexTemplate]) -> str:
        output = text
        for template in templates:
            if template.handler == "dev_dialect":
                output = re.sub(
                    template.pattern,
                    lambda match: self._format_dev_dialect(match),
                    output,
                    flags=re.IGNORECASE,
                )
                continue
            if template.replacement is None:
                continue
            # Use a callable replacer so `replacement` is treated as a literal string.
            # `re.sub` replacement templates interpret backslashes (e.g. "\\") which breaks
            # simple punctuation mappings like a single backslash.
            output = re.sub(
                template.pattern,
                lambda _m, repl=template.replacement: repl,
                output,
                flags=re.IGNORECASE,
            )
        return output

    def _apply_spoken_layout_commands(self, text: str) -> str:
        # Convert spoken layout commands to real line breaks for paste targets.
        return re.sub(
            r"\s*(?:\bnew\s*line\b|\bновая\s*строка\b)\s*",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

    def process(self, text: str, template_path: str | None = None) -> str:
        templates = self.templates
        if template_path is not None and template_path != self.template_path:
            templates = self._load_templates(template_path)

        output = self._apply_templates(text, templates)
        output = self._apply_templates(output, self.dev_dialect_templates)
        output = self._apply_spoken_layout_commands(output)
        return output.strip()

    def _format_dev_dialect(self, match: Match[str]) -> str:
        keyword = match.group(1).lower()
        body = match.group(2).strip()

        words = re.findall(r"[^\W\d_]+", body, flags=re.UNICODE)
        if not words:
            return keyword
        return f"{keyword} {'\\'.join(words)}"
