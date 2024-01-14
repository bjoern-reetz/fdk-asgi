# fdk-asgi

[![pipeline status](https://github.com/bjoern-reetz/fdk-asgi/actions/workflows/publish.yml/badge.svg?main)](https://github.com/bjoern-reetz/fdk-asgi/actions/workflows/publish.yml)
[![latest package version](https://img.shields.io/pypi/v/fdk-asgi)](https://pypi.org/project/fdk-asgi/)
![supported python versions](https://img.shields.io/pypi/pyversions/fdk-asgi)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/fdk-asgi)](https://pypistats.org/packages/fdk-asgi)
![source files coverage](./images/coverage.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

An alternative FDK to easily run any ASGI application on OCI Functions behind an API Gateway.

## Basic usage

Use it just like uvicorn. The fdk-asgi-serve command wraps your ASGI app with a middleware
that translates from/to the Fn protocol and starts a server that respects runtime Fn configuration,
e.g. listens on a unix-socket etc.

```bash
pip install fdk-asgi[cli]
fdk-asgi-serve package.module:app
```

If you install the package without extras, Typer and uvicorn dependencies are skipped.
This is particularly useful if you want to use another ASGI server
and just need the ASGI middleware this package provides.

## Full usage

```
fdk-asgi-serve --help
Usage: fdk-asgi-serve [OPTIONS] APP

Arguments:
  APP  [required]

Options:
  --uds TEXT                      Path to the UNIX domain socket, prefixed
                                  with "unix:". This will be managed by the Fn
                                  Server.  [env var: FN_LISTENER; default:
                                  unix:./fdk-asgi.socket]
  --loop [none|auto|asyncio|uvloop]
                                  [env var: FDK_ASGI_LOOP; default: none]
  --http [auto|h11|httptools]     [env var: FDK_ASGI_HTTP; default: auto]
  --lifespan [auto|on|off]        [env var: FDK_ASGI_LIFESPAN; default: auto]
  --env-file PATH                 Read configuration from an env file. Only
                                  affects the ASGI app, not the FDK/Server!
                                  [env var: FDK_ASGI_ENV_FILE]
  --log-config PATH               [env var: FDK_ASGI_LOG_CONFIG]
  --log-level TEXT                [env var: FDK_ASGI_LOG_LEVEL]
  --proxy-headers / --no-proxy-headers
                                  Enable/Disable X-Forwarded-Proto,
                                  X-Forwarded-For, X-Forwarded-Port to
                                  populate remote address info.  [env var:
                                  FDK_ASGI_PROXY_HEADERS; default: proxy-
                                  headers]
  --server-header / --no-server-header
                                  [env var: FDK_ASGI_SERVER_HEADER; default:
                                  server-header]
  --date-header / --no-date-header
                                  [env var: FDK_ASGI_DATE_HEADER; default:
                                  date-header]
  --prefix TEXT                   Strips the given prefix from URL paths. Also
                                  sets root_path to this value.  [env var:
                                  FDK_ASGI_PREFIX]
  --timeout-keep-alive INTEGER    [env var: FDK_ASGI_TIMEOUT_KEEP_ALIVE;
                                  default: 5]
  --factory / --no-factory        Treat APP as an application factory, i.e. a
                                  () -> <ASGI app> callable.  [env var:
                                  FDK_ASGI_FACTORY; default: no-factory]
  --h11-max-incomplete-event-size INTEGER
                                  [env var:
                                  FDK_ASGI_H11_MAX_INCOMPLETE_EVENT_SIZE]
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.
```

## Documentation on the Open Fn Project and OCI Functions

Example request:

```
POST /call HTTP/1.1
Fn-Call-Id : 12345678910
Fn-Deadline: <date/time>
Fn-Http-Request-Url: https://my.fn.com/t/hello/world
Fn-Http-Method: PUT
Fn-Http-H-Custom-Header: foo
Content-type: text/plain

<Body here>
```

Example Response:

```
HTTP/1.1 200 OK
Fn-Http-Status: 204
Fn-Http-H-My-Header: foo
Fn-Fdk-Version: fdk-go/0.0.42
Content-type: text/plain

<Body here>
```

For more info see [Fn container contract](https://github.com/fnproject/docs/blob/master/fn/develop/fn-format.md).

Notes:

- 0666 contract can be fulfilled by `gunicorn --umask 0666`.

### Default Environment Variables

Here is the list of automatically generated environment variables that are available to your functions.

| Fn Generated Var | Sample Value                 | Description                                                                                                                                                                                                                                                                   |
|------------------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `FN_APP_ID`      | `01NNNNNNNNNG8G00GZJ0000001` | The application ID for the app the current function is contained in.                                                                                                                                                                                                          |
| `FN_FN_ID`       | `01DYNNNNNNNG8G00GZJ0000002` | The ID of the current function                                                                                                                                                                                                                                                |
| `FN_FORMAT`      | `http-stream`                | Communications protocol. **(Deprecated)**                                                                                                                                                                                                                                     |
| `FN_LISTENER`    | `unix:/tmp/iofs/lsnr.sock`   | The Unix socket address (prefixed with “unix:”) on the file system that the FDK should create to listen for requests. The platform will guarantee that this directory is writable to the function. FDKs must not write any other data than the unix socket to this directory. |
| `FN_MEMORY`      | `128`                        | The maximum memory of the function in MB.                                                                                                                                                                                                                                     |
| `FN_TYPE`        | `sync`                       | The type of function. Always sync currently.                                                                                                                                                                                                                                  |

Source: [Fn Project: Using Config Variables and Environment Variables](https://fnproject.io/tutorials/basics/UsingRuntimeContext/#UsingConfigVariablesandEnvironmentVariables)
