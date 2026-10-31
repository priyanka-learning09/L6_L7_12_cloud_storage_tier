
import pytest
from cloud_storage_tier import (
    process_storage_tenants,
    monitor_replication_latency
)


# Test 1: Invalid tenants input
def test_invalid_tenants():
    with pytest.raises(ValueError):
        process_storage_tenants("invalid", 10)


# Test 2: Negative support fee
def test_negative_support_fee():
    with pytest.raises(ValueError):
        process_storage_tenants([], -5)


# Test 3: Hot storage tier
def test_hot_tier():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100, "egress_gb": 50}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 2.5


# Test 4: Cool storage tier
def test_cool_tier():
    tenants = [{
        "account_active": True,
        "tier": "cool",
        "buckets": [{"size_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 1.5


# Test 5: Archive storage tier
def test_archive_tier():
    tenants = [{
        "account_active": True,
        "tier": "archive",
        "buckets": [{"size_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 0.5


# Test 6: Invalid storage tier
def test_invalid_tier():
    tenants = [{
        "account_active": True,
        "tier": "unknown",
        "buckets": [{"size_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 0


# Test 7: Inactive tenant
def test_inactive_tenant():
    tenants = [{"account_active": False}]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# Test 8: Missing account status
def test_missing_account_active():
    tenants = [{"tier": "hot", "buckets": []}]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# Test 9: Zero-size bucket
def test_zero_size_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 0}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# Test 10: Negative-size bucket
def test_negative_size_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": -10}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# Test 11: Corrupted bucket
def test_corrupted_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100, "corrupted": True}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["status"] == "ZERO_USAGE"


# Test 12: Large bucket
def test_large_bucket():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 600}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 13.5


# Test 13: Normal bucket boundary
def test_normal_bucket_boundary():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 500}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 12.5


# Test 14: High egress
def test_high_egress():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100, "egress_gb": 150}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 6.5


# Test 15: Normal egress boundary
def test_normal_egress_boundary():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "buckets": [{"size_gb": 100, "egress_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 2.5


# Test 16: Backup vault
def test_backup_vault():
    tenants = [{
        "account_active": True,
        "tier": "hot",
        "has_backup_vault": True,
        "buckets": [{"size_gb": 100}]
    }]
    result = process_storage_tenants(tenants, 10)
    assert result["total_billed"] == 12.5


# Test 17: Empty tenants
def test_empty_tenants():
    result = process_storage_tenants([], 10)
    assert result["status"] == "ZERO_USAGE"


# Test 18: No replication data
def test_no_replication_data():
    assert monitor_replication_latency([]) == "NO_DATA"


# Test 19: Replication synced
def test_replication_synced():
    assert monitor_replication_latency([[100, 150, 180]]) == "SYNCED"


# Test 20: Replication alert
def test_replication_alert():
    assert monitor_replication_latency([[250, 300]]) == "SYNC_LAG_ALERT"


# Test 21: Replication lag reset
def test_replication_lag_reset():
    assert monitor_replication_latency([[250, 100, 250]]) == "SYNCED"
