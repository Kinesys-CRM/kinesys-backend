from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"       # Uploaded to S3, waiting for Agent
    PROCESSING = "processing" # Agent is currently "looking" at it
    COMPLETED = "completed"   # Data extracted successfully
    FAILED = "failed"