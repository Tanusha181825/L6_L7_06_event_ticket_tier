import pytest
from event_ticket_tier import process_ticket_manifest, monitor_gate_flow


def test_general_ticket_with_tax():
    manifests = [{"is_confirmed": True, "tier": "general", "orders": [{"qty": 2}]}]
    assert process_ticket_manifest(manifests, 0.10) == {"total_revenue": 99.0, "status": "COMPLETED"}


def test_vip_earlybird_with_lounge():
    manifests = [{"is_confirmed": True, "tier": "vip", "exclusive_lounge": True,
                  "orders": [{"qty": 2, "promo": "EARLYBIRD"}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 315.0, "status": "COMPLETED"}


def test_premium_bulk_discount():
    manifests = [{"is_confirmed": True, "tier": "premium", "orders": [{"qty": 5}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 430.0, "status": "COMPLETED"}


def test_unconfirmed_and_unknown_tier():
    manifests = [{"is_confirmed": False, "tier": "general", "orders": [{"qty": 3}]},
                 {"is_confirmed": True, "tier": "balcony", "orders": [{"qty": 1}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_invalid_quantity():
    manifests = [{"is_confirmed": True, "tier": "general", "orders": [{"qty": 0}, {"qty": 1}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 45.0, "status": "COMPLETED"}


def test_vip_fraud_cancels_manifest():
    manifests = [{"is_confirmed": True, "tier": "vip", "orders": [
        {"qty": 2}, {"qty": 1, "promo": "FRAUD_RISK"}, {"qty": 4}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_non_vip_fraud_still_counts_price():
    manifests = [{"is_confirmed": True, "tier": "premium", "orders": [{"qty": 1, "promo": "FRAUD_RISK"}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 90.0, "status": "COMPLETED"}


def test_audit_rejected_after_five_bad_orders():
    manifests = [{"is_confirmed": True, "tier": "general", "orders": [{"qty": -1}] * 5}]
    assert process_ticket_manifest(manifests, 0.1) == {"total_revenue": 0.0, "status": "AUDIT_REJECTED"}


@pytest.mark.parametrize("manifests,tax", [("wrong", 0.1), ([], -0.1)])
def test_bad_input_raises_error(manifests, tax):
    with pytest.raises(ValueError):
        process_ticket_manifest(manifests, tax)


def test_gate_no_data():
    assert monitor_gate_flow([]) == "NO_DATA"


def test_gate_normal_with_reset():
    assert monitor_gate_flow([[51, 50, 55], [20, 40]]) == "FLOW_NORMAL"


def test_gate_overflow():
    assert monitor_gate_flow([[20], [51, 52]]) == "OVERFLOW"



def test_general_default_tier_and_empty_orders():
    assert process_ticket_manifest([{"is_confirmed": True}], 0) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


def test_bulk_discount_boundary_and_default_promo():
    manifests = [{"is_confirmed": True, "tier": "general", "orders": [{"qty": 4}, {"qty": 5}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 385.0, "status": "COMPLETED"}


def test_fraud_on_general_does_not_break():
    manifests = [{"is_confirmed": True, "tier": "general", "orders": [
        {"qty": 1, "promo": "FRAUD_RISK"}, {"qty": 1, "promo": "EARLYBIRD"}]}]
    assert process_ticket_manifest(manifests, 0) == {"total_revenue": 81.0, "status": "COMPLETED"}


def test_gate_exact_threshold():
    assert monitor_gate_flow([[50, 50, 50], []]) == "FLOW_NORMAL"
