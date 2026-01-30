import logging
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from service.server.server import ConversationServer
from starlette.responses import JSONResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from dotenv import load_dotenv

load_dotenv()

logfile = "api.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(module)s - %(funcName)s - %(message)s",
    handlers=[
        logging.FileHandler(logfile, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class HTTPXClientWrapper:
    """Wrapper to return the singleton client where needed."""

    async_client: httpx.AsyncClient = None

    def start(self):
        """Instantiate the client. Call from the FastAPI startup hook."""
        self.async_client = httpx.AsyncClient(timeout=30)

    async def stop(self):
        """Gracefully shutdown. Call from FastAPI shutdown hook."""
        await self.async_client.aclose()
        self.async_client = None

    def __call__(self):
        """Calling the instantiated HTTPXClientWrapper returns the wrapped singleton."""
        # Ensure we don't use it if not started / running
        assert self.async_client is not None
        return self.async_client

httpx_client_wrapper = HTTPXClientWrapper()
@asynccontextmanager
async def lifespan(app: FastAPI):
    httpx_client_wrapper.start()
    agent_server = ConversationServer(app, httpx_client_wrapper())
    app.openapi_schema = None
    app.setup()
    yield
    await httpx_client_wrapper.stop()
# 添加 ping 路由

app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )

@app.middleware("http")
async def log_request_body(request: Request, call_next):
    if request.method == "POST":
        body = await request.body()
        logging.info(f"Request to {request.url.path} with body: {body.decode('utf-8')}")
    else:
        logging.info(f"Request to {request.url.path}")
    response = await call_next(request)
    return response
@app.api_route("/ping", methods=["GET", "POST"])
async def ping():
    return "Pong"


# 启动服务
if __name__ == "__main__":
    import uvicorn
    print(f"启动A2A的多Agent协调者后端服务，端口为13000")
    uvicorn.run(app, host="0.0.0.0", port=13000)
