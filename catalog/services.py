"""Helpers to read the active catalog for validation and EN/AR label resolution."""
from .models import FormVersion


def get_active_version():
    return FormVersion.active()


def question_map(form_version):
    """{code: Question} with options prefetched."""
    return {q.code: q for q in form_version.questions.prefetch_related("options").all()}


def resolve_maps(form_version):
    """Return (questions_by_code, option_labels) where option_labels maps
    (question_code, option_code) -> {"en": ..., "ar": ...}."""
    questions = {}
    options = {}
    for q in form_version.questions.prefetch_related("options").all():
        questions[q.code] = q
        for o in q.options.all():
            options[(q.code, o.code)] = {"en": o.label_en, "ar": o.label_ar}
    return questions, options
