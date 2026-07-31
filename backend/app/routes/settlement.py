"""POST /api/settlement — thin glue: Pydantic validation -> settle.py -> JSON."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.models.game import (
    SettlementRequest,
    reconciliation_failure_to_response,
    settlement_success_to_response,
)
from app.services.settle import ReconciliationFailure, compute_settlement

settlement_bp = Blueprint("settlement", __name__)


def _format_validation_error(exc: ValidationError) -> str:
    first_error = exc.errors()[0]
    field = ".".join(str(part) for part in first_error["loc"])
    return f"{field}: {first_error['msg']}" if field else first_error["msg"]


@settlement_bp.route("/api/settlement", methods=["POST"])
def settlement():
    payload = request.get_json(silent=True)
    if payload is None:
        return (
            jsonify({"error": "invalid_input", "message": "Request body must be valid JSON."}),
            400,
        )

    try:
        settlement_request = SettlementRequest.model_validate(payload)
    except ValidationError as exc:
        return (
            jsonify({"error": "invalid_input", "message": _format_validation_error(exc)}),
            400,
        )

    result = compute_settlement(settlement_request.to_domain_players())

    if isinstance(result, ReconciliationFailure):
        response = reconciliation_failure_to_response(result)
        return jsonify(response.model_dump()), 422

    response = settlement_success_to_response(result)
    return jsonify(response.model_dump(by_alias=True)), 200
