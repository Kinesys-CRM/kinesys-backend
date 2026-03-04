"""Pydantic schemas for lead request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enums import LeadSource, LeadStage, LeadTemperature


# --- Tag Schemas ---

class TagCreate(BaseModel):
    name: str = Field(max_length=50)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    color: str


class TagWithIdResponse(TagResponse):
    id: UUID


# --- Assignee Schema ---

class AssigneeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: str
    avatar: str | None = None


# --- Lead Stage History ---

class LeadStageHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    lead_id: UUID
    from_stage: str | None
    to_stage: str
    changed_by: UUID
    changed_at: datetime
    notes: str | None


# --- Lead Schemas ---

def _serialize_enum(value):
    """Convert enum to its string value for DB storage."""
    if value is not None and hasattr(value, "value"):
        return value.value
    return value


class LeadCreate(BaseModel):
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

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        for field in ("source", "stage", "temperature"):
            if field in data:
                data[field] = _serialize_enum(data[field])
        return data


class LeadUpdate(BaseModel):
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
    stage_change_notes: str | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        for field in ("source", "stage", "temperature"):
            if field in data:
                data[field] = _serialize_enum(data[field])
        return data


def _build_assignee(lead: Any) -> AssigneeResponse | None:
    if not hasattr(lead, "assignee") or not lead.assignee:
        return None
    assignee = lead.assignee
    return AssigneeResponse(
        name=getattr(assignee, "full_name", assignee.email),
        email=assignee.email,
        avatar=getattr(assignee, "picture_url", None),
    )


class LeadResponse(BaseModel):
    """Response schema for a single lead."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
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
    stage: str
    temperature: str
    lead_score: int
    source: str
    annual_revenue: str | None
    employee_count: str | None
    territory: str | None
    notes: str | None
    interests: list[str]
    custom_fields: dict[str, Any]
    lead_owner: str | None
    assigned_to: AssigneeResponse | None
    created_at: datetime
    creation: datetime
    modified: datetime
    last_activity_at: datetime | None
    tags: list[TagResponse]

    @model_validator(mode="before")
    @classmethod
    def build_response(cls, data: Any) -> Any:
        """Transform ORM Lead model to response dict."""
        if not hasattr(data, "__dict__"):
            return data

        lead = data
        lead_id = str(lead.id)
        return {
            "id": lead_id,
            "name": lead_id,
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
        }


class LeadListResponse(BaseModel):
    data: list[LeadResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class LeadsByStageResponse(BaseModel):
    new: list[LeadResponse] = Field(default_factory=list)
    contacted: list[LeadResponse] = Field(default_factory=list)
    qualified: list[LeadResponse] = Field(default_factory=list)
    proposal: list[LeadResponse] = Field(default_factory=list)
    negotiation: list[LeadResponse] = Field(default_factory=list)
    won: list[LeadResponse] = Field(default_factory=list)
    lost: list[LeadResponse] = Field(default_factory=list)


# --- Metadata Schemas ---

class LeadStageInfo(BaseModel):
    name: str
    label: str
    color: str


class LeadStatusInfo(BaseModel):
    name: str
    color: str


class LeadSourceInfo(BaseModel):
    value: str
    label: str


class LeadTemperatureInfo(BaseModel):
    value: str
    label: str
    color: str


class LeadIndustryInfo(BaseModel):
    value: str
    label: str


class LeadTerritoryInfo(BaseModel):
    value: str
    label: str


class EmployeeCountInfo(BaseModel):
    value: str
    label: str


class LeadMetadataResponse(BaseModel):
    stages: list[LeadStageInfo]
    sources: list[LeadSourceInfo]
    temperatures: list[LeadTemperatureInfo]
    industries: list[LeadIndustryInfo]
    territories: list[LeadTerritoryInfo]
    employee_counts: list[EmployeeCountInfo]
