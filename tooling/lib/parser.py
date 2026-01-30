"""CSS parser for extracting theme variables."""

import re
from pathlib import Path
from typing import Dict, Optional


class CSSParser:
    """Parses CSS files to extract CSS variables."""

    # Pattern to match CSS variable declarations: --name: value;
    VAR_PATTERN = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")

    # Pattern to match :root or .dark blocks specifically
    ROOT_PATTERN = re.compile(r":root\s*\{([^}]*)\}", re.DOTALL)
    DARK_PATTERN = re.compile(r"\.dark\s*\{([^}]*)\}", re.DOTALL)

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None

    @property
    def content(self) -> str:
        """Load and cache file content."""
        if self._content is None:
            self._content = self.file_path.read_text(encoding="utf-8")
        return self._content

    def _extract_variables(self, block_content: str) -> Dict[str, str]:
        """Extract CSS variables from a block's content."""
        variables = {}
        for match in self.VAR_PATTERN.finditer(block_content):
            var_name = match.group(1)
            var_value = match.group(2).strip()
            variables[var_name] = var_value
        return variables

    def parse_variables(self) -> Dict[str, Dict[str, str]]:
        """
        Parse CSS variables from the file.

        Returns a dict with selectors as keys and variable dicts as values:
        {
            ':root': {'--primary': '#6b8e5f', '--background': '#faf9f7'},
            '.dark': {'--primary': '#8aa879', '--background': '#2a2220'},
        }
        """
        result = {}

        # Extract :root variables
        root_match = self.ROOT_PATTERN.search(self.content)
        if root_match:
            variables = self._extract_variables(root_match.group(1))
            if variables:
                result[":root"] = variables

        # Extract .dark variables
        dark_match = self.DARK_PATTERN.search(self.content)
        if dark_match:
            variables = self._extract_variables(dark_match.group(1))
            if variables:
                result[".dark"] = variables

        return result

    def get_root_variables(self) -> Dict[str, str]:
        """Get variables from :root (light mode)."""
        variables = self.parse_variables()
        return variables.get(":root", {})

    def get_dark_variables(self) -> Dict[str, str]:
        """Get variables from .dark (dark mode)."""
        variables = self.parse_variables()
        return variables.get(".dark", {})


def parse_css_file(file_path: str | Path) -> Dict[str, Dict[str, str]]:
    """Convenience function to parse a CSS file."""
    parser = CSSParser(file_path)
    return parser.parse_variables()
