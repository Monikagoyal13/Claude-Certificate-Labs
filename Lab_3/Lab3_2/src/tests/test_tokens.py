"""Tests for auth.tokens."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth.tokens import verify_token


def test_verify_token_accepts_a_valid_live_token():
    assert verify_token("npk_live_abcdef123456") is True


def test_verify_token_rejects_a_short_or_malformed_token():
    assert verify_token("npk_live_short") is False
    assert verify_token("not_a_token_at_all_123456") is False
