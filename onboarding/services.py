"""Validate an onboarding payload against the active catalog and persist it as
Partner + Submission + Answer rows. Server-side validation never trusts the
client: it re-checks required fields, valid option codes, max selections, email
format, the "Other" specify text, and the consent acknowledgments."""
import re

from django.db import transaction
from rest_framework import serializers

from catalog.services import get_active_version, question_map
from partners.models import Partner

from .models import Answer, Invitation, Submission

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# "Your details" screen → stored as Partner columns; everything else → Answers.
PARTNER_KEYS = {"full_name", "honorific", "email", "mobile", "based_in", "nationality", "linkedin"}
ACK_KEYS = ("ack_intro", "ack_consent")
CHOICE_SINGLE = {"single", "select", "country"}
CHOICE_MULTI = {"multi", "ordered"}


def _validate(payload, qmap):
    errors = {}
    for code, q in qmap.items():
        val = payload.get(code)
        if q.type in CHOICE_SINGLE:
            valid = {o.code for o in q.options.all()}
            if not val:
                if q.required:
                    errors[code] = "This field is required."
            elif val not in valid:
                errors[code] = f"'{val}' is not a valid option."
            elif q.has_other and val == "other" and not str(payload.get(f"{code}_other", "")).strip():
                errors[f"{code}_other"] = "Please specify."
        elif q.type in CHOICE_MULTI:
            lst = val if isinstance(val, list) else []
            valid = {o.code for o in q.options.all()}
            if q.required and not lst:
                errors[code] = "Select at least one."
            bad = [v for v in lst if v not in valid]
            if bad:
                errors[code] = f"Invalid option(s): {', '.join(map(str, bad))}."
            if q.max_select and len(lst) > q.max_select:
                errors[code] = f"Choose at most {q.max_select}."
            if q.has_other and "other" in lst and not str(payload.get(f"{code}_other", "")).strip():
                errors[f"{code}_other"] = "Please specify."
        else:  # text / email / tel / url
            s = val.strip() if isinstance(val, str) else ""
            if q.required and not s:
                errors[code] = "This field is required."
            if q.type == "email" and s and not EMAIL_RE.match(s):
                errors[code] = "Enter a valid email address."

    for ak in ACK_KEYS:
        if payload.get(ak) is not True:
            errors[ak] = "Acknowledgment required."
    return errors


@transaction.atomic
def create_submission(payload):
    if not isinstance(payload, dict):
        raise serializers.ValidationError("Invalid payload.")

    fv = get_active_version()
    if fv is None:
        raise serializers.ValidationError("No active form version. Seed the catalog first.")

    qmap = question_map(fv)
    errors = _validate(payload, qmap)
    if errors:
        raise serializers.ValidationError(errors)

    locale = payload.get("locale") or "en"

    partner = Partner.objects.create(
        full_name=str(payload.get("full_name", "")).strip(),
        honorific=payload.get("honorific") or "",
        email=str(payload.get("email", "")).strip(),
        mobile=str(payload.get("mobile", "")).strip(),
        based_in=str(payload.get("based_in", "")).strip(),
        nationality=payload.get("nationality") or "",
        linkedin=str(payload.get("linkedin", "")).strip(),
        locale=locale,
    )

    invitation = None
    token = payload.get("invitation_token")
    if token:
        invitation, _ = Invitation.objects.get_or_create(token=token, defaults={"locale": locale})
        invitation.status = Invitation.Status.SUBMITTED
        invitation.save(update_fields=["status"])

    submission = Submission.objects.create(
        partner=partner,
        invitation=invitation,
        form_version=fv,
        locale=locale,
        ack_intro=bool(payload.get("ack_intro")),
        ack_consent=bool(payload.get("ack_consent")),
        raw_payload=payload,
    )

    rows = []
    for code, q in qmap.items():
        if code in PARTNER_KEYS:
            continue
        val = payload.get(code)
        if q.type in CHOICE_MULTI:
            for i, ocode in enumerate(val if isinstance(val, list) else []):
                rows.append(Answer(
                    submission=submission,
                    question_code=code,
                    option_code=ocode,
                    rank=(i + 1) if q.type == "ordered" else None,
                    other_text=str(payload.get(f"{code}_other", "")).strip() if (q.has_other and ocode == "other") else "",
                ))
        elif q.type in CHOICE_SINGLE:
            if val:
                rows.append(Answer(
                    submission=submission,
                    question_code=code,
                    option_code=val,
                    other_text=str(payload.get(f"{code}_other", "")).strip() if (q.has_other and val == "other") else "",
                ))
        else:
            s = val.strip() if isinstance(val, str) else ""
            if s:
                rows.append(Answer(submission=submission, question_code=code, text_value=s))
    Answer.objects.bulk_create(rows)

    return submission
