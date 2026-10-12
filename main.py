
import time
import uuid

from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware

EMAIL = "26ds1000025@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-zrhnet.example.com"

api = FastAPI(title="CORS-Aware Metrics API")


@api.get("/stats")
def get_stats(values: str = Query(...)):
    try:
        numbers = [int(v.strip()) for v in values.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="values must be integers")

    if not numbers:
        raise HTTPException(status_code=422, detail="values cannot be empty")

    total = sum(numbers)
    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / len(numbers),
    }


cors_app = CORSMiddleware(
    app=api,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
    max_age=600,
)


class RequestMetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                elapsed = max(0.0, time.perf_counter() - start_time)
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-request-id", request_id.encode("ascii")),
                    (b"x-process-time", f"{elapsed:.6f}".encode("ascii")),
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


app = RequestMetricsMiddleware(cors_app)
