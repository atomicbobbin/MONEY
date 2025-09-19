import json
from io import BytesIO

from profit_platform.api import ProfitPlatformAPI
from profit_platform.service import ProfitPlatformService


def test_product_insights_flow(service: ProfitPlatformService):
    product = service.create_product(
        name="AI Funnel Optimizer",
        base_price=120.0,
        target_margin=0.4,
        description="Premium SaaS for ecommerce pricing",
    )

    observations = [
        (110, 30, 200),
        (130, 26, 210),
        (150, 18, 205),
    ]
    for price, units, visitors in observations:
        service.add_observation(product.id, price, units, visitors)

    insight = service.pricing_insight(product.id)
    assert insight.product_id == product.id
    assert 0 <= insight.expected_conversion <= 1
    assert insight.sample_size == len(observations)
    assert insight.expected_revenue_per_visitor >= 0

    experiment = service.create_experiment(
        product_id=product.id,
        hypothesis="Higher urgency messaging will sustain conversions at $140",
        control_price=130,
        variant_price=140,
    )
    experiments = service.list_experiments(product.id)
    assert experiments[0].id == experiment.id
    assert experiments[0].hypothesis.startswith("Higher urgency")


def test_wsgi_health_endpoint(service: ProfitPlatformService):
    api = ProfitPlatformAPI(service)
    status, body = _wsgi_request(api, "GET", "/health")
    assert status.startswith("200")
    assert json.loads(body) == {"status": "ok"}


def _wsgi_request(app, method: str, path: str, payload: dict | None = None):
    body_bytes = json.dumps(payload).encode("utf-8") if payload is not None else b""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body_bytes)),
        "wsgi.input": BytesIO(body_bytes),
    }
    response = {}

    def start_response(status_line, headers):
        response["status"] = status_line
        response["headers"] = headers

    chunks = app(environ, start_response)
    body = b"".join(chunks).decode("utf-8")
    return response["status"], body
