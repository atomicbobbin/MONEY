"""Domain service layer for Profit Platform."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .database import create_tables, get_connection
from .models import PriceExperiment, PriceObservation, Product
from .pricing import PricingInsight, recommend_price


class ProfitPlatformService:
    """High level API for managing products and pricing data."""

    def __init__(self, database_path: str | Path | None = None):
        self.database_path = database_path
        with get_connection(self.database_path) as connection:
            create_tables(connection)

    # Product management -------------------------------------------------
    def create_product(
        self, name: str, base_price: float, target_margin: float, description: str | None = None
    ) -> Product:
        with get_connection(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO product (name, base_price, target_margin, description)
                VALUES (?, ?, ?, ?)
                """,
                (name, base_price, target_margin, description),
            )
            product_id = cursor.lastrowid
            row = connection.execute(
                "SELECT id, name, base_price, target_margin, description, created_at FROM product WHERE id = ?",
                (product_id,),
            ).fetchone()
        return _row_to_product(row)

    def list_products(self) -> List[Product]:
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                "SELECT id, name, base_price, target_margin, description, created_at FROM product ORDER BY id"
            ).fetchall()
        return [_row_to_product(row) for row in rows]

    # Observations -------------------------------------------------------
    def add_observation(
        self, product_id: int, price: float, units_sold: int, visitors: int
    ) -> PriceObservation:
        with get_connection(self.database_path) as connection:
            self._ensure_product_exists(connection, product_id)
            cursor = connection.execute(
                """
                INSERT INTO price_observation (product_id, price, units_sold, visitors)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, price, units_sold, visitors),
            )
            obs_id = cursor.lastrowid
            row = connection.execute(
                "SELECT id, product_id, price, units_sold, visitors, created_at FROM price_observation WHERE id = ?",
                (obs_id,),
            ).fetchone()
        return _row_to_observation(row)

    def list_observations(self, product_id: int) -> List[PriceObservation]:
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, product_id, price, units_sold, visitors, created_at
                FROM price_observation WHERE product_id = ? ORDER BY created_at
                """,
                (product_id,),
            ).fetchall()
        return [_row_to_observation(row) for row in rows]

    def pricing_insight(self, product_id: int) -> PricingInsight:
        product = self.get_product(product_id)
        observations = self.list_observations(product_id)
        return recommend_price(product, observations)

    def get_product(self, product_id: int) -> Product:
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT id, name, base_price, target_margin, description, created_at FROM product WHERE id = ?",
                (product_id,),
            ).fetchone()
        if not row:
            raise ValueError(f"Product {product_id} not found")
        return _row_to_product(row)

    # Experiments --------------------------------------------------------
    def create_experiment(
        self,
        product_id: int,
        hypothesis: str,
        control_price: float,
        variant_price: float,
        completed: bool = False,
    ) -> PriceExperiment:
        with get_connection(self.database_path) as connection:
            self._ensure_product_exists(connection, product_id)
            cursor = connection.execute(
                """
                INSERT INTO price_experiment (product_id, hypothesis, control_price, variant_price, completed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (product_id, hypothesis, control_price, variant_price, int(completed)),
            )
            exp_id = cursor.lastrowid
            row = connection.execute(
                """
                SELECT id, product_id, hypothesis, control_price, variant_price, completed, start_date
                FROM price_experiment WHERE id = ?
                """,
                (exp_id,),
            ).fetchone()
        return _row_to_experiment(row)

    def list_experiments(self, product_id: Optional[int] = None) -> List[PriceExperiment]:
        with get_connection(self.database_path) as connection:
            if product_id is None:
                rows = connection.execute(
                    """
                    SELECT id, product_id, hypothesis, control_price, variant_price, completed, start_date
                    FROM price_experiment ORDER BY start_date DESC
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, product_id, hypothesis, control_price, variant_price, completed, start_date
                    FROM price_experiment WHERE product_id = ? ORDER BY start_date DESC
                    """,
                    (product_id,),
                ).fetchall()
        return [_row_to_experiment(row) for row in rows]

    # Internal helpers ---------------------------------------------------
    @staticmethod
    def _ensure_product_exists(connection, product_id: int) -> None:
        row = connection.execute("SELECT id FROM product WHERE id = ?", (product_id,)).fetchone()
        if not row:
            raise ValueError(f"Product {product_id} not found")


def _row_to_product(row) -> Product:
    created_at = _parse_datetime(row["created_at"]) if row["created_at"] else None
    return Product(
        id=row["id"],
        name=row["name"],
        base_price=row["base_price"],
        target_margin=row["target_margin"],
        description=row["description"],
        created_at=created_at,
    )


def _row_to_observation(row) -> PriceObservation:
    created_at = _parse_datetime(row["created_at"]) if row["created_at"] else None
    return PriceObservation(
        id=row["id"],
        product_id=row["product_id"],
        price=row["price"],
        units_sold=row["units_sold"],
        visitors=row["visitors"],
        created_at=created_at,
    )


def _row_to_experiment(row) -> PriceExperiment:
    start_date = _parse_datetime(row["start_date"]) if row["start_date"] else None
    return PriceExperiment(
        id=row["id"],
        product_id=row["product_id"],
        hypothesis=row["hypothesis"],
        control_price=row["control_price"],
        variant_price=row["variant_price"],
        completed=bool(row["completed"]),
        start_date=start_date,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
