"""Testes das regras de filtro do scanner: preço >= R$50 e margem >= 30%."""
from src.collectors.liga_pokemon import LigaOffer
from src.collectors.tcgplayer import TCGReference
from src.matching.card_matcher import match_cards


def _make_pair(price_liga: float, price_usd: float, name: str = "Card"):
    return (
        LigaOffer(
            card_name=name,
            set_name="Set",
            price_brl=price_liga,
            url=f"https://liga/{name}",
        ),
        TCGReference(
            card_name=name,
            set_name="Set",
            price_usd=price_usd,
            url=f"https://tcg/{name}",
        ),
    )


class TestFilters:
    def test_approved_when_meets_both_rules(self):
        offer, ref = _make_pair(price_liga=100.0, price_usd=30.0)
        # tcg_brl = 30 * 5 = 150; margem sobre a venda = 33,3%
        result = match_cards([offer], [ref], exchange_rate=5.0)
        assert result[0].status == "approved"

    def test_rejected_when_price_below_50(self):
        offer, ref = _make_pair(price_liga=40.0, price_usd=20.0)
        # margem boa (60%) mas preço Liga abaixo de R$50
        result = match_cards([offer], [ref], exchange_rate=5.0)
        assert result[0].status == "rejected"

    def test_rejected_when_margin_below_30(self):
        offer, ref = _make_pair(price_liga=100.0, price_usd=22.0)
        # tcg_brl = 110; margem = 9,1%
        result = match_cards([offer], [ref], exchange_rate=5.0)
        assert result[0].status == "rejected"

    def test_rejected_when_margin_negative(self):
        offer, ref = _make_pair(price_liga=200.0, price_usd=20.0)
        # tcg_brl = 100; margem = -100%
        result = match_cards([offer], [ref], exchange_rate=5.0)
        assert result[0].status == "rejected"

    def test_approved_exactly_at_boundary(self):
        # margem sobre a venda exatamente 30%: compra 70, ref 100 (usd 20 * 5)
        offer, ref = _make_pair(price_liga=70.0, price_usd=20.0)
        result = match_cards([offer], [ref], exchange_rate=5.0)
        assert result[0].status == "approved"

    def test_custom_min_price(self):
        offer, ref = _make_pair(price_liga=60.0, price_usd=20.0)
        # margem boa, preço acima do default mas abaixo do custom 100
        result = match_cards(
            [offer], [ref], exchange_rate=5.0, min_price=100.0
        )
        assert result[0].status == "rejected"

    def test_custom_min_margin(self):
        offer, ref = _make_pair(price_liga=100.0, price_usd=30.0)
        # margem 33,3%, mas exige >= 75%
        result = match_cards(
            [offer], [ref], exchange_rate=5.0, min_margin=75.0
        )
        assert result[0].status == "rejected"

    def test_filters_mixed_batch(self):
        offers = []
        refs = []
        for i, (lp, up, expected) in enumerate(
            [
                (100.0, 30.0, "approved"),   # margem 33,3%
                (40.0, 20.0, "rejected"),    # preço < R$50
                (100.0, 22.0, "rejected"),   # margem 9,1%
                (200.0, 20.0, "rejected"),   # margem -100%
            ]
        ):
            name = f"Card{i}"
            o, r = _make_pair(lp, up, name=name)
            offers.append(o)
            refs.append(r)

        results = match_cards(offers, refs, exchange_rate=5.0)
        approved = [r for r in results if r.status == "approved"]
        rejected = [r for r in results if r.status == "rejected"]
        assert len(approved) == 1
        assert len(rejected) == 3


class TestDiscardCounters:
    def test_zero_reference_is_counted_not_silent(self):
        from src.reporting.markdown import build_markdown
        o1, r1 = _make_pair(price_liga=100.0, price_usd=0.0, name="Zero")
        o2, r2 = _make_pair(price_liga=0.0, price_usd=20.0, name="SemPreco")
        o3, r3 = _make_pair(price_liga=100.0, price_usd=30.0, name="Ok")
        o4, _ = _make_pair(price_liga=100.0, price_usd=30.0, name="SemMatch")
        offers = [o1, o2, o3, o4]
        result = match_cards(offers, [r1, r2, r3], exchange_rate=5.0)
        d = result.discards
        assert d["sem_referencia_valida"] == 1
        assert d["sem_preco_liga"] == 1
        assert d["sem_match"] == 1
        assert len(result) + sum(d.values()) == len(offers)
        md = build_markdown(result, 5.0)
        assert "sem referência válida: 1" in md
        assert "sem preço Liga válido: 1" in md
