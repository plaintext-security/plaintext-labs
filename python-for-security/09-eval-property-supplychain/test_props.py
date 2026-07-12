"""Property tests — fuzz the validator to prove it rejects ALL malformed input.

Example-based tests check the cases you thought of; hypothesis generates thousands
you didn't. The invariant: any string that isn't a valid IP must raise ValidationError.
"""
import ipaddress
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))
from sift.classify import Indicator


def _is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


@given(st.text())
def test_non_ip_strings_are_rejected(s):
    if not _is_ip(s):
        with pytest.raises(ValidationError):
            Indicator(value=s)


@given(st.ip_addresses().map(str))
def test_valid_ips_are_accepted(ip):
    assert Indicator(value=ip).value == ip
