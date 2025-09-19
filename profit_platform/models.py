"""Domain models for Profit Platform."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    name: str
    base_price: float
    target_margin: float
    description: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class PriceObservation:
    product_id: int
    price: float
    units_sold: int
    visitors: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    @property
    def conversion_rate(self) -> float:
        return self.units_sold / self.visitors if self.visitors else 0.0


@dataclass
class PriceExperiment:
    product_id: int
    hypothesis: str
    control_price: float
    variant_price: float
    completed: bool = False
    id: Optional[int] = None
    start_date: Optional[datetime] = None
