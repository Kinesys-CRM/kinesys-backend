from pydantic import BaseModel, Field, field_validator
import re


class VisionOutput(BaseModel):
    receiver_name: str = Field(
        description="Full name of the mail recipient. Extract from 'To:' section."
    )
    receiver_address: str = Field(
        description="Complete street address of the recipient WITHOUT the pincode. Include building, street, area, city, state."
    )
    receiver_pincode: str = Field(
        description="Exactly 6-digit Indian postal code for the receiver. Must be a single pincode, not multiple values."
    )
    
    sender_name: str = Field(
        description="Full name of the mail sender. Extract from 'From:' section."
    )
    sender_address: str = Field(
        description="Complete street address of the sender WITHOUT the pincode. Include building, street, area, city, state."
    )
    sender_pincode: str = Field(
        description="Exactly 6-digit Indian postal code for the sender. Must be a single pincode, not multiple values."
    )

    @field_validator('*', mode='before')
    @classmethod
    def remove_null_bytes(cls, v):
        """Remove null bytes that PostgreSQL can't handle"""
        if isinstance(v, str):
            # Remove null bytes and other problematic characters
            v = v.replace('\x00', '').replace('\u0000', '')
        return v

    @field_validator('receiver_pincode', 'sender_pincode')
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        if not v or v.strip() == "":
            return ""
        
        v = v.strip()
        
        # If multiple pincodes detected, take only the first valid one
        if ',' in v or '/' in v or ' ' in v:
            parts = re.split(r'[,/\s]+', v)
            for part in parts:
                part = part.strip()
                if re.match(r'^\d{6}$', part):
                    return part
            return ""
        
        # Validate single pincode format (exactly 6 digits)
        if not re.match(r'^\d{6}$', v):
            match = re.search(r'\d{6}', v)
            if match:
                return match.group()
            return ""
        
        return v

    @field_validator('receiver_name', 'sender_name', 'receiver_address', 'sender_address')
    @classmethod
    def clean_string(cls, v: str) -> str:
        if not v:
            return ""
        # Remove null bytes and strip whitespace
        return v.replace('\x00', '').replace('\u0000', '').strip()