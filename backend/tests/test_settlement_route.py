import pytest

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def post_settlement(client, payload):
    return client.post("/api/settlement", json=payload)


def test_three_player_worked_example_returns_full_success_shape(client):
    payload = {
        "players": [
            {"name": "Nathan", "buy_in": 10.00, "final_balance": 12.50},
            {"name": "Jason", "buy_in": 20.00, "final_balance": 10.00},
            {"name": "Emily", "buy_in": 10.00, "final_balance": 17.50},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 200
    assert body["nets"] == [
        {"name": "Nathan", "net": 2.50},
        {"name": "Jason", "net": -10.00},
        {"name": "Emily", "net": 7.50},
    ]
    assert body["transactions"] == [
        {"from": "Jason", "to": "Emily", "amount": 7.50},
        {"from": "Jason", "to": "Nathan", "amount": 2.50},
    ]
    assert body["breakdown"]["debtors_sorted"] == [{"name": "Jason", "amount": 10.00}]
    assert body["breakdown"]["creditors_sorted"] == [
        {"name": "Emily", "amount": 7.50},
        {"name": "Nathan", "amount": 2.50},
    ]
    assert body["breakdown"]["match_trace"] == [
        "Jason (owes $10.00) pays Emily (owed $7.50) -> $7.50; "
        "Jason now owes $2.50, Emily settled",
        "Jason (owes $2.50) pays Nathan (owed $2.50) -> $2.50; "
        "Jason now owes $0.00, Nathan settled",
    ]
    assert body["breakdown"]["rounding_adjustment"] is None


def test_already_settled_all_zero_returns_empty_transactions(client):
    payload = {
        "players": [
            {"name": "A", "buy_in": 10.00, "final_balance": 10.00},
            {"name": "B", "buy_in": 5.00, "final_balance": 5.00},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 200
    assert body["transactions"] == []
    assert body["breakdown"]["debtors_sorted"] == []
    assert body["breakdown"]["creditors_sorted"] == []
    assert body["breakdown"]["match_trace"] == []


def test_mismatched_nets_returns_reconciliation_error(client):
    payload = {
        "players": [
            {"name": "Nathan", "buy_in": 10.00, "final_balance": 12.50},
            {"name": "Jason", "buy_in": 20.00, "final_balance": 10.01},
            {"name": "Emily", "buy_in": 10.00, "final_balance": 17.50},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 422
    assert body == {
        "error": "nets_do_not_reconcile",
        "total_buy_ins": 40.00,
        "total_final_balances": 40.01,
        "delta": 0.01,
        "message": (
            "Final balances exceed buy-ins by $0.01 — check entries for a data entry mistake."
        ),
    }


def test_duplicate_names_rejected_with_actionable_message(client):
    payload = {
        "players": [
            {"name": "Jason", "buy_in": 10.00, "final_balance": 10.00},
            {"name": "Jason", "buy_in": 10.00, "final_balance": 10.00},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"] == "invalid_input"
    assert "Jason" in body["message"]
    assert "duplicate" in body["message"].lower()


def test_negative_buy_in_rejected(client):
    payload = {
        "players": [
            {"name": "A", "buy_in": -5.00, "final_balance": 0.00},
            {"name": "B", "buy_in": 5.00, "final_balance": 0.00},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"] == "invalid_input"
    assert "buy_in" in body["message"]


def test_non_numeric_buy_in_rejected(client):
    payload = {
        "players": [
            {"name": "A", "buy_in": "not-a-number", "final_balance": 0.00},
            {"name": "B", "buy_in": 5.00, "final_balance": 0.00},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"] == "invalid_input"


def test_sub_cent_buy_in_rejected(client):
    payload = {
        "players": [
            {"name": "A", "buy_in": 10.001, "final_balance": 10.00},
            {"name": "B", "buy_in": 5.00, "final_balance": 5.00},
        ]
    }

    response = post_settlement(client, payload)
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"] == "invalid_input"
    assert "decimal places" in body["message"]


def test_fewer_than_two_players_rejected(client):
    payload = {"players": [{"name": "A", "buy_in": 10.00, "final_balance": 10.00}]}

    response = post_settlement(client, payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_input"


def test_malformed_json_body_rejected(client):
    response = client.post(
        "/api/settlement", data="not json at all", content_type="application/json"
    )
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"] == "invalid_input"


def test_missing_players_field_rejected(client):
    response = post_settlement(client, {})

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_input"
