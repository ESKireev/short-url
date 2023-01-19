import xxhash
import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, RedirectResponse
from fastapi_utils.cbv import cbv

from .db import models
from . import schemas
from .db.connect import get_pg_session


router = APIRouter()


def get_hash(value):
    return xxhash.xxh32(value).hexdigest()


async def run_in_process(executor, func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)


@cbv(router)
class LinkGeneratorViews:
    pg: AsyncSession = Depends(get_pg_session)

    @router.post("/", response_model=schemas.Url)
    async def create_short_path(
        self, url_api: schemas.UrlCreate, request: Request
    ):
        short_path = await run_in_process(
            request.app.state.executor, get_hash, url_api.url
        )

        execute_result = await self.pg.execute(
            statement=sqlalchemy.select(models.Url).where(
                models.Url.short_path == short_path
            )
        )
        db_url = execute_result.scalar()

        if db_url:
            raise HTTPException(
                status_code=400,
                detail=f"This url {url_api.url} already exists.",
            )

        db_url = models.Url(short_path=short_path, url=url_api.url)
        self.pg.add(db_url)

        await self.pg.commit()
        await self.pg.refresh(db_url)

        return {"url": url_api.url, "short_url": request.url._url + short_path}

    @router.get("/{short_path}")
    async def redirect(self, short_path: str):
        execute_result = await self.pg.execute(
            statement=sqlalchemy.select(models.Url).where(
                models.Url.short_path == short_path
            )
        )
        db_url = execute_result.scalar()

        if not db_url:
            raise HTTPException(
                status_code=404,
                detail=f"Not found local_short_path: {short_path}",
            )

        return RedirectResponse(url=db_url.url)

    @router.delete("/{short_path}")
    async def delete_url(self, short_path: str):
        db_url = await self.pg.execute(
            sqlalchemy.select(models.Url).where(
                models.Url.short_path == short_path
            )
        )

        if not db_url:
            raise HTTPException(
                status_code=404,
                detail=f"Not found url with short path: {short_path}",
            )

        query = sqlalchemy.delete(models.Url).where(
            models.Url.short_path == short_path
        )
        await self.pg.execute(query)
        await self.pg.commit()

        return Response(status_code=200)
