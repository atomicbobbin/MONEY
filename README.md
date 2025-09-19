# Profit Platform

Profit Platform is a pricing-intelligence SaaS starter kit. It helps digital product
founders and agencies monetise by providing:

- **Product catalog management** with sales observations stored in SQLite.
- **Automatic pricing insights** that estimate conversion rates, revenue per visitor,
  and elasticity, then recommend a winning price point.
- **Experiment tracking** so you can document hypotheses and AB-test offers.
- **Lightweight JSON API** powered by the Python standard library so you can deploy
  anywhere without extra dependencies.

Use it as the foundation for a premium pricing optimizer that you can charge for via
subscriptions, consulting retainers, or enterprise licences.

## Quick start

Create a virtual environment and install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Initialise the database and seed it with demo data:

```bash
python -m profit_platform.cli --database demo.db init-db
python -m profit_platform.cli --database demo.db seed-demo
```

Launch the HTTP API server (built on `wsgiref.simple_server`):

```bash
python -m profit_platform.cli --database demo.db serve --port 8080
```

Visit `http://localhost:8080/health` for a quick status check. Pair the
backend with a React or no-code dashboard to sell analytics subscriptions,
or embed it behind a paywall for your clients.

## CLI usage

The CLI is designed for founders who prefer to automate workflows from the terminal:

```bash
python -m profit_platform.cli --database demo.db init-db
python -m profit_platform.cli --database demo.db seed-demo
python -m profit_platform.cli --database demo.db recommend 1
```

## Testing

```bash
pytest
```

## Monetisation ideas

- Offer real-time pricing dashboards to ecommerce brands on a monthly retainer.
- Bundle bespoke price testing playbooks with consulting engagements.
- Sell API access to agencies that want to embed smart pricing into their internal tools.
