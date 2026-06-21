"""Seed/refresh the bilingual question catalog from catalog/seed/catalog.json
(produced by scripts/export_catalog.mjs). Idempotent: re-running upserts and
prunes stale questions/options, then marks the version active."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import FormVersion, Option, Question


class Command(BaseCommand):
    help = "Seed the question catalog from catalog/seed/catalog.json"

    def add_arguments(self, parser):
        parser.add_argument("--file", default=None, help="Path to catalog JSON")
        parser.add_argument("--no-activate", action="store_true", help="Do not mark this version active")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["file"]) if opts["file"] else Path(__file__).resolve().parents[2] / "seed" / "catalog.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        version = data["version"]

        fv, _ = FormVersion.objects.update_or_create(version=version)

        seen_questions = []
        for q in data["questions"]:
            question, _ = Question.objects.update_or_create(
                form_version=fv,
                code=q["code"],
                defaults=dict(
                    type=q["type"],
                    screen=q.get("screen", ""),
                    order=q.get("order", 0),
                    required=q.get("required", False),
                    max_select=q.get("max_select"),
                    has_other=q.get("has_other", False),
                    label_en=q.get("label_en", ""),
                    label_ar=q.get("label_ar", ""),
                    help_en=q.get("help_en", ""),
                    help_ar=q.get("help_ar", ""),
                ),
            )
            seen_questions.append(question.id)

            seen_options = []
            for o in q.get("options", []):
                opt, _ = Option.objects.update_or_create(
                    question=question,
                    code=o["code"],
                    defaults=dict(
                        order=o.get("order", 0),
                        label_en=o.get("label_en", ""),
                        label_ar=o.get("label_ar", ""),
                    ),
                )
                seen_options.append(opt.id)
            question.options.exclude(id__in=seen_options).delete()

        fv.questions.exclude(id__in=seen_questions).delete()

        if not opts["no_activate"]:
            FormVersion.objects.exclude(pk=fv.pk).update(is_active=False)
            fv.is_active = True
            fv.save(update_fields=["is_active"])

        self.stdout.write(self.style.SUCCESS(
            f"Seeded catalog '{version}': {len(seen_questions)} questions"
            f"{' (active)' if not opts['no_activate'] else ''}."
        ))
