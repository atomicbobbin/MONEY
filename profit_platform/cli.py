"""Command line interface for the Profit Platform."""

from __future__ import annotations

import argparse
from typing import Sequence

from .api import run_server
from .database import create_tables, get_connection
from .service import ProfitPlatformService

DEFAULT_DATABASE = "profit_platform.db"


def init_db(database_path: str) -> None:
    with get_connection(database_path) as connection:
        create_tables(connection)


def seed_demo(database_path: str) -> None:
    service = ProfitPlatformService(database_path)
    product = service.create_product(
        name="Conversion Boost Course",
        base_price=149.0,
        target_margin=0.35,
        description="Premium training for ecommerce founders",
    )
    demo_observations = [
        (129, 42, 400),
        (149, 38, 310),
        (169, 32, 295),
        (189, 21, 260),
    ]
    for price, units, visitors in demo_observations:
        service.add_observation(product.id, price, units, visitors)


def show_insight(database_path: str, product_id: int) -> None:
    service = ProfitPlatformService(database_path)
    insight = service.pricing_insight(product_id)
    print("Recommended price:", f"${insight.recommended_price:.2f}")
    print("Expected conversion:", f"{insight.expected_conversion*100:.1f}%")
    print("Revenue per visitor:", f"${insight.expected_revenue_per_visitor:.2f}")
    if insight.elasticity is not None:
        print("Estimated elasticity:", f"{insight.elasticity:.2f}")
    print("Data points used:", insight.sample_size)


def serve(database_path: str, host: str, port: int) -> None:
    run_server(host=host, port=port, database_path=database_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profit Platform utilities")
    parser.add_argument("--database", default=DEFAULT_DATABASE, help="Path to SQLite database")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db", help="Initialise the database")
    subparsers.add_parser("seed-demo", help="Populate the database with demo data")

    recommend_parser = subparsers.add_parser("recommend", help="Show pricing insight for a product")
    recommend_parser.add_argument("product_id", type=int)

    serve_parser = subparsers.add_parser("serve", help="Run the Profit Platform API server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        init_db(args.database)
    elif args.command == "seed-demo":
        seed_demo(args.database)
    elif args.command == "recommend":
        show_insight(args.database, args.product_id)
    elif args.command == "serve":
        serve(args.database, args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
