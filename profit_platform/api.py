"""Minimal WSGI API exposing Profit Platform services."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any, Callable
from wsgiref.simple_server import make_server

from .pricing import PricingInsight
from .service import ProfitPlatformService

ResponseStart = Callable[[str, list[tuple[str, str]]], None]


class ProfitPlatformAPI:
    def __init__(self, service: ProfitPlatformService | None = None):
        self.service = service or ProfitPlatformService()

    # WSGI callable -----------------------------------------------------
    def __call__(self, environ, start_response: ResponseStart):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "")

        try:
            if method == "GET" and path == "/health":
                return self._response(start_response, HTTPStatus.OK, {"status": "ok"})
            if method == "GET" and path == "/products":
                products = [self._serialize_product(p) for p in self.service.list_products()]
                return self._response(start_response, HTTPStatus.OK, products)
            if method == "POST" and path == "/products":
                payload = self._load_json(environ)
                product = self.service.create_product(
                    name=payload["name"],
                    base_price=float(payload["base_price"]),
                    target_margin=float(payload.get("target_margin", 0.2)),
                    description=payload.get("description"),
                )
                return self._response(start_response, HTTPStatus.CREATED, self._serialize_product(product))
            if path.startswith("/products/"):
                return self._handle_product_routes(method, path, environ, start_response)
            if method == "POST" and path == "/experiments":
                payload = self._load_json(environ)
                experiment = self.service.create_experiment(
                    product_id=int(payload["product_id"]),
                    hypothesis=payload["hypothesis"],
                    control_price=float(payload["control_price"]),
                    variant_price=float(payload["variant_price"]),
                    completed=bool(payload.get("completed", False)),
                )
                return self._response(start_response, HTTPStatus.CREATED, self._serialize_experiment(experiment))
            if method == "GET" and path == "/experiments":
                experiments = [self._serialize_experiment(e) for e in self.service.list_experiments()]
                return self._response(start_response, HTTPStatus.OK, experiments)

            return self._response(start_response, HTTPStatus.NOT_FOUND, {"detail": "Not found"})
        except KeyError as exc:
            return self._response(
                start_response, HTTPStatus.BAD_REQUEST, {"detail": f"Missing field: {exc.args[0]}"}
            )
        except ValueError as exc:
            return self._response(start_response, HTTPStatus.BAD_REQUEST, {"detail": str(exc)})

    # Internal routing --------------------------------------------------
    def _handle_product_routes(self, method: str, path: str, environ, start_response: ResponseStart):
        parts = [p for p in path.split("/") if p]
        if len(parts) < 2:
            return self._response(start_response, HTTPStatus.NOT_FOUND, {"detail": "Not found"})
        product_id = int(parts[1])

        if len(parts) == 2 and method == "GET":
            product = self.service.get_product(product_id)
            return self._response(start_response, HTTPStatus.OK, self._serialize_product(product))
        if len(parts) == 2 and method == "POST":
            payload = self._load_json(environ)
            observation = self.service.add_observation(
                product_id=product_id,
                price=float(payload["price"]),
                units_sold=int(payload["units_sold"]),
                visitors=int(payload["visitors"]),
            )
            return self._response(start_response, HTTPStatus.CREATED, self._serialize_observation(observation))
        if len(parts) == 3 and parts[2] == "observations" and method == "POST":
            payload = self._load_json(environ)
            observation = self.service.add_observation(
                product_id=product_id,
                price=float(payload["price"]),
                units_sold=int(payload["units_sold"]),
                visitors=int(payload["visitors"]),
            )
            return self._response(start_response, HTTPStatus.CREATED, self._serialize_observation(observation))
        if len(parts) == 3 and parts[2] == "insights" and method == "GET":
            insight = self.service.pricing_insight(product_id)
            return self._response(start_response, HTTPStatus.OK, self._serialize_insight(insight))

        return self._response(start_response, HTTPStatus.NOT_FOUND, {"detail": "Not found"})

    # Serialisation helpers ---------------------------------------------
    def _serialize_product(self, product):
        return {
            "id": product.id,
            "name": product.name,
            "base_price": product.base_price,
            "target_margin": product.target_margin,
            "description": product.description,
            "created_at": product.created_at.isoformat() if product.created_at else None,
        }

    def _serialize_observation(self, observation):
        return {
            "id": observation.id,
            "product_id": observation.product_id,
            "price": observation.price,
            "units_sold": observation.units_sold,
            "visitors": observation.visitors,
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
        }

    def _serialize_experiment(self, experiment):
        return {
            "id": experiment.id,
            "product_id": experiment.product_id,
            "hypothesis": experiment.hypothesis,
            "control_price": experiment.control_price,
            "variant_price": experiment.variant_price,
            "completed": experiment.completed,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
        }

    def _serialize_insight(self, insight: PricingInsight) -> dict[str, Any]:
        return {
            "product_id": insight.product_id,
            "recommended_price": insight.recommended_price,
            "expected_conversion": insight.expected_conversion,
            "expected_revenue_per_visitor": insight.expected_revenue_per_visitor,
            "elasticity": insight.elasticity,
            "average_conversion": insight.average_conversion,
            "sample_size": insight.sample_size,
        }

    # Utility methods ---------------------------------------------------
    def _load_json(self, environ) -> dict[str, Any]:
        try:
            length = int(environ.get("CONTENT_LENGTH", "0") or "0")
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(length) if length else b""
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))

    def _response(self, start_response: ResponseStart, status: HTTPStatus, payload: Any):
        body = json.dumps(payload).encode("utf-8")
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ]
        start_response(f"{status.value} {status.phrase}", headers)
        return [body]


def run_server(host: str = "127.0.0.1", port: int = 8000, database_path: str | None = None):
    service = ProfitPlatformService(database_path)
    app = ProfitPlatformAPI(service)
    with make_server(host, port, app) as httpd:
        print(f"Profit Platform API running on http://{host}:{port}")
        httpd.serve_forever()
