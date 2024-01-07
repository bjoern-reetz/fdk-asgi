import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
import uvicorn
from uvicorn.importer import import_from_string

from fdk_asgi.app import FnMiddleware
from fdk_asgi.types import HTTPProtocolType, LifespanType, LoopSetupType

UDS_PREFIX = "unix:"
DEFAULT_LOGGING_CONFIG: dict[str, any] = {
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
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "fdk_asgi": {"handlers": ["default"], "level": "INFO"},
        "fdk_asgi.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
    },
}

app = typer.Typer()
logger = logging.getLogger(__name__)


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
    prefix: Annotated[
        str,
        typer.Option(
            envvar="FDK_ASGI_PREFIX",
            help="Strips the given prefix from URL paths. "
            "Also sets root_path to this value.",
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
    fn_asgi_app = FnMiddleware(asgi_app, prefix)

    socket = Path(uds[len(UDS_PREFIX) :]) if uds.startswith(UDS_PREFIX) else Path(uds)
    # os.umask(0o666)  # todo: check if this is necessary

    config = uvicorn.Config(
        app=fn_asgi_app,
        uds=str(socket),
        loop=loop.value,
        http=http.value,
        ws="none",
        lifespan=lifespan.value,
        env_file=env_file,
        log_config=DEFAULT_LOGGING_CONFIG if log_config is None else log_config,
        log_level=log_level,
        access_log=False,
        # use_colors: Optional[bool] = None,
        interface="asgi3",
        workers=1,
        proxy_headers=proxy_headers,  # todo: check if Functions supports this header
        server_header=server_header,  # todo: check if Functions supports this header
        date_header=date_header,  # todo: check if Functions supports this header
        # forwarded_allow_ips: Optional[Union[List[str], str]] = None,
        # root_path="",
        # limit_concurrency: Optional[int] = None,
        # limit_max_requests: Optional[int] = None,
        # backlog: int = 2048,
        timeout_keep_alive=timeout_keep_alive,
        # timeout_notify: int = 30,
        # timeout_graceful_shutdown: Optional[int] = None,
        # callback_notify: Optional[Callable[..., Awaitable[None]]] = None,
        # headers: Optional[List[Tuple[str, str]]] = None,
        factory=False,
        h11_max_incomplete_event_size=h11_max_incomplete_event_size,
    )

    server = uvicorn.Server(config)
    try:
        server.run()
    finally:
        socket.unlink(missing_ok=True)
