from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import skfuzzy.control as ctrl

from backend.fuzzy_engine.diagnosis_engine import (
    DISEASE_ENGINES,
    DISEASE_NAMES,
    classify_severity,
    rank_diseases,
)
from backend.fuzzy_engine.recommendations import get_patient_advice
from backend.fuzzy_engine.risk_engine import analyze_risk


SYMPTOM_FIELDS = (
    "pain",
    "redness",
    "vision_blur",
    "dryness",
    "itching",
    "tearing",
    "discharge",
    "photophobia",
    "halos",
    "headache",
    "nausea",
    "floaters",
    "vision_loss",
    "peripheral_loss",
    "burning",
    "foreign_body",
    "eye_fatigue",
)

BINARY_FIELDS = (
    "contact_lens",
    "diabetes",
    "hypertension",
    "family_glaucoma",
    "previous_surgery",
    "eye_trauma",
    "smoking",
)

REQUIRED_FIELDS = (
    "age",
    *SYMPTOM_FIELDS,
    "screen_time",
    *BINARY_FIELDS,
)

EXPECTED_DISEASES = {
    "glaucoma",
    "cataract",
    "dry_eye",
    "conjunctivitis",
    "keratitis",
    "uveitis",
    "retinopathy",
    "computer_vision",
}


class FuzzyAssessmentError(RuntimeError):
    """Raised only when fuzzy inference genuinely fails."""


@dataclass(frozen=True)
class FuzzyAssessmentResult:
    score: float
    risk_level: str
    recommendation: str
    primary_finding: str
    confidence: float
    details_json: str


def _as_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        return float(int(value))

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for {field}.") from exc


def _validate_answers(
    answers: dict[str, Any],
) -> dict[str, float]:
    if not isinstance(answers, dict):
        raise ValueError(
            "Assessment answers must be an object."
        )

    missing = [
        field
        for field in REQUIRED_FIELDS
        if field not in answers
    ]

    if missing:
        raise ValueError(
            "Missing required assessment fields: "
            + ", ".join(missing)
        )

    data: dict[str, float] = {}

    age = _as_number(
        answers["age"],
        "age",
    )

    if not 0 <= age <= 100:
        raise ValueError(
            "Age must be between 0 and 100."
        )

    data["age"] = age

    for field in SYMPTOM_FIELDS:
        value = _as_number(
            answers[field],
            field,
        )

        if not 0 <= value <= 10:
            raise ValueError(
                f"{field} must be between 0 and 10."
            )

        data[field] = value

    screen_time = _as_number(
        answers["screen_time"],
        "screen_time",
    )

    if not 0 <= screen_time <= 12:
        raise ValueError(
            "screen_time must be between 0 and 12."
        )

    data["screen_time"] = screen_time

    for field in BINARY_FIELDS:
        value = _as_number(
            answers[field],
            field,
        )

        if value not in {0.0, 1.0}:
            raise ValueError(
                f"{field} must be 0 or 1."
            )

        data[field] = value

    return data


def _friendly_disease_name(
    name: str,
) -> str:
    raw = DISEASE_NAMES.get(
        name,
        name,
    )

    return raw.split(
        " - ",
        1,
    )[0].strip()


def _risk_label(
    source_level: str,
) -> str:
    mapping = {
        "Safe": "Low Concern",
        "Warning": "Review Recommended",
        "Danger": "Prompt Eye Review Recommended",
    }

    return mapping.get(
        source_level,
        "Review Recommended",
    )


def _summary_recommendation(
    source_level: str,
    recommendations: list[dict[str, Any]],
) -> str:
    for item in recommendations:
        message = item.get("message")
        if message:
            return str(message)

    for item in recommendations:
        warning = item.get("warning")
        if warning:
            return str(warning)

    if source_level == "Safe":
        return (
            "No high-risk overall symptom pattern was identified by this "
            "assessment. Seek eye-care review if symptoms persist, worsen, "
            "or cause concern."
        )

    return (
        "An ophthalmology review is recommended."
    )


def _run_one_engine(
    disease: str,
    patient_data: dict[str, float],
) -> tuple[float, str]:
    """
    Execute one disease engine with explicit production semantics.

    scikit-fuzzy may successfully compute a ControlSystem while returning no
    consequent when none of that engine's rules fires. The original source
    converted that situation to 0.0 through a caught KeyError. We preserve
    that intended numeric behavior, but distinguish it from a genuine engine
    exception.

    Returns:
        (score, status)

        status == "evaluated":
            at least one rule produced the requested consequent.

        status == "no_rule_activation":
            computation succeeded, but no rule produced a consequent.
            This is represented as 0.0, matching the original system's
            effective output.

    Genuine compute failures raise FuzzyAssessmentError.
    """
    try:
        system, output_variable = (
            DISEASE_ENGINES[disease]
        )
    except KeyError as exc:
        raise FuzzyAssessmentError(
            f"Unknown fuzzy disease engine: {disease}"
        ) from exc

    simulation = ctrl.ControlSystemSimulation(
        system
    )

    try:
        accepted_inputs = {
            antecedent.label
            for antecedent in system.antecedents
        }
    except Exception as exc:
        raise FuzzyAssessmentError(
            f"Could not inspect inputs for {disease}."
        ) from exc

    missing_inputs = (
        accepted_inputs
        - patient_data.keys()
    )

    if missing_inputs:
        raise FuzzyAssessmentError(
            f"Missing fuzzy inputs for {disease}: "
            + ", ".join(sorted(missing_inputs))
        )

    try:
        for label in accepted_inputs:
            simulation.input[label] = (
                patient_data[label]
            )

        simulation.compute()

    except Exception as exc:
        raise FuzzyAssessmentError(
            f"Fuzzy computation failed for {disease}."
        ) from exc

    output_label = output_variable.label

    if output_label not in simulation.output:
        return 0.0, "no_rule_activation"

    try:
        score = float(
            simulation.output[output_label]
        )
    except (TypeError, ValueError) as exc:
        raise FuzzyAssessmentError(
            f"Invalid fuzzy output for {disease}."
        ) from exc

    if not 0.0 <= score <= 100.0:
        raise FuzzyAssessmentError(
            f"Out-of-range fuzzy output for {disease}: {score}"
        )

    return round(score, 2), "evaluated"


def _run_all_engines(
    patient_data: dict[str, float],
) -> tuple[
    dict[str, float],
    dict[str, str],
]:
    if set(DISEASE_ENGINES) != EXPECTED_DISEASES:
        raise FuzzyAssessmentError(
            "Unexpected fuzzy-engine set."
        )

    scores: dict[str, float] = {}
    statuses: dict[str, str] = {}

    for disease in DISEASE_ENGINES:
        score, status = _run_one_engine(
            disease,
            patient_data,
        )

        scores[disease] = score
        statuses[disease] = status

    return scores, statuses


def assess_eye_health(
    answers: dict[str, Any],
) -> FuzzyAssessmentResult:
    patient_data = _validate_answers(
        answers
    )

    disease_scores, engine_status = (
        _run_all_engines(
            patient_data
        )
    )

    risk_analysis = analyze_risk(
        disease_scores
    )

    source_risk_level = str(
        risk_analysis["risk_level"]
    )

    risk_score = float(
        risk_analysis["risk_score"]
    )

    if not 0.0 <= risk_score <= 100.0:
        raise FuzzyAssessmentError(
            "The overall fuzzy risk score is out of range."
        )

    advice = get_patient_advice(
        disease_scores,
        {
            "risk_level": source_risk_level,
            "risk_score": risk_score,
        },
    )

    recommendations = list(
        advice.get("recommendations")
        or []
    )

    recommendation = (
        _summary_recommendation(
            source_risk_level,
            recommendations,
        )
    )

    ranked = rank_diseases(
        disease_scores
    )

    non_zero_ranked = [
        (disease, float(score))
        for disease, score in ranked
        if float(score) > 0.0
    ]

    if non_zero_ranked:
        primary_key, primary_score = (
            non_zero_ranked[0]
        )

        primary_finding = (
            _friendly_disease_name(
                primary_key
            )
        )

        severity = classify_severity(
            primary_score
        )

    else:
        primary_key = None
        primary_score = 0.0
        primary_finding = (
            "No dominant pattern"
        )
        severity = "Very Low"

    readable_scores = {
        _friendly_disease_name(
            disease
        ): float(score)
        for disease, score in ranked
    }

    readable_causes = []

    for item in (
        risk_analysis.get("causes")
        or []
    ):
        readable_causes.append(
            {
                "finding":
                    _friendly_disease_name(
                        str(
                            item["disease"]
                        )
                    ),
                "score":
                    float(
                        item["probability"]
                    ),
            }
        )

    details = {
        "assessment_engine":
            "eye_health_rules_v1",

        "source_risk_level":
            source_risk_level,

        "risk_score":
            risk_score,

        "primary_finding":
            primary_finding,

        "primary_score":
            primary_score,

        "severity":
            severity,

        "assessment_scores":
            readable_scores,

        "risk_causes":
            readable_causes,

        # Stored for auditability; not exposed as technical UI text.
        "engine_status":
            engine_status,

        "recommendations":
            recommendations,
    }

    return FuzzyAssessmentResult(
        score=round(
            risk_score,
            2,
        ),

        risk_level=_risk_label(
            source_risk_level
        ),

        recommendation=(
            recommendation
        ),

        primary_finding=(
            primary_finding
        ),

        confidence=round(
            primary_score,
            2,
        ),

        details_json=json.dumps(
            details,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )
