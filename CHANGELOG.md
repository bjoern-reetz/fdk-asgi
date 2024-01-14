## v0.5.0 (2024-01-14)

### Refactor

- change uvicorn and typer to optional dependencies

## v0.4.0 (2024-01-07)

### Feat

- add module fdk_asgi.testing

### Fix

- remove usage of language features not supported by Python 3.8

### Refactor

- move default logging config from separate JSON file to cli.py
- replace pytest-asyncio with anyio and trio
