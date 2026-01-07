"""Theme syncer for synchronizing Figma theme to frontends."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .parser import CSSParser


@dataclass
class ThemeChange:
    """Represents a single theme variable change."""
    target: str  # 'react' or 'legacy'
    variable: str
    old_value: Optional[str]
    new_value: str
    action: str  # 'update', 'add', 'skip'
    reason: Optional[str] = None


class ThemeSyncer:
    """Syncs theme variables from Figma export to frontend CSS files."""

    def __init__(self, project_root: Path, mapping_path: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.mapping_path = mapping_path or self.project_root / 'tooling' / 'theme-mapping.json'
        self._mapping: Optional[dict] = None

    @property
    def mapping(self) -> dict:
        """Load and cache the theme mapping."""
        if self._mapping is None:
            self._mapping = json.loads(self.mapping_path.read_text(encoding='utf-8'))
        return self._mapping

    @property
    def figma_path(self) -> Path:
        """Path to Figma theme.css."""
        return self.project_root / self.mapping['figma_source']

    @property
    def react_path(self) -> Path:
        """Path to React theme.css."""
        return self.project_root / self.mapping['react_target']

    @property
    def legacy_path(self) -> Path:
        """Path to Legacy base.css."""
        return self.project_root / self.mapping['legacy_target']

    def analyze(self) -> Dict[str, List[ThemeChange]]:
        """
        Analyze what changes would be made.

        Returns dict with 'react' and 'legacy' keys containing lists of changes.
        """
        figma_parser = CSSParser(self.figma_path)
        figma_root = figma_parser.get_root_variables()
        figma_dark = figma_parser.get_dark_variables()

        changes = {
            'react': [],
            'legacy': [],
            'summary': {
                'react_updates': 0,
                'react_skipped': 0,
                'legacy_updates': 0,
                'legacy_skipped': 0,
            }
        }

        # Analyze React changes (supports both light and dark)
        react_changes = self._analyze_react(figma_root, figma_dark)
        changes['react'] = react_changes
        changes['summary']['react_updates'] = sum(1 for c in react_changes if c.action in ('update', 'add'))
        changes['summary']['react_skipped'] = sum(1 for c in react_changes if c.action == 'skip')

        # Analyze Legacy changes (light mode only)
        legacy_changes = self._analyze_legacy(figma_root)
        changes['legacy'] = legacy_changes
        changes['summary']['legacy_updates'] = sum(1 for c in legacy_changes if c.action in ('update', 'add'))
        changes['summary']['legacy_skipped'] = sum(1 for c in legacy_changes if c.action == 'skip')

        return changes

    def _analyze_react(self, figma_root: dict, figma_dark: dict) -> List[ThemeChange]:
        """Analyze changes needed for React theme."""
        changes = []
        var_mapping = self.mapping['variables']

        # Get current React variables if file exists
        current_root = {}
        current_dark = {}
        if self.react_path.exists():
            react_parser = CSSParser(self.react_path)
            current_root = react_parser.get_root_variables()
            current_dark = react_parser.get_dark_variables()

        for figma_var, mapping in var_mapping.items():
            react_var = mapping.get('react')
            if not react_var:
                continue

            # Light mode
            if figma_var in figma_root:
                new_value = figma_root[figma_var]
                old_value = current_root.get(react_var)
                if old_value != new_value:
                    changes.append(ThemeChange(
                        target='react',
                        variable=f':root {react_var}',
                        old_value=old_value,
                        new_value=new_value,
                        action='update' if old_value else 'add',
                    ))

            # Dark mode
            if figma_var in figma_dark:
                new_value = figma_dark[figma_var]
                old_value = current_dark.get(react_var)
                if old_value != new_value:
                    changes.append(ThemeChange(
                        target='react',
                        variable=f'.dark {react_var}',
                        old_value=old_value,
                        new_value=new_value,
                        action='update' if old_value else 'add',
                    ))

        return changes

    def _analyze_legacy(self, figma_root: dict) -> List[ThemeChange]:
        """Analyze changes needed for Legacy CSS (light mode only)."""
        changes = []
        var_mapping = self.mapping['variables']

        # Get current Legacy variables if file exists
        current_vars = {}
        if self.legacy_path.exists():
            legacy_parser = CSSParser(self.legacy_path)
            current_vars = legacy_parser.get_root_variables()

        for figma_var, mapping in var_mapping.items():
            legacy_var = mapping.get('legacy')
            if not legacy_var:
                changes.append(ThemeChange(
                    target='legacy',
                    variable=figma_var,
                    old_value=None,
                    new_value=figma_root.get(figma_var, ''),
                    action='skip',
                    reason='No legacy mapping',
                ))
                continue

            if figma_var in figma_root:
                new_value = figma_root[figma_var]
                old_value = current_vars.get(legacy_var)
                if old_value != new_value:
                    changes.append(ThemeChange(
                        target='legacy',
                        variable=legacy_var,
                        old_value=old_value,
                        new_value=new_value,
                        action='update' if old_value else 'add',
                    ))

        return changes

    def sync(self, dry_run: bool = False, react_only: bool = False, legacy_only: bool = False) -> Dict:
        """
        Sync theme variables to frontend CSS files.

        Args:
            dry_run: If True, only analyze without making changes.
            react_only: Only sync to React frontend.
            legacy_only: Only sync to Legacy frontend.

        Returns:
            Dict with analysis results and sync status.
        """
        analysis = self.analyze()

        if dry_run:
            return {
                'dry_run': True,
                'changes': analysis,
            }

        result = {
            'dry_run': False,
            'changes': analysis,
            'synced': {
                'react': False,
                'legacy': False,
            }
        }

        # Sync to React
        if not legacy_only and analysis['react']:
            self._sync_react(analysis['react'])
            result['synced']['react'] = True

        # Sync to Legacy
        if not react_only and analysis['legacy']:
            self._sync_legacy(analysis['legacy'])
            result['synced']['legacy'] = True

        return result

    def _sync_react(self, changes: List[ThemeChange]):
        """Apply changes to React theme.css by copying from Figma."""
        # For React, we mostly just copy the Figma file since it's nearly identical
        # This ensures we get any new variables or structural changes
        figma_content = self.figma_path.read_text(encoding='utf-8')
        self.react_path.parent.mkdir(parents=True, exist_ok=True)
        self.react_path.write_text(figma_content, encoding='utf-8')

    def _sync_legacy(self, changes: List[ThemeChange]):
        """Apply changes to Legacy base.css."""
        if not self.legacy_path.exists():
            # Create a basic CSS file with variables
            self._create_legacy_css(changes)
            return

        content = self.legacy_path.read_text(encoding='utf-8')

        for change in changes:
            if change.action == 'skip':
                continue

            var_name = change.variable
            new_value = change.new_value

            # Pattern to match the variable declaration
            pattern = re.compile(
                rf'({re.escape(var_name)})\s*:\s*[^;]+;',
                re.MULTILINE
            )

            if pattern.search(content):
                # Update existing variable
                content = pattern.sub(f'{var_name}: {new_value};', content)
            else:
                # Add new variable to :root block
                root_pattern = re.compile(r'(:root\s*\{)([^}]*)\}', re.DOTALL)
                match = root_pattern.search(content)
                if match:
                    existing = match.group(2)
                    new_block = f'{existing}  {var_name}: {new_value};\n'
                    content = root_pattern.sub(f'{match.group(1)}{new_block}}}', content)

        self.legacy_path.write_text(content, encoding='utf-8')

    def _create_legacy_css(self, changes: List[ThemeChange]):
        """Create a new Legacy CSS file with theme variables."""
        lines = ['/* Cookie 2 - Legacy Theme Variables */\n', '/* Generated by figma-sync-theme */\n\n', ':root {\n']

        for change in changes:
            if change.action != 'skip':
                lines.append(f'  {change.variable}: {change.new_value};\n')

        lines.append('}\n')

        self.legacy_path.parent.mkdir(parents=True, exist_ok=True)
        self.legacy_path.write_text(''.join(lines), encoding='utf-8')
