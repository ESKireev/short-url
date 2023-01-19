from urllib.parse import urlparse

from pydantic import BaseModel, validator


class UrlCreate(BaseModel):
    url: str

    @validator("url")
    def check_url(cls, value):
        result = urlparse(value)

        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL")

        return value


class Url(BaseModel):
    url: str
    short_url: str
