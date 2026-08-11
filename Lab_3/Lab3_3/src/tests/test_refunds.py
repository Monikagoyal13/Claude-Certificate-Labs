"""Tests for northpeak.refunds."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from northpeak.refunds import refund_amount, within_return_window


def test_within_return_window_is_true_at_and_before_the_30_day_boundary():
    assert within_return_window(0) is True
    assert within_return_window(30) is True


def test_within_return_window_is_false_after_the_30_day_boundary():
    assert within_return_window(31) is False


def test_within_return_window_rejects_a_negative_days_value():
    with pytest.raises(ValueError):
        within_return_window(-1)


def test_refund_amount_returns_full_price_within_the_window():
    assert refund_amount(100.0, 10) == 100.0


def test_refund_amount_returns_zero_outside_the_window():
    assert refund_amount(100.0, 45) == 0.0


def test_refund_amount_rejects_a_negative_price():
    with pytest.raises(ValueError):
        refund_amount(-1.0, 10)
