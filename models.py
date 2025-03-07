from sqlalchemy import Column, String, Float, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class OHLCVData(Base):
    __tablename__ = 'ohlcv_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)