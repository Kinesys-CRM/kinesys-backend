"""Lead module Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enums import LeadSource, LeadStage, LeadTemperature


# ============== Tag Schemas ==============

class TagCreate(BaseModel):
    """Schema for creating a tag."""

    name: str = Field(max_length=50)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    """Schema for tag response."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    color: str


class TagWithIdResponse(TagResponse):
    """Tag response with ID."""

    id: UUID


# ============== Assignee Schema ==============

class AssigneeResponse(BaseModel):
    """Schema for assigned user in lead response."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    avatar: str | None = None


# ============== Lead Stage History Schemas ==============

class LeadStageHistoryResponse(BaseModel):
    """Schema for lead stage history response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    from_stage: LeadStage | None
    to_stage: LeadStage
    changed_by: UUID
    changed_at: datetime
    notes: str | None


# ============== Lead Schemas ==============

class LeadCreate(BaseModel):
    """Schema for creating a lead."""

    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    mobile_no: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    job_title: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    source: LeadSource = LeadSource.OTHER
    stage: LeadStage = LeadStage.NEW
    temperature: LeadTemperature = LeadTemperature.COLD
    lead_score: int = Field(default=0, ge=0, le=100)
    annual_revenue: str | None = None
    employee_count: str | None = None
    territory: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    interests: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    assigned_to: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v and not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v


class LeadUpdate(BaseModel):
    """Schema for updating a lead. All fields optional."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    mobile_no: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    job_title: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    source: LeadSource | None = None
    stage: LeadStage | None = None
    temperature: LeadTemperature | None = None
    lead_score: int | None = Field(default=None, ge=0, le=100)
    annual_revenue: str | None = None
    employee_count: str | None = None
    territory: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    interests: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    assigned_to: UUID | None = None
    tag_ids: list[UUID] | None = None
    stage_change_notes: str | None = None  # Notes for stage change history


class LeadResponse(BaseModel):
    """Schema for lead response matching frontend expectations."""

    model_config = ConfigDict(from_attributes=True)

    name: str  # lead identifier (could be ID or slug)
    first_name: str
    last_name: str
    lead_name: str
    email: str | None
    phone: str | None
    mobile_no: str | None
    company: str | None
    organization: str | None
    website: str | None
    job_title: str | None
    industry: str | None
    status: str
    stage: LeadStage
    temperature: LeadTemperature
    lead_score: int
    source: LeadSource
    annual_revenue: str | None
    employee_count: str | None
    territory: str | None
    notes: str | None
    interests: list[str]
    custom_fields: dict[str, Any]
    lead_owner: str | None  # Owner email
    assigned_to: AssigneeResponse | None
    created_at: datetime
    creation: datetime  # Alias for created_at
    modified: datetime
    last_activity_at: datetime | None
    tags: list[TagResponse]
    _email_count: int = 0
    _note_count: int = 0
    _task_count: int = 0
    _comment_count: int = 0

    @model_validator(mode="before")
    @classmethod
    def build_response(cls, data: Any) -> Any:
        """Transform Lead model to response format."""
        if hasattr(data, "__dict__"):
            # It's a model instance
            lead = data
            return {
                "name": str(lead.id),
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "lead_name": lead.lead_name,
                "email": lead.email,
                "phone": lead.phone,
                "mobile_no": lead.mobile_no,
                "company": lead.company,
                "organization": lead.organization,
                "website": lead.website,
                "job_title": lead.job_title,
                "industry": lead.industry,
                "status": lead.status,
                "stage": lead.stage,
                "temperature": lead.temperature,
                "lead_score": lead.lead_score,
                "source": lead.source,
                "annual_revenue": lead.annual_revenue,
                "employee_count": lead.employee_count,
                "territory": lead.territory,
                "notes": lead.notes,
                "interests": lead.interests or [],
                "custom_fields": lead.custom_fields or {},
                "lead_owner": lead.owner.email if hasattr(lead, "owner") and lead.owner else None,
                "assigned_to": _build_assignee(lead),
                "created_at": lead.created_at,
                "creation": lead.created_at,
                "modified": lead.modified,
                "last_activity_at": lead.last_activity_at,
                "tags": [{"name": t.name, "color": t.color} for t in (lead.tags or [])],
                "_email_count": getattr(lead, "_email_count", 0),
                "_note_count": getattr(lead, "_note_count", 0),
                "_task_count": getattr(lead, "_task_count", 0),
                "_comment_count": getattr(lead, "_comment_count", 0),
            }
        return data


def _build_assignee(lead: Any) -> AssigneeResponse | None:
    """Build assignee response from lead."""
    if not hasattr(lead, "assignee") or not lead.assignee:
        return None
    assignee = lead.assignee
    return AssigneeResponse(
        name=getattr(assignee, "full_name", assignee.email),
        email=assignee.email,
        avatar=getattr(assignee, "picture_url", None),
    )


class LeadListResponse(BaseModel):
    """Paginated response for leads list."""

    data: list[LeadResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class LeadsByStageResponse(BaseModel):
    """Response for leads grouped by stage."""

    new: list[LeadResponse] = Field(default_factory=list)
    contacted: list[LeadResponse] = Field(default_factory=list)
    qualified: list[LeadResponse] = Field(default_factory=list)
    proposal: list[LeadResponse] = Field(default_factory=list)
    negotiation: list[LeadResponse] = Field(default_factory=list)
    won: list[LeadResponse] = Field(default_factory=list)
    lost: list[LeadResponse] = Field(default_factory=list)


# ============== Stage/Status Metadata ==============

class LeadStageInfo(BaseModel):
    """Info about a lead stage."""

    name: str
    label: str
    color: str


class LeadStatusInfo(BaseModel):
    """Info about a lead status."""

    name: str
    color: str
