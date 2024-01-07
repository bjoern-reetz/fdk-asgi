# fdk-asgi

[![pipeline status](https://github.com/bjoern-reetz/fdk-asgi/actions/workflows/publish.yml/badge.svg?main)](https://github.com/bjoern-reetz/fdk-asgi/actions/workflows/publish.yml)
[![latest package version](https://img.shields.io/pypi/v/fdk-asgi)](https://pypi.org/project/fdk-asgi/)
[![supported python versions](https://img.shields.io/pypi/pyversions/fdk-asgi)](https://pypi.org/project/fdk-asgi/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

An alternative FDK to easily run any ASGI application on OCI Functions behind an API Gateway.

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
