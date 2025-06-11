"""
Module for database configuration and models.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Tuple

# Create SQLite database engine
engine = create_engine('sqlite:///watchbill.db')
Base = declarative_base()

class WatchstanderDB(Base):
    """Database model for Watchstander."""
    __tablename__ = 'watchstanders'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    qualification_date = Column(DateTime, nullable=False)
    is_n_head = Column(Boolean, nullable=False)
    availability_vectors = Column(JSON)  # Store monthly vectors as JSON

    def __repr__(self):
        return f"<WatchstanderDB(name='{self.name}', is_n_head={self.is_n_head})>"

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def get_db_session():
    """Get a new database session."""
    return Session()

def get_all_watchstanders() -> List[WatchstanderDB]:
    """Get all watchstanders from the database."""
    session = get_db_session()
    try:
        return session.query(WatchstanderDB).all()
    finally:
        session.close()

def calculate_total_availability(year: int, month: int) -> Tuple[int, Dict[str, int]]:
    """
    Calculate total available days for all watchstanders in a given month.
    Returns a tuple of (total_available_days, individual_available_days)
    where individual_available_days is a dict mapping watchstander names to their available days.
    """
    session = get_db_session()
    try:
        watchstanders = session.query(WatchstanderDB).all()
        month_key = f"{year:04d}-{month:02d}"
        total_available = 0
        individual_available = {}

        for ws in watchstanders:
            if month_key in ws.availability_vectors:
                vector = ws.availability_vectors[month_key]
                available_days = sum(1 for day in vector if day in [0, 4, 5, 6, 7, 8, 9])
                individual_available[ws.name] = available_days
                total_available += available_days

        return total_available, individual_available
    finally:
        session.close() 