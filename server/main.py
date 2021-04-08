import argparse
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from server.core.config import settings
from server.endpoints import activelearning, inference, logs, train, info
from server.utils.app_utils import get_app_instance
from server.utils.generic import init_log_config

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_STR}/openapi.json",
    docs_url=None,
    redoc_url="/docs"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(info.router)
app.include_router(inference.router)
app.include_router(train.router)
app.include_router(activelearning.router)
app.include_router(logs.router)


@app.get("/", include_in_schema=False)
async def custom_swagger_ui_html():
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - APIs")

    body = html.body.decode("utf-8")
    body = body.replace('showExtensions: true,', 'showExtensions: true, defaultModelsExpandDepth: -1,')
    return HTMLResponse(body)


@app.on_event("startup")
async def startup_event():
    get_app_instance()


def run_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', required=True)
    parser.add_argument('-a', '--app', required=True)
    parser.add_argument('-d', '--debug', action='store_true')

    parser.add_argument('-i', '--host', default="0.0.0.0", type=str)
    parser.add_argument('-p', '--port', default=8000, type=int)
    parser.add_argument('-r', '--reload', action='store_true')
    parser.add_argument('-l', '--log_config', default=None, type=str)

    args = parser.parse_args()
    if not os.path.exists(args.app):
        print(f"APP Directory {args.app} NOT Found")
        exit(1)

    args.app = os.path.realpath(args.app)

    for arg in vars(args):
        print('USING:: {} = {}'.format(arg, getattr(args, arg)))
    print("")

    settings.PROJECT_NAME = f"MONAI-Label - {args.name}"
    settings.APP = args.name
    settings.APP_DIR = args.app

    os.putenv("PROJECT_NAME", settings.PROJECT_NAME)
    os.putenv("APP", settings.APP)
    os.putenv("APP_DIR", settings.APP_DIR)

    sys.path.append(args.app)
    sys.path.append(os.path.join(args.app, 'lib'))

    uvicorn.run(
        "main:app" if args.reload else app,
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info",
        reload=args.reload,
        log_config=init_log_config(args.log_config, args.app, "app.log"),
        use_colors=True,
        access_log=args.debug,
    )


if __name__ == '__main__':
    run_main()