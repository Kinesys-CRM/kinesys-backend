"""Lead management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.crud import lead_crud
from app.models.enums import (
    EmployeeCount,
    LeadIndustry,
    LeadSource,
    LeadStage,
    LeadTemperature,
    LeadTerritory,
)
from app.models.user_model import User
from app.schemas.lead_schema import (
    EmployeeCountInfo,
    LeadCreate,
    LeadIndustryInfo,
    LeadListResponse,
    LeadMetadataResponse,
    LeadResponse,
    LeadsByStageResponse,
    LeadSourceInfo,
    LeadStageInfo,
    LeadStatusInfo,
    LeadTemperatureInfo,
    LeadTerritoryInfo,
    LeadUpdate,
    TagCreate,
    TagWithIdResponse,
)

router = APIRouter()


# --- Lead CRUD ---

@router.get("", response_model=LeadListResponse)
async def list_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    stage: LeadStage | None = Query(default=None),
    temperature: LeadTemperature | None = Query(default=None),
    lead_owner: str | None = Query(default=None),
    source: LeadSource | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma-separated tag names"),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> LeadListResponse:
    """Get paginated leads with optional filters."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    # Map status label to stage enum if stage not explicitly set
    filter_stage = stage
    if status and not stage:
        status_to_stage = {s.label.lower(): s for s in LeadStage}
        filter_stage = status_to_stage.get(status.lower())

    leads, total_count = await lead_crud.get_leads(
        db,
        user_id=current_user.id,
        search=search,
        stage=filter_stage,
        temperature=temperature.value if temperature else None,
        source=source.value if source else None,
        lead_owner=lead_owner,
        tags=tag_list,
        order_by=order_by,
        order_dir=order_dir,
        page=page,
        page_size=page_size,
    )

    total_pages = (total_count + page_size - 1) // page_size

    return LeadListResponse(
        data=[LeadResponse.model_validate(lead) for lead in leads],
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/by-stage", response_model=LeadsByStageResponse)
async def get_leads_by_stage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadsByStageResponse:
    """Get all leads grouped by pipeline stage."""
    grouped = await lead_crud.get_leads_by_stage(db, user_id=current_user.id)

    return LeadsByStageResponse(
        **{
            stage.value: [LeadResponse.model_validate(l) for l in grouped.get(stage.value, [])]
            for stage in LeadStage
        }
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadResponse:
    lead = await lead_crud.get_lead(db, lead_id=lead_id, user_id=current_user.id)
    return LeadResponse.model_validate(lead)


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(
    lead_in: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadResponse:
    lead = await lead_crud.create_lead(db, lead_in=lead_in, user_id=current_user.id)
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_in: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadResponse:
    """Update a lead. Stage changes are tracked in history."""
    lead = await lead_crud.update_lead(
        db,
        lead_id=lead_id,
        lead_in=lead_in,
        user_id=current_user.id,
        changed_by=current_user.id,
    )
    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Soft delete a lead."""
    await lead_crud.delete_lead(db, lead_id=lead_id, user_id=current_user.id)
    return {"success": True}


# --- Metadata Endpoints ---

@router.get("/meta/stages", response_model=list[LeadStageInfo])
async def get_lead_stages() -> list[LeadStageInfo]:
    return [
        LeadStageInfo(name=s.value, label=s.label, color=s.color)
        for s in LeadStage
    ]


@router.get("/meta/statuses", response_model=list[LeadStatusInfo])
async def get_lead_statuses() -> list[LeadStatusInfo]:
    return [
        LeadStatusInfo(name=s.label, color=s.color)
        for s in LeadStage
    ]


@router.get("/meta/sources", response_model=list[LeadSourceInfo])
async def get_lead_sources() -> list[LeadSourceInfo]:
    return [LeadSourceInfo(value=s.value, label=s.value) for s in LeadSource]


@router.get("/meta/temperatures", response_model=list[LeadTemperatureInfo])
async def get_lead_temperatures() -> list[LeadTemperatureInfo]:
    return [
        LeadTemperatureInfo(value=t.value, label=t.label, color=t.color)
        for t in LeadTemperature
    ]


@router.get("/meta/industries", response_model=list[LeadIndustryInfo])
async def get_lead_industries() -> list[LeadIndustryInfo]:
    return [LeadIndustryInfo(value=i.value, label=i.value) for i in LeadIndustry]


@router.get("/meta/territories", response_model=list[LeadTerritoryInfo])
async def get_lead_territories() -> list[LeadTerritoryInfo]:
    return [LeadTerritoryInfo(value=t.value, label=t.value) for t in LeadTerritory]


@router.get("/meta/employee-counts", response_model=list[EmployeeCountInfo])
async def get_employee_counts() -> list[EmployeeCountInfo]:
    return [EmployeeCountInfo(value=ec.value, label=ec.value) for ec in EmployeeCount]


@router.get("/meta/all", response_model=LeadMetadataResponse)
async def get_all_metadata() -> LeadMetadataResponse:
    """Combined metadata for populating frontend dropdowns."""
    return LeadMetadataResponse(
        stages=[
            LeadStageInfo(name=s.value, label=s.label, color=s.color) for s in LeadStage
        ],
        sources=[
            LeadSourceInfo(value=s.value, label=s.value) for s in LeadSource
        ],
        temperatures=[
            LeadTemperatureInfo(value=t.value, label=t.label, color=t.color)
            for t in LeadTemperature
        ],
        industries=[
            LeadIndustryInfo(value=i.value, label=i.value) for i in LeadIndustry
        ],
        territories=[
            LeadTerritoryInfo(value=t.value, label=t.value) for t in LeadTerritory
        ],
        employee_counts=[
            EmployeeCountInfo(value=ec.value, label=ec.value) for ec in EmployeeCount
        ],
    )


# --- Tag Endpoints ---

@router.get("/tags", response_model=list[TagWithIdResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TagWithIdResponse]:
    tags = await lead_crud.get_tags(db, user_id=current_user.id)
    return [TagWithIdResponse.model_validate(tag) for tag in tags]


@router.post("/tags", response_model=TagWithIdResponse, status_code=201)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TagWithIdResponse:
    tag = await lead_crud.create_tag(
        db, name=tag_in.name, color=tag_in.color, user_id=current_user.id,
    )
    return TagWithIdResponse.model_validate(tag)


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await lead_crud.delete_tag(db, tag_id=tag_id, user_id=current_user.id)
    return {"success": True}
