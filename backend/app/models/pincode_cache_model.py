from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from datetime import datetime

class PincodeCache(SQLModel, table=True):
    """
    Acts as a local cache for the external API.
    We only fetch from the API if the pincode is NOT in this table.
    """
    __tablename__ = "pincode_cache"

    pincode: str = Field(primary_key=True, index=True)
    
    sorting_district: str  # e.g., "Hyderabad"
    sorting_division: str  # e.g., "Hyderabad City"
    state: str             # e.g., "Telangana"
    
    raw_api_data: list | dict = Field(default={}, sa_column=Column(JSON))
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)