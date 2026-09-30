from __future__ import annotations

from collections import Counter

import httpx

from nist_gas_srm.client import crud
from nist_gas_srm.core import basemodels

FASTAPI_URL = "http://127.0.0.1:8000"

TABLEGROUP_DBNAMES_TABLENAMES_MAPPING = {
    "Measurements": {
        "measurements.ratios": "Ratio data",
        "measurements.vendors": "Vendor data",
        "measurements.standards": "Standards",
        "measurements.ratio_analysis_random_effects": "Ratio analysis",
        "measurements.ratio_analysis_fixed_effects": "Ratio analysis fixed effects",
        "measurements.past_lot_standards": "Past lot standards",
        "measurements.additional_lot_standards": "Additional lot standards",
    },
    "Standard Analysis": {
        "standard_analysis.params": "Parameters",
        "standard_analysis.genline_params": "StandardAnalysisGenLine parameters",
        "standard_analysis.genline_solution": "StandardAnalysisGenLine solution",
        "standard_analysis.genline_eval": "StandardAnalysisGenLine evaluation",
    },
    "RCertification": {
        "rcert.srm_values": "SRM values",
        "rcert.standards_values": "Standards values",
        "rcert.additional_lot_standards": "Certified additional lot standards",
        "rcert.cylinder_results": "Cylinder results",
        "rcert.analysis_function_coefficients": "Analysis function coefficients",
        "rcert.correlation_coefficients": "Correlation coefficients",
        "rcert.outliers": "RCertOutliers",
    },
}


def get_srm_string_id(
    srm_id: int, batch_id: str | None = None, lot_id: str | None = None
) -> str:
    return f"{srm_id}{batch_id or ''}{'-' + lot_id if lot_id else ''}"


def get_all_srms(include_subtypes: bool = True) -> list[str]:
    with httpx.Client(base_url=FASTAPI_URL) as client:
        response = crud.get_srms(client)
    models = [basemodels.srm.SRMPublic.model_validate(x) for x in response.json()]

    out = {model.srm_string_id for model in models}

    if include_subtypes:
        # which srm_id is repeated?
        for value, count in Counter(str(model.srm_id) for model in models).items():
            if count > 1:
                out.add(value)

        # which srm + batch is repeated
        for value, count in Counter(
            get_srm_string_id(model.srm_id, model.batch_id) for model in models
        ).items():
            if count > 1:
                out.add(value)

        # which srm + lot is repeated
        for value, count in Counter(
            get_srm_string_id(model.srm_id, lot_id=model.lot_id) for model in models
        ).items():
            if count > 1:
                out.add(value)

    return sorted(out)
