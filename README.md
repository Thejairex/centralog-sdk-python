# Centralog SDK — Python

Python SDK for [Centralog](https://github.com/Thejairex/centralog) error monitoring.
Captures exceptions and sends a copy to your Centralog platform. Never breaks your app.

Supports **FastAPI**, **Flask** and **Django** (plus manual capture anywhere).

## Install

```bash
pip install centralog-sdk
# with framework support:
pip install "centralog-sdk[fastapi]"
```

## Configure

Env vars:

```env
CENTRALOG_ENABLED=true
CENTRALOG_ENDPOINT=https://centralog.tudominio.com/api/v1/ingest/events
CENTRALOG_API_KEY=clk_tu_api_key
CENTRALOG_ENVIRONMENT=production
CENTRALOG_RELEASE=2026.09.30.1
CENTRALOG_TIMEOUT=2
```

Generate the API key in Centralog: Projects → API Keys.

## Usage

**FastAPI** (one line):

```python
from fastapi import FastAPI
from centralog.frameworks.fastapi import register as centralog_register

app = FastAPI()
centralog_register(app)
```

**Flask**:

```python
from flask import Flask
from centralog.frameworks.flask import register as centralog_register

app = Flask(__name__)
centralog_register(app)
```

**Django** — add to `MIDDLEWARE`:

```python
MIDDLEWARE = [
    ...,
    "centralog.frameworks.django.CentralogMiddleware",
]
```

**Manual** (anywhere):

```python
from centralog import CentralogClient

client = CentralogClient()
client.context({"tenant": "acme"})

try:
    charge(order)
except Exception as exc:
    client.capture(exc, {"order_id": order.id})
```

Your local logging keeps working as always — the SDK only sends a **copy** to Centralog.

## Safety

- Short timeout (2s default), never blocks a request for long.
- Any network failure is swallowed and logged with `logging.debug`.
- Disabled automatically when `CENTRALOG_ENABLED=false` or endpoint/key are missing.
- No workers required (synchronous by design).

## Testing

```bash
uv run pytest
```
