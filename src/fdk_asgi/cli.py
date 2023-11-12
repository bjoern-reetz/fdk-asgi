import logging
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
import uvicorn
from uvicorn.importer import import_from_string

from fdk_asgi.app import FnMiddleware
from fdk_asgi.types import HTTPProtocolType, LifespanType, LoopSetupType

app = typer.Typer()
logger = logging.getLogger(__name__)

LOGGING_CONFIG: dict[str] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: B950
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        __package__: {"handlers": ["default"], "level": "DEBUG"},
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


@app.command()
def serve(
    app_uri: Annotated[str, typer.Argument(metavar="APP")],
    uds: Annotated[
        str,
        typer.Option(
            envvar="FN_LISTENER",
            help='Path to the UNIX domain socket, prefixed with "unix:". '
            "This will be managed by the Fn Server.",
        ),
    ] = "unix:./fdk-asgi.socket",
    loop: Annotated[
        LoopSetupType, typer.Option(envvar="FDK_ASGI_LOOP")
    ] = LoopSetupType.none,
    http: Annotated[
        HTTPProtocolType, typer.Option(envvar="FDK_ASGI_HTTP")
    ] = HTTPProtocolType.auto,
    lifespan: Annotated[
        LifespanType, typer.Option(envvar="FDK_ASGI_LIFESPAN")
    ] = LifespanType.auto,
    env_file: Annotated[
        Optional[Path],
        typer.Option(
            envvar="FDK_ASGI_ENV_FILE",
            help="Read configuration from an env file. "
            "Only affects the ASGI app, not the FDK/Server!",
        ),
    ] = None,
    log_config: Annotated[
        Optional[Path], typer.Option(envvar="FDK_ASGI_LOG_CONFIG")
    ] = None,
    log_level: Annotated[
        Optional[str], typer.Option(envvar="FDK_ASGI_LOG_LEVEL")
    ] = None,
    access_log: Annotated[bool, typer.Option(envvar="FDK_ASGI_ACCESS_LOG")] = True,
    proxy_headers: Annotated[
        bool,
        typer.Option(
            envvar="FDK_ASGI_PROXY_HEADERS",
            help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For, X-Forwarded-Port "
            "to populate remote address info.",
        ),
    ] = True,
    server_header: Annotated[
        bool, typer.Option(envvar="FDK_ASGI_SERVER_HEADER")
    ] = True,
    date_header: Annotated[bool, typer.Option(envvar="FDK_ASGI_DATE_HEADER")] = True,
    root_path: Annotated[
        str,
        typer.Option(
            envvar="FDK_ASGI_ROOT_PATH",
            help="Set the ASGI 'root_path' for applications "
            "sub-mounted below a given URL path.",
            show_default=False,
        ),
    ] = "",
    timeout_keep_alive: Annotated[
        int, typer.Option(envvar="FDK_ASGI_TIMEOUT_KEEP_ALIVE")
    ] = 5,
    factory: Annotated[
        bool,
        typer.Option(
            envvar="FDK_ASGI_FACTORY",
            help="Treat APP as an application factory, "
            "i.e. a () -> <ASGI app> callable.",
        ),
    ] = False,
    h11_max_incomplete_event_size: Annotated[
        Optional[int], typer.Option(envvar="FDK_ASGI_H11_MAX_INCOMPLETE_EVENT_SIZE")
    ] = None,
):
    asgi_app = import_from_string(app_uri)
    if factory:
        asgi_app = asgi_app()
    fn_asgi_app = FnMiddleware(asgi_app)
    if log_config is None:
        log_config = LOGGING_CONFIG

    socket = Path(uds.removeprefix("unix:"))
    os.umask(0o666)

    config = uvicorn.Config(
        app=fn_asgi_app,
        uds=str(socket),
        loop=loop.value,
        http=http.value,
        ws="none",
        lifespan=lifespan.value,
        env_file=env_file,
        log_config=log_config,
        log_level=log_level,
        access_log=access_log,
        # use_colors: Optional[bool] = None,
        interface="asgi3",  # todo: add support for asgi2 and wsgi
        workers=1,
        proxy_headers=proxy_headers,  # todo: check if Functions supports this header
        server_header=server_header,  # todo: check if Functions supports this header
        date_header=date_header,  # todo: check if Functions supports this header
        # forwarded_allow_ips: Optional[Union[List[str], str]] = None,
        root_path=root_path,
        # limit_concurrency: Optional[int] = None,
        # limit_max_requests: Optional[int] = None,
        # backlog: int = 2048,
        timeout_keep_alive=timeout_keep_alive,
        # timeout_notify: int = 30,
        # timeout_graceful_shutdown: Optional[int] = None,
        # callback_notify: Optional[Callable[..., Awaitable[None]]] = None,
        # headers: Optional[List[Tuple[str, str]]] = None,
        factory=factory,
        h11_max_incomplete_event_size=h11_max_incomplete_event_size,
    )

    server = uvicorn.Server(config)
    server.run()
