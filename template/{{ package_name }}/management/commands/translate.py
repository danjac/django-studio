import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

try:
    import polib  # type: ignore[import-untyped]
except ImportError:
    polib = None  # type: ignore[assignment]


class Command(BaseCommand):
    """Extract, count, or apply translations to/from a .po file."""

    help = (
        "extract: dump untranslated/fuzzy entries from a .po file as JSON.\n"
        "count:   print a summary for a .po file, or scan all .po files under a locale directory.\n"
        "apply:   write a translations JSON back into a .po file."
    )

    def add_arguments(self, parser: CommandParser) -> None:  # noqa: D102
        parser.add_argument(
            "subcommand",
            choices=["extract", "count", "apply"],
            help="extract, count, or apply.",
        )
        parser.add_argument(
            "target",
            help="Path to a .po file, a locale directory (e.g. locale/fr), or a locale code (e.g. fr) for count.",
        )
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
        target: str,
        translations: str | None,
        **options: Any,
    ) -> None:
        if polib is None:
            raise CommandError("polib is not installed. Run: uv add --dev polib")

        if subcommand == "count":
            po_files = self._resolve_count_target(target)
            self._count_files(po_files)
        else:
            po_path = Path(target)
            if not po_path.exists() or po_path.suffix != ".po":
                raise CommandError(f".po file not found: {po_path}")
            if subcommand == "extract":
                self._extract(po_path)
            else:
                if translations is None:
                    raise CommandError("translations JSON file is required for apply.")
                translations_path = Path(translations)
                if not translations_path.exists():
                    raise CommandError(
                        f"Translations file not found: {translations_path}"
                    )
                self._apply(po_path, translations_path)

    @staticmethod
    def _resolve_count_target(target_str: str) -> list[Path]:
        target = Path(target_str)
        if target.is_dir():
            po_files = sorted(target.rglob("*.po"))
            if not po_files:
                raise CommandError(f"No .po files found under {target}")
            return po_files
        if target.suffix == ".po":
            if not target.exists():
                raise CommandError(f"File not found: {target}")
            return [target]
        resolved = Path("locale") / target_str
        if resolved.is_dir():
            po_files = sorted(resolved.rglob("*.po"))
            if not po_files:
                raise CommandError(f"No .po files found under {resolved}")
            return po_files
        raise CommandError(f"Not a .po file or locale directory: {target}")

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

    def _count_file(self, po_path: Path) -> dict[str, int]:
        assert polib is not None
        po = polib.pofile(str(po_path))
        total = len(po)
        translated = untranslated = fuzzy = obsolete = 0
        for entry in po:
            if entry.obsolete:
                obsolete += 1
            elif entry.fuzzy:
                fuzzy += 1
                translated += 1
            elif entry.msgid_plural:
                if all(entry.msgstr_plural.values()):
                    translated += 1
                else:
                    untranslated += 1
            elif entry.msgstr:
                translated += 1
            else:
                untranslated += 1
        return {
            "total": total,
            "translated": translated,
            "untranslated": untranslated,
            "fuzzy": fuzzy,
            "obsolete": obsolete,
        }

    def _count_files(self, po_files: list[Path]) -> None:
        locale_root = Path("locale")
        totals: dict[str, int] = {
            "total": 0,
            "translated": 0,
            "untranslated": 0,
            "fuzzy": 0,
            "obsolete": 0,
        }
        for po_file in po_files:
            counts = self._count_file(po_file)
            try:
                rel = po_file.relative_to(locale_root)
            except ValueError:
                rel = po_file
            self.stdout.write(f"--- {rel} ---")
            self.stdout.write(self._format_counts(counts))
            self.stdout.write("")
            for k in totals:
                totals[k] += counts[k]
        if len(po_files) > 1:
            self.stdout.write(f"--- totals ({len(po_files)} files) ---")
            self.stdout.write(self._format_counts(totals))

    @staticmethod
    def _format_counts(counts: dict[str, int]) -> str:
        return (
            f"Total:        {counts['total']}\n"
            f"Translated:   {counts['translated']}\n"
            f"Untranslated: {counts['untranslated']}\n"
            f"Fuzzy:        {counts['fuzzy']}\n"
            f"Obsolete:     {counts['obsolete']}"
        )

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
