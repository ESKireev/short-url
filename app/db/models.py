from sqlalchemy import Column, String

from .connect import DBBase


class Url(DBBase):
    __tablename__ = "urls"

    short_path = Column(String, primary_key=True)
    url = Column(String, nullable=False)
