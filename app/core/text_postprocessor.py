from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from re import Match


@dataclass(slots=True)
class RegexTemplate:
    pattern: str
    replacement: str | None = None
    handler: str | None = None


class TextPostProcessor:
    def __init__(self, template_path: str) -> None:
        raw = json.loads(Path(template_path).read_text(encoding="utf-8"))
        self.templates = [RegexTemplate(**item) for item in raw]

    def process(self, text: str) -> str:
        output = text
        for template in self.templates:
            if template.handler == "dev_dialect":
                output = re.sub(
                    template.pattern,
                    lambda match: self._format_dev_dialect(match),
                    output,
                )
                continue
            if template.replacement is None:
                continue
            output = re.sub(template.pattern, template.replacement, output)
        return output.strip()

    def _format_dev_dialect(self, match: Match[str]) -> str:
        keyword = match.group(1)
        body = match.group(2).strip()

        if keyword in {"file", "function"}:
            normalized = re.sub(r"\s*\.\s*", ".", body)
            words = re.split(r"\s+", normalized.strip())
            formatted = "_".join(part for part in words if part)
            return f"{keyword} {formatted}"

        if keyword == "class":
            words = [part for part in re.split(r"\s+", body) if part]
            formatted = "".join(part[:1].upper() + part[1:] for part in words)
            return f"class {formatted}"

        if keyword == "path":
            words = [part for part in re.split(r"\s+", body) if part]
            return f"path {'\\'.join(words)}"

        return match.group(0)
