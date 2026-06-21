"""Internal dashboard API: submissions list/detail, analytics, export.
All endpoints are JWT-authenticated and staff-only."""
import csv
from collections import Counter, defaultdict

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.services import get_active_version, resolve_maps
from onboarding.models import Answer, Invitation, Submission
from partners.models import Partner

from .serializers import SubmissionListSerializer

PARTNER_TEXT = ("full_name", "email", "mobile", "based_in", "linkedin")
PARTNER_CHOICE = ("honorific", "nationality")


def _option(option_labels, qcode, ocode):
    lab = option_labels.get((qcode, ocode), {})
    return {"code": ocode, "en": lab.get("en", ocode), "ar": lab.get("ar", ocode)}


def _build_detail(submission):
    fv = submission.form_version or get_active_version()
    questions, option_labels = resolve_maps(fv) if fv else ({}, {})
    p = submission.partner

    rows_by_q = defaultdict(list)
    for a in submission.answers.all():
        rows_by_q[a.question_code].append(a)

    answers = []
    for code, q in sorted(questions.items(), key=lambda kv: kv[1].order):
        entry = {"code": code, "screen": q.screen, "type": q.type,
                 "label_en": q.label_en, "label_ar": q.label_ar, "values": []}
        if code in PARTNER_CHOICE:
            v = getattr(p, code)
            if v:
                entry["values"] = [_option(option_labels, code, v)]
        elif code in PARTNER_TEXT:
            v = getattr(p, code)
            if v:
                entry["values"] = [{"text": v}]
        else:
            for r in sorted(rows_by_q.get(code, []), key=lambda r: (r.rank or 0, r.id)):
                if r.option_code:
                    val = _option(option_labels, code, r.option_code)
                    if r.rank:
                        val["rank"] = r.rank
                    if r.other_text:
                        val["other"] = r.other_text
                    entry["values"].append(val)
                elif r.text_value:
                    entry["values"].append({"text": r.text_value})
        answers.append(entry)

    return {
        "id": submission.id,
        "reference": submission.reference,
        "status": submission.status,
        "locale": submission.locale,
        "submitted_at": submission.submitted_at,
        "partner": {
            "full_name": p.full_name,
            "email": p.email,
            "mobile": p.mobile,
            "based_in": p.based_in,
            "linkedin": p.linkedin,
            "honorific": _option(option_labels, "honorific", p.honorific) if p.honorific else None,
            "nationality": _option(option_labels, "nationality", p.nationality) if p.nationality else None,
        },
        "acknowledgments": {"ack_intro": submission.ack_intro, "ack_consent": submission.ack_consent},
        "answers": answers,
        "raw_payload": submission.raw_payload,
    }


class SubmissionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = SubmissionListSerializer
    queryset = Submission.objects.select_related("partner").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "locale", "partner__nationality"]
    search_fields = ["reference", "partner__full_name", "partner__email"]
    ordering_fields = ["submitted_at", "status"]
    ordering = ["-submitted_at"]


class SubmissionDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        try:
            sub = (Submission.objects
                   .select_related("partner", "form_version")
                   .prefetch_related("answers")
                   .get(pk=pk))
        except Submission.DoesNotExist:
            raise Http404
        return Response(_build_detail(sub))


class AnalyticsOverviewView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        by_status = {r["status"]: r["n"] for r in Submission.objects.values("status").annotate(n=Count("id"))}
        inv_status = {r["status"]: r["n"] for r in Invitation.objects.values("status").annotate(n=Count("id"))}
        trend = (Submission.objects.annotate(d=TruncDate("submitted_at"))
                 .values("d").annotate(n=Count("id")).order_by("d"))
        invited = Invitation.objects.count()
        return Response({
            "totals": {
                "submissions": Submission.objects.count(),
                "partners": Partner.objects.count(),
                "invitations": invited,
            },
            "by_status": by_status,
            "funnel": {
                "invited": invited,
                "opened": inv_status.get("opened", 0) + inv_status.get("submitted", 0),
                "submitted": inv_status.get("submitted", 0),
            },
            "trend": [{"date": str(t["d"]), "count": t["n"]} for t in trend],
        })


class AnalyticsDistributionsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        fv = get_active_version()
        if fv is None:
            return Response({"questions": []})
        questions, _labels = resolve_maps(fv)

        answer_counts = defaultdict(Counter)
        for row in Answer.objects.exclude(option_code="").values("question_code", "option_code").annotate(n=Count("id")):
            answer_counts[row["question_code"]][row["option_code"]] = row["n"]

        partner_counts = {
            "nationality": Counter({r["nationality"]: r["n"] for r in Partner.objects.exclude(nationality="").values("nationality").annotate(n=Count("id"))}),
            "honorific": Counter({r["honorific"]: r["n"] for r in Partner.objects.exclude(honorific="").values("honorific").annotate(n=Count("id"))}),
        }

        out = []
        for code, q in sorted(questions.items(), key=lambda kv: kv[1].order):
            if not q.is_choice:
                continue
            counts = partner_counts.get(code) if code in partner_counts else answer_counts.get(code, Counter())
            options = []
            for o in q.options.all():
                options.append({"code": o.code, "label_en": o.label_en, "label_ar": o.label_ar, "count": counts.get(o.code, 0)})
            if q.type == "country":
                options = sorted([o for o in options if o["count"] > 0], key=lambda o: -o["count"])
            out.append({
                "code": code, "screen": q.screen, "type": q.type,
                "label_en": q.label_en, "label_ar": q.label_ar,
                "total_responses": sum(counts.values()),
                "options": options,
            })
        return Response({"questions": out})


class SubmissionExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        fv = get_active_version()
        questions, option_labels = resolve_maps(fv) if fv else ({}, {})
        ordered = sorted(questions.values(), key=lambda q: q.order)

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="bnp-house-submissions.csv"'
        writer = csv.writer(resp)

        base_cols = ["reference", "submitted_at", "status", "locale"]
        q_cols = [q.code for q in ordered]
        writer.writerow(base_cols + [q.label_en or q.code for q in ordered])

        for sub in (Submission.objects.select_related("partner").prefetch_related("answers").all()):
            detail = _build_detail(sub)
            answer_by_code = {a["code"]: a for a in detail["answers"]}
            row = [sub.reference, sub.submitted_at.isoformat(), sub.status, sub.locale]
            for code in q_cols:
                a = answer_by_code.get(code, {"values": []})
                parts = []
                for v in a["values"]:
                    if "text" in v:
                        parts.append(v["text"])
                    else:
                        parts.append(v.get("en", v.get("code", "")))
                row.append(" | ".join(parts))
            writer.writerow(row)
        return resp
