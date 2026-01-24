from app.services.r2_service import R2Service
from uuid import uuid4, UUID

async def genarate_upload_url(user_id: UUID):

    r2 = R2Service()
    file_key = f"user_uploads/{user_id}/{uuid4()}.jpg"
    
    upload_url = r2.generate_upload_url(file_key)
    
    return {
        "upload_url": upload_url, # Flutter uploads here
        "file_key": file_key      # Flutter sends this back in step 2
    }
