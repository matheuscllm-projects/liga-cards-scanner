"""Testes para src/pricing/margin.py."""
import pytest

from src.pricing.margin import (
    MIN_MARGIN_PERCENT,
    MIN_PRICE_BRL,
    calculate_margin,
    calculate_roi,
    is_approved,
)


class TestCalculateMargin:
    """Margem sobre a VENDA = (ref - compra)/ref; ROI = (ref - compra)/compra."""

    # (compra, ref, margem_venda %, roi %, passa no corte de 30)
    GOLDEN = [
        (75.0, 100.0, 25.0, 33.33, False),
        (70.0, 100.0, 30.0, 42.86, True),   # fronteira
        (100.0, 80.0, -25.0, -20.0, False),
    ]

    @pytest.mark.parametrize("compra,ref,margem,roi,passa", GOLDEN)
    def test_golden_cases(self, compra, ref, margem, roi, passa):
        m = calculate_margin(compra, ref)
        assert m == pytest.approx(margem, abs=0.005)
        assert calculate_roi(compra, ref) == pytest.approx(roi, abs=0.005)
        assert (m >= MIN_MARGIN_PERCENT) is passa

    def test_zero_margin_when_prices_equal(self):
        assert calculate_margin(100.0, 100.0) == 0.0

    @pytest.mark.parametrize("compra,ref", [(0, 100), (-10, 100), (100, 0), (100, -5)])
    def test_none_when_non_positive(self, compra, ref):
        assert calculate_margin(compra, ref) is None
        assert calculate_roi(compra, ref) is None


class TestIsApproved:
    def test_approved_when_above_both_thresholds(self):
        assert is_approved(price_liga_brl=100.0, margin_percent=35.0) is True

    def test_rejected_when_margin_below_threshold(self):
        assert is_approved(price_liga_brl=100.0, margin_percent=20.0) is False

    def test_rejected_when_price_below_threshold(self):
        # Margem boa mas preço abaixo de R$50
        assert is_approved(price_liga_brl=45.0, margin_percent=40.0) is False

    def test_approved_exactly_at_thresholds(self):
        assert (
            is_approved(
                price_liga_brl=MIN_PRICE_BRL, margin_percent=MIN_MARGIN_PERCENT
            )
            is True
        )

    def test_rejected_just_below_price_threshold(self):
        assert is_approved(price_liga_brl=49.99, margin_percent=100.0) is False

    def test_rejected_just_below_margin_threshold(self):
        assert is_approved(price_liga_brl=1000.0, margin_percent=29.99) is False

    def test_custom_thresholds(self):
        # Critérios mais agressivos: preço >= 100, margem >= 50
        assert (
            is_approved(80.0, 60.0, min_price=100.0, min_margin=50.0) is False
        )
        assert (
            is_approved(120.0, 60.0, min_price=100.0, min_margin=50.0) is True
        )

    def test_default_thresholds_match_business_rules(self):
        assert MIN_PRICE_BRL == 50.0
        assert MIN_MARGIN_PERCENT == 30.0
