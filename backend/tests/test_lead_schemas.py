"""Tests for lead Pydantic schema validation and serialization."""

import pytest
from uuid import uuid4

from pydantic import ValidationError

from app.models.enums import LeadSource, LeadStage, LeadTemperature
from app.schemas.lead_schema import LeadCreate, LeadUpdate, TagCreate


class TestLeadCreate:
    """Validation tests for lead creation schema."""

    def test_minimal_valid_lead(self):
        lead = LeadCreate(first_name="John", last_name="Doe")
        assert lead.first_name == "John"
        assert lead.stage == LeadStage.NEW
        assert lead.temperature == LeadTemperature.COLD
        assert lead.source == LeadSource.OTHER
        assert lead.lead_score == 0

    def test_full_lead_with_all_fields(self):
        tag_id = uuid4()
        assignee_id = uuid4()
        lead = LeadCreate(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone="+1234567890",
            company="Acme Corp",
            organization="Acme",
            website="acme.com",
            job_title="CTO",
            industry="Technology",
            source=LeadSource.LINKEDIN,
            stage=LeadStage.QUALIFIED,
            temperature=LeadTemperature.HOT,
            lead_score=85,
            territory="North America",
            notes="Met at conference",
            interests=["AI", "Cloud"],
            custom_fields={"budget": "100k"},
            assigned_to=assignee_id,
            tag_ids=[tag_id],
        )
        assert lead.email == "jane@example.com"
        assert lead.interests == ["AI", "Cloud"]
        assert lead.custom_fields == {"budget": "100k"}

    def test_website_auto_prepends_https(self):
        lead = LeadCreate(first_name="A", last_name="B", website="example.com")
        assert lead.website == "https://example.com"

    def test_website_preserves_existing_scheme(self):
        lead = LeadCreate(first_name="A", last_name="B", website="http://example.com")
        assert lead.website == "http://example.com"

    def test_rejects_missing_first_name(self):
        with pytest.raises(ValidationError):
            LeadCreate(last_name="Doe")

    def test_rejects_missing_last_name(self):
        with pytest.raises(ValidationError):
            LeadCreate(first_name="John")

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            LeadCreate(first_name="A", last_name="B", email="not-an-email")

    def test_rejects_lead_score_out_of_range(self):
        with pytest.raises(ValidationError):
            LeadCreate(first_name="A", last_name="B", lead_score=101)
        with pytest.raises(ValidationError):
            LeadCreate(first_name="A", last_name="B", lead_score=-1)

    def test_model_dump_serializes_enums_to_values(self):
        lead = LeadCreate(
            first_name="A",
            last_name="B",
            source=LeadSource.LINKEDIN,
            stage=LeadStage.PROPOSAL,
            temperature=LeadTemperature.WARM,
        )
        data = lead.model_dump()
        assert data["source"] == "LinkedIn"
        assert data["stage"] == "proposal"
        assert data["temperature"] == "warm"

    def test_defaults_empty_lists_and_dicts(self):
        lead = LeadCreate(first_name="A", last_name="B")
        assert lead.interests == []
        assert lead.custom_fields == {}
        assert lead.tag_ids == []


class TestLeadUpdate:
    """Validation tests for lead update schema."""

    def test_partial_update_only_changed_fields(self):
        update = LeadUpdate(stage=LeadStage.WON, stage_change_notes="Closed deal")
        data = update.model_dump(exclude_unset=True)
        assert "stage" in data
        assert "stage_change_notes" in data
        assert "first_name" not in data

    def test_enum_serialization_in_update(self):
        update = LeadUpdate(temperature=LeadTemperature.HOT)
        data = update.model_dump(exclude_unset=True)
        assert data["temperature"] == "hot"

    def test_all_fields_optional(self):
        update = LeadUpdate()
        data = update.model_dump(exclude_unset=True)
        assert data == {}


class TestTagCreate:
    """Validation tests for tag schema."""

    def test_valid_tag(self):
        tag = TagCreate(name="VIP", color="#FF5733")
        assert tag.name == "VIP"
        assert tag.color == "#FF5733"

    def test_default_color(self):
        tag = TagCreate(name="Test")
        assert tag.color == "#3B82F6"

    def test_rejects_invalid_color(self):
        with pytest.raises(ValidationError):
            TagCreate(name="Bad", color="red")

    def test_rejects_long_name(self):
        with pytest.raises(ValidationError):
            TagCreate(name="x" * 51)
