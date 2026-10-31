
import pytest

from cloud_storage_tier import (
    process_storage_tenants,
    monitor_replication_latency
)


# 1. Invalid input conditions

def test_invalid_tenants_type():
    with pytest.raises(ValueError):
        process_storage_tenants("invalid", 10)


def test_negative_support_fee():
    with pytest.raises(ValueError):
        process_storage_tenants([], -10)


# 2. Empty and inactive tenants

def test_empty_tenant_list():
    result = process_storage_tenants([], 10)
    assert result["status"] == "ZERO_USAGE"


def test_inactive_tenant():
    tenants = [{"account_active": False}]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 3. All storage tiers

@pytest.mark.parametrize(
    "tier, expected",
    [
        ("hot", 2.5),
        ("cool", 1.5),
        ("archive", 0.5)
    ]
)
def test_storage_tiers(tier, expected):
    tenants = [{
        "account_active": True,
        "tier": tier,
        "buckets": [{"size_gb": 100}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == expected


def test_invalid_storage_tier():
    tenants = [{
        "account_active": True,
        "tier": "unknown",
        "buckets": [{"size_gb": 100}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 4. Bucket conditions

def test_empty_buckets():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": []
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


def test_zero_size_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 0}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


def test_negative_size_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": -10}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 5. Corrupted buckets

def test_corrupted_hot_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100, "corrupted": True}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


def test_corrupted_archive_bucket():
    tenants = [{
        "account_active": True,
        "tier": "archive",
        "buckets": [
            {"size_gb": 100, "corrupted": True},
            {"size_gb": 200}
        ]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# 6. Bucket size boundary

def test_bucket_size_above_500():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 600}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 13.5


def test_bucket_size_equal_to_500():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 500}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 12.5


# 7. Egress conditions

def test_egress_above_100():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{
            "size_gb": 100,
            "egress_gb": 150
        }]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 6.5


def test_egress_equal_to_100():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{
            "size_gb": 100,
            "egress_gb": 100
        }]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 2.5


# 8. Backup vault conditions

def test_backup_vault_enabled():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100}],
        "has_backup_vault": True
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 12.5


def test_backup_vault_disabled():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100}],
        "has_backup_vault": False
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 2.5


# 9. Audit flag condition

def test_audit_flagged():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 0} for _ in range(5)]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "AUDIT_FLAGGED"


def test_billed_status():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100}]
    }]

    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "BILLED"


# 10. Replication latency conditions

def test_no_replication_data():
    assert monitor_replication_latency([]) == "NO_DATA"


def test_empty_node_logs():
    assert monitor_replication_latency([[]]) == "SYNCED"


def test_single_high_latency():
    assert monitor_replication_latency([[250]]) == "SYNCED"


def test_latency_streak_reset():
    assert monitor_replication_latency([[250, 100, 250]]) == "SYNCED"


def test_replication_lag_alert():
    assert monitor_replication_latency([[250, 300]]) == "SYNC_LAG_ALERT"
