"""CRUD operations for leads and tags."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.enums import LeadStage
from app.models.lead_model import Lead, LeadStageHistory, LeadTagLink, Tag
from app.schemas.lead_schema import LeadCreate, LeadUpdate


async def get_leads(
    db: AsyncSession,
    user_id: UUID,
    *,
    search: str | None = None,
    stage: LeadStage | None = None,
    temperature: str | None = None,
    source: str | None = None,
    lead_owner: str | None = None,
    tags: list[str] | None = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Lead], int]:
    query = (
        select(Lead)
        .where(Lead.user_id == user_id, Lead.is_active == True)
        .options(selectinload(Lead.tags), selectinload(Lead.owner), selectinload(Lead.assignee))
    )

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Lead.first_name.ilike(term),
                Lead.last_name.ilike(term),
                Lead.email.ilike(term),
                Lead.company.ilike(term),
                Lead.organization.ilike(term),
            )
        )

    if stage:
        stage_value = stage.value if hasattr(stage, "value") else stage
        query = query.where(Lead.stage == stage_value)

    if temperature:
        query = query.where(Lead.temperature == temperature)

    if source:
        query = query.where(Lead.source == source)

    if lead_owner:
        from app.models.user_model import User
        query = query.join(User, Lead.assigned_to == User.id).where(User.email == lead_owner)

    if tags:
        query = query.join(LeadTagLink).join(Tag).where(Tag.name.in_(tags))

    # Count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.exec(count_query)
    total_count = total_result.one()

    # Ordering
    order_column = getattr(Lead, order_by, Lead.created_at)
    if order_dir.lower() == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.exec(query)
    leads = result.unique().all()

    return list(leads), total_count


async def get_lead(db: AsyncSession, lead_id: UUID, user_id: UUID) -> Lead:
    query = (
        select(Lead)
        .where(Lead.id == lead_id, Lead.user_id == user_id, Lead.is_active == True)
        .options(
            selectinload(Lead.tags),
            selectinload(Lead.owner),
            selectinload(Lead.assignee),
            selectinload(Lead.stage_history),
        )
    )
    result = await db.exec(query)
    lead = result.first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with id {lead_id} not found",
        )
    return lead


async def create_lead(db: AsyncSession, lead_in: LeadCreate, user_id: UUID) -> Lead:
    tag_ids = lead_in.tag_ids
    lead_data = lead_in.model_dump(exclude={"tag_ids"})

    lead = Lead(**lead_data, user_id=user_id)
    db.add(lead)
    await db.flush()

    if tag_ids:
        await _update_lead_tags(db, lead.id, tag_ids, user_id)

    await db.commit()
    await db.refresh(lead)
    return await get_lead(db, lead.id, user_id)


async def update_lead(
    db: AsyncSession,
    lead_id: UUID,
    lead_in: LeadUpdate,
    user_id: UUID,
    changed_by: UUID,
) -> Lead:
    lead = await get_lead(db, lead_id, user_id)
    old_stage = lead.stage

    update_data = lead_in.model_dump(exclude_unset=True, exclude={"tag_ids", "stage_change_notes"})
    for field, value in update_data.items():
        setattr(lead, field, value)

    lead.last_activity_at = datetime.now(timezone.utc)

    # Track stage changes
    new_stage = lead_in.stage.value if hasattr(lead_in.stage, "value") else lead_in.stage
    if new_stage and new_stage != old_stage:
        await _record_stage_change(
            db,
            lead_id=lead.id,
            from_stage=old_stage,
            to_stage=new_stage,
            changed_by=changed_by,
            notes=lead_in.stage_change_notes,
        )

    if lead_in.tag_ids is not None:
        await _update_lead_tags(db, lead.id, lead_in.tag_ids, user_id)

    await db.commit()
    await db.refresh(lead)
    return await get_lead(db, lead.id, user_id)


async def delete_lead(db: AsyncSession, lead_id: UUID, user_id: UUID) -> bool:
    lead = await get_lead(db, lead_id, user_id)
    lead.deleted_at = datetime.now(timezone.utc)
    lead.is_active = False
    await db.commit()
    return True


async def get_leads_by_stage(db: AsyncSession, user_id: UUID) -> dict[str, list[Lead]]:
    query = (
        select(Lead)
        .where(Lead.user_id == user_id, Lead.is_active == True)
        .options(selectinload(Lead.tags), selectinload(Lead.owner), selectinload(Lead.assignee))
        .order_by(Lead.created_at.desc())
    )

    result = await db.exec(query)
    leads = result.unique().all()

    grouped: dict[str, list[Lead]] = {stage.value: [] for stage in LeadStage}
    for lead in leads:
        stage_key = lead.stage if isinstance(lead.stage, str) else lead.stage.value
        if stage_key in grouped:
            grouped[stage_key].append(lead)

    return grouped


async def _record_stage_change(
    db: AsyncSession,
    lead_id: UUID,
    from_stage: str | None,
    to_stage: str,
    changed_by: UUID,
    notes: str | None = None,
) -> LeadStageHistory:
    from_str = from_stage.value if hasattr(from_stage, "value") else from_stage
    to_str = to_stage.value if hasattr(to_stage, "value") else to_stage

    history = LeadStageHistory(
        lead_id=lead_id,
        from_stage=from_str,
        to_stage=to_str,
        changed_by=changed_by,
        notes=notes,
    )
    db.add(history)
    await db.flush()
    return history


async def _update_lead_tags(
    db: AsyncSession,
    lead_id: UUID,
    tag_ids: list[UUID],
    user_id: UUID,
) -> None:
    # Remove existing links
    result = await db.exec(select(LeadTagLink).where(LeadTagLink.lead_id == lead_id))
    for link in result.all():
        await db.delete(link)

    # Add new links (only for tags belonging to this user)
    if tag_ids:
        tags_result = await db.exec(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        )
        for tag in tags_result.all():
            db.add(LeadTagLink(lead_id=lead_id, tag_id=tag.id))


# --- Tag CRUD ---

async def get_tags(db: AsyncSession, user_id: UUID) -> list[Tag]:
    result = await db.exec(select(Tag).where(Tag.user_id == user_id).order_by(Tag.name))
    return list(result.all())


async def create_tag(db: AsyncSession, name: str, color: str, user_id: UUID) -> Tag:
    tag = Tag(name=name, color=color, user_id=user_id)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag_id: UUID, user_id: UUID) -> bool:
    result = await db.exec(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
    tag = result.first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )
    await db.delete(tag)
    await db.commit()
    return True
