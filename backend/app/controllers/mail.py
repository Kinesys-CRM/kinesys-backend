from app.models.mail_model import Mail
from app.models.enums.enums import ProcessingStatus
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.services.r2_service import R2Service
from app.services.agent_service import AgentService
from app.services.pincode_lookup_service import PincodeLookupService
import requests

async def initialize_mail(user_id: UUID, file_key: str, db: AsyncSession) -> Mail:
    new_mail = Mail(
        user_id=user_id,
        image_s3_key=file_key,
        image_url="",
        status=ProcessingStatus.PENDING
    )
    db.add(new_mail)
    await db.commit()
    await db.refresh(new_mail)
    
    return new_mail


async def process_mail_task(mail_id: int, file_key: str, db: AsyncSession):

    mail_item = await db.get(Mail, mail_id)
    r2 = R2Service()
    agent = AgentService()
    lookup = PincodeLookupService()

    try:
        # Step 1: Set status to Processing
        mail_item.status = ProcessingStatus.PROCESSING
        db.add(mail_item)
        await db.commit()

        # Step 2: Give AI access to the image
        ai_url = r2.generate_read_url(file_key=file_key)
        extracted_data = await agent.run_agent(user_input="", image_url=ai_url)

        # Step 3: Map Data to Model
        mail_item.receiver_name = extracted_data.get("receiver_name")
        mail_item.receiver_address = extracted_data.get("receiver_address")
        mail_item.receiver_pincode = extracted_data.get("receiver_pincode")
        mail_item.sender_name = extracted_data.get("sender_name")
        mail_item.sender_address = extracted_data.get("sender_address")
        mail_item.sender_pincode = extracted_data.get("sender_pincode")
        mail_item.raw_ai_response = extracted_data

        # Step 4: Logic - Resolve Sorting Center (The "Lazy Loading" Logic)
        pincode = mail_item.receiver_pincode
        print(pincode)
        sorting_division = await lookup.resolve_sorting_center(extracted_pincode=pincode, db=db)

        mail_item.status = ProcessingStatus.COMPLETED
        mail_item.assigned_sorting_center = sorting_division
        
    except Exception as e:
        print(f"Error processing mail {mail_id}: {e}")
        mail_item.status = ProcessingStatus.FAILED
    
    finally:
        db.add(mail_item)
        await db.commit()

async def get_all_mails(user_id: UUID, db: AsyncSession, limit: int = 20, offset: int = 0) -> list[dict]:
    """Get all mails for a user with signed URLs"""
    r2 = R2Service()
    
    statement = (
        select(Mail)
        .where(Mail.user_id == user_id)
        .order_by(Mail.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.exec(statement)
    mails = result.all()
    
    response_list = []
    for mail in mails:
        temp_url = r2.generate_read_url(mail.image_s3_key)
        mail_dict = {
            "id": mail.id,
            "user_id": mail.user_id,
            "image_url": temp_url,
            "image_s3_key": mail.image_s3_key,
            "status": mail.status,
            "receiver_name": mail.receiver_name,
            "receiver_address": mail.receiver_address,
            "receiver_pincode": mail.receiver_pincode,
            "sender_name": mail.sender_name,
            "sender_address": mail.sender_address,
            "sender_pincode": mail.sender_pincode,
            "raw_ai_response": mail.raw_ai_response,
            "created_at": mail.created_at,
            "updated_at": mail.updated_at,
        }
        response_list.append(mail_dict)
    
    return response_list


async def get_mail_by_id(mail_id: UUID, user_id: UUID, db: AsyncSession) -> dict | None:
    """Get a specific mail by ID with signed URL"""
    r2 = R2Service()
    
    statement = (
        select(Mail)
        .where(Mail.id == mail_id)
        .where(Mail.user_id == user_id)
    )
    result = await db.exec(statement)
    mail = result.first()
    
    if not mail:
        return None
    
    temp_url = r2.generate_read_url(mail.image_s3_key)
    
    return {
        "id": mail.id,
        "user_id": mail.user_id,
        "image_url": temp_url,
        "image_s3_key": mail.image_s3_key,
        "status": mail.status,
        "receiver_name": mail.receiver_name,
        "receiver_address": mail.receiver_address,
        "receiver_pincode": mail.receiver_pincode,
        "sender_name": mail.sender_name,
        "sender_address": mail.sender_address,
        "sender_pincode": mail.sender_pincode,
        "raw_ai_response": mail.raw_ai_response,
        "created_at": mail.created_at,
        "updated_at": mail.updated_at,
    }