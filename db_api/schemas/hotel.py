from sqlalchemy import Column, BigInteger, Integer, String, sql, Float

from db_api.db_gino import TimedBaseModel


class Hotel(TimedBaseModel):
    __tablename__ = 'hotels'
    id = Column(BigInteger)
    name = Column(String(100))
    address = Column(String(100))
    distance = Column(Float)
    night_price = Column(Integer)
    all_period_price = Column(BigInteger)
    link = Column(String(100))

    query: sql.Select
