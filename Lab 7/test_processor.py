from hypothesis import given, strategies as st
from processor import parse_storage_quota, compute_compression_ratio, lookup_bandwidth_tier_rate

@given(st.text() | st.none())
def test_parse_storage_quota_no_crash(s):
    # To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_compute_compression_ratio_safe(s):
    # To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_lookup_bandwidth_tier_rate_safe(s):
    # To-Do:Using try and except complete this function.
    pass