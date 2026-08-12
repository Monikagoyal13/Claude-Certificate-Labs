"""Tests for northpeak.pricing."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from northpeak.pricing import gift_wrap_fee, member_discount, order_total, shipping_cost


def test_member_discount_applies_ten_percent_for_members():
    assert member_discount(100.0, is_member=True) == 10.0


def test_member_discount_is_zero_for_non_members():
    assert member_discount(100.0, is_member=False) == 0.0


def test_shipping_is_free_at_and_above_the_threshold_but_charged_below_it():
    assert shipping_cost(75.0) == 0.0
    assert shipping_cost(74.99) == 6.99


def test_order_total_combines_discount_and_shipping_correctly():
    assert order_total([50.0, 30.0], is_member=True) == 78.99
    assert order_total([50.0, 30.0], is_member=False) == 80.0


def test_gift_wrap_fee_charges_per_item_and_is_zero_for_no_items():
    assert gift_wrap_fee(0) == 0.0
    assert gift_wrap_fee(3) == 7.50


def test_gift_wrap_fee_rejects_a_negative_item_count():
    with pytest.raises(ValueError):
        gift_wrap_fee(-1)
