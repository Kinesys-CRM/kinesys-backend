from app.models.pincode_cache_model import PincodeCache
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import requests

class PincodeLookupService():

    async def resolve_sorting_center(self, extracted_pincode: str, db: AsyncSession):
        # 1. Check Local Cache
        result = await db.exec(select(PincodeCache).where(PincodeCache.pincode == extracted_pincode))
        cached_info = result.first()
        
        if cached_info:
            return cached_info.sorting_division

        # 2. If missing, fetch from External API
        response = requests.get(f"https://api.postalpincode.in/pincode/{extracted_pincode}")
        data = response.json()

        if data[0]["Status"] == "Success":
            # The API returns a list of POs. Usually, the Division is consistent across them.
            # We pick the first one to determine routing.
            first_po = data[0]["PostOffice"][0]
            
            # Create new cache entry
            new_entry = PincodeCache(
                pincode=extracted_pincode,
                sorting_district=first_po.get("District"),
                sorting_division=first_po.get("Division"),
                state=first_po.get("State"),
                raw_api_data=data
            )
            db.add(new_entry)
            await db.commit()
            
            return new_entry.sorting_division
        
        return None

