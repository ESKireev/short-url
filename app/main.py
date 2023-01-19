from concurrent.futures.process import ProcessPoolExecutor

from fastapi import FastAPI

from app.routers import router


app = FastAPI()
app.include_router(router)


@app.on_event("startup")
async def on_startup():
    app.state.executor = ProcessPoolExecutor()


@app.on_event("shutdown")
async def on_shutdown():
    app.state.executor.shutdown()
