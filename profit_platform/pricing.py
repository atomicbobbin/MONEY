"""Pricing intelligence utilities."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Sequence

from .models import PriceObservation, Product


@dataclass
class PricingInsight:
    product_id: int
    recommended_price: float
    expected_conversion: float
    expected_revenue_per_visitor: float
    elasticity: float | None
    average_conversion: float
    sample_size: int


def _linear_regression(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float] | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = mean(xs)
    mean_y = mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return None
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    return slope, intercept


def _bounded_prediction(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def calculate_elasticity(observations: Iterable[PriceObservation]) -> float | None:
    obs_list = list(observations)
    if len(obs_list) < 2:
        return None
    prices = [obs.price for obs in obs_list]
    conversions = [obs.conversion_rate for obs in obs_list]
    regression = _linear_regression(prices, conversions)
    if regression is None:
        return None
    slope, _intercept = regression
    mean_price = mean(prices)
    mean_conversion = mean(conversions)
    if mean_conversion == 0 or mean_price == 0:
        return None
    elasticity = slope * mean_price / mean_conversion
    return elasticity


def recommend_price(product: Product, observations: Sequence[PriceObservation]) -> PricingInsight:
    obs_list = list(observations)
    if not obs_list:
        margin_price = product.base_price * (1 + product.target_margin)
        return PricingInsight(
            product_id=product.id or -1,
            recommended_price=margin_price,
            expected_conversion=0.15,
            expected_revenue_per_visitor=margin_price * 0.15,
            elasticity=None,
            average_conversion=0.0,
            sample_size=0,
        )

    prices = [obs.price for obs in obs_list]
    conversions = [obs.conversion_rate for obs in obs_list]
    regression = _linear_regression(prices, conversions)
    average_conversion = mean(conversions)
    elasticity = calculate_elasticity(obs_list)

    def conversion_at(price: float) -> float:
        if regression is None:
            return average_conversion
        slope, intercept = regression
        return _bounded_prediction(intercept + slope * price)

    search_prices = [round(p, 2) for p in _generate_price_candidates(product.base_price, prices)]
    best_price = max(search_prices, key=lambda price: price * conversion_at(price))
    expected_conversion = conversion_at(best_price)
    expected_revenue = best_price * expected_conversion

    return PricingInsight(
        product_id=product.id or -1,
        recommended_price=best_price,
        expected_conversion=expected_conversion,
        expected_revenue_per_visitor=expected_revenue,
        elasticity=elasticity,
        average_conversion=average_conversion,
        sample_size=len(obs_list),
    )


def _generate_price_candidates(base_price: float, observed_prices: Sequence[float]) -> list[float]:
    floor_price = min(observed_prices + [base_price * 0.6])
    ceiling_price = max(observed_prices + [base_price * 1.6])
    step = max(base_price * 0.02, 0.25)
    price = floor_price
    candidates = []
    while price <= ceiling_price:
        candidates.append(round(price, 2))
        price += step
    return sorted(set(candidates + [base_price]))
