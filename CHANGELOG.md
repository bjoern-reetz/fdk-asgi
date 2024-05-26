## v0.6.0 (2024-05-26)

### BREAKING CHANGE

- The InverseFnMiddleware was removed from fdk_asgi and is now only available in the tests when cloning the repo.

### Refactor

- move InverseFnMiddleware tests
- **fdk_asgi.types**: refactor to strenum.StrEnum implementation

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
