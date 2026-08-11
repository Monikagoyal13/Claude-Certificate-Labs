"""Tests for orders.service."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orders.service import place_order


def test_place_order_returns_item_count_for_a_valid_token():
    result = place_order("npk_live_abcdef123456", [{"sku": "A"}, {"sku": "B"}])
    assert result["count"] == 2


def test_place_order_rejects_an_invalid_token():
    with pytest.raises(PermissionError):
        place_order("bad", [{"sku": "A"}])
