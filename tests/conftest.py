"""
FILE:      tests/conftest.py
CREATED:   2026-11-05 07:08 +03
TASK:      int-testnumber (Boss 2026-11-05 00:33)
AUTHOR:    M Alhassoun
WHAT:      Shared pytest fixtures: the test phone number and its format variants.
WHY:       Tests must not hardcode a phone number. The number comes from the
           KWTSMS_TEST_NUMBER environment variable (an international Kuwait
           mobile, digits only, e.g. 965XXXXXXXX) and every test that needs one
           is skipped when it is unset.
USAGE:     KWTSMS_TEST_NUMBER=965XXXXXXXX pytest tests/
           CI reads it from the repository secret of the same name.
DEPENDS:   pytest
"""
import os

import pytest

_ARABIC_INDIC = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_PERSIAN = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_arabic_indic(digits: str) -> str:
    """2026-11-05 07:08 +03: Latin digits to Arabic-Indic (U+0660-0669), for normalization tests (int-testnumber)."""
    return digits.translate(_ARABIC_INDIC)


def to_persian(digits: str) -> str:
    """2026-11-05 07:08 +03: Latin digits to Extended Arabic-Indic (U+06F0-06F9), for normalization tests (int-testnumber)."""
    return digits.translate(_PERSIAN)


@pytest.fixture
def num() -> str:
    """2026-11-05 07:08 +03: the test number from KWTSMS_TEST_NUMBER; skip when unset (int-testnumber)."""
    n = os.environ.get("KWTSMS_TEST_NUMBER", "").strip()
    if not n.isdigit() or not n.startswith("965") or len(n) != 11:
        pytest.skip("KWTSMS_TEST_NUMBER not set (digits only, 965 plus 8 digits)")
    return n
