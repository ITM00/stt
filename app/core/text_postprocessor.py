from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RegexTemplate:
    pattern: str
    replacement: str


class TextPostProcessor:
    def __init__(self, template_path: str) -> None:
        raw = json.loads(Path(template_path).read_text(encoding="utf-8"))
        self.templates = [RegexTemplate(**item) for item in raw]

    def process(self, text: str) -> str:
        output = text
        for template in self.templates:
            output = re.sub(template.pattern, template.replacement, output)
        return output.strip()
