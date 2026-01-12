from pydantic import BaseModel, EmailStr


class EmailSendRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str
