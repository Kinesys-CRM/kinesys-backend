from enum import Enum, StrEnum


class ProcessingStatus(str, Enum):
    PENDING = "pending"       # Uploaded to S3, waiting for Agent
    PROCESSING = "processing" # Agent is currently "looking" at it
    COMPLETED = "completed"   # Data extracted successfully
    FAILED = "failed"


class LeadSource(StrEnum):
    WEBSITE = "Website"
    LINKEDIN = "LinkedIn"
    REFERRAL = "Referral"
    TRADE_SHOW = "TradeShow"
    COLD_CALL = "ColdCall"
    ADVERTISEMENT = "Advertisement"
    PARTNER = "Partner"
    OTHER = "Other"


class LeadStage(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

    @property
    def label(self) -> str:
        return self.value.capitalize()

    @property
    def color(self) -> str:
        colors = {
            "new": "#6B7280",
            "contacted": "#3B82F6",
            "qualified": "#10B981",
            "proposal": "#F59E0B",
            "negotiation": "#8B5CF6",
            "won": "#059669",
            "lost": "#EF4444",
        }
        return colors.get(self.value, "#6B7280")


class LeadTemperature(StrEnum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"