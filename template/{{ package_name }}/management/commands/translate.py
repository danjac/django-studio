from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

try:
    import polib  # type: ignore[import-untyped]
except ImportError:
    polib = None  # type: ignore[assignment]


class Command(BaseCommand):
    """Extract untranslated .po entries as JSON, or apply a translations JSON back."""

    help = (
        "extract: dump untranslated/fuzzy entries from a .po file as JSON.\n"
        "apply:   write a translations JSON back into a .po file."
    )

    def add_arguments(self, parser: CommandParser) -> None:  # noqa: D102
        parser.add_argument(
            "subcommand",
            choices=["extract", "apply"],
            help="extract or apply.",
        )
        parser.add_argument("po_file", help="Path to the .po file.")
        parser.add_argument(
            "translations",
            nargs="?",
            default=None,
            help="Path to the translations JSON file (required for apply).",
        )

    def handle(  # noqa: D102
        self,
        *,
        subcommand: str,
        po_file: str,
        translations: str | None,
        **options: Any,
    ) -> None:
        if polib is None:
            raise CommandError("polib is not installed. Run: uv add --dev polib")

        po_path = Path(po_file)
        if not po_path.exists():
            raise CommandError(f"File not found: {po_path}")

        if subcommand == "extract":
            self._extract(po_path)
        else:
            if translations is None:
                raise CommandError("translations JSON file is required for apply.")
            translations_path = Path(translations)
            if not translations_path.exists():
                raise CommandError(f"Translations file not found: {translations_path}")
            self._apply(po_path, translations_path)

    def _extract(self, po_path: Path) -> None:
        assert polib is not None
        po = polib.pofile(str(po_path))
        entries = []
        for entry in po:
            if entry.fuzzy:
                pass
            elif entry.msgid_plural:
                if all(entry.msgstr_plural.values()):
                    continue
            elif entry.msgstr:
                continue
            item: dict[str, Any] = {
                "msgid": entry.msgid,
                "msgstr": entry.msgstr,
                "fuzzy": entry.fuzzy,
            }
            if entry.msgid_plural:
                item["msgid_plural"] = entry.msgid_plural
                item["msgstr_plural"] = dict(entry.msgstr_plural)
            if entry.comment:
                item["comment"] = entry.comment
            entries.append(item)
        self.stdout.write(json.dumps(entries, ensure_ascii=False, indent=2))

    def _apply(self, po_path: Path, translations_path: Path) -> None:
        assert polib is not None
        po = polib.pofile(str(po_path))
        translations: list[dict[str, Any]] = json.loads(translations_path.read_text())
        by_msgid = {t["msgid"]: t for t in translations}

        updated = 0
        for entry in po:
            t = by_msgid.get(entry.msgid)
            if t is None:
                continue
            if "msgstr_plural" in t:
                for idx_str, form in t["msgstr_plural"].items():
                    entry.msgstr_plural[int(idx_str)] = form
            elif t.get("msgstr"):
                entry.msgstr = t["msgstr"]
            if entry.fuzzy:
                entry.flags.remove("fuzzy")
            updated += 1

        po.save(str(po_path))
        self.stdout.write(
            self.style.SUCCESS(f"Applied {updated} translation(s) to {po_path}.")
        )
