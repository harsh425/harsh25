from pydantic import BaseModel
from typing import Optional


class ContractCreate(BaseModel):
    employee_number: str
    contract_type: str
    contract_content: str
    expires_at: Optional[str] = None


class ContractSign(BaseModel):
    signature_data: str
