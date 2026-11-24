"""Cálculo de margem de arbitragem e regras de aprovação."""
from __future__ import annotations

MIN_MARGIN_PERCENT = 30.0
MIN_PRICE_BRL = 50.0


def calculate_margin(price_liga_brl: float, price_tcg_brl: float) -> float | None:
    """Margem BRUTA sobre a VENDA (%) = (ref - compra) / ref * 100.

    compra = preco Liga; ref = TCGplayer em BRL. Sem taxas (frete, cartao,
    IOF: o operador calcula por fora). compra ou ref <= 0 -> None.
    """
    if price_liga_brl <= 0 or price_tcg_brl <= 0:
        return None
    return (price_tcg_brl - price_liga_brl) / price_tcg_brl * 100


def calculate_roi(price_liga_brl: float, price_tcg_brl: float) -> float | None:
    """ROI de aquisicao (%) = (ref - compra) / compra * 100. So informativo:
    nunca filtra, classifica nem ordena. compra ou ref <= 0 -> None."""
    if price_liga_brl <= 0 or price_tcg_brl <= 0:
        return None
    return (price_tcg_brl - price_liga_brl) / price_liga_brl * 100


def is_approved(
    price_liga_brl: float,
    margin_percent: float,
    min_price: float = MIN_PRICE_BRL,
    min_margin: float = MIN_MARGIN_PERCENT,
) -> bool:
    return price_liga_brl >= min_price and margin_percent >= min_margin
