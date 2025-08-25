from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str

class DocumentRequest(BaseModel):
    name: str
    pdf: str


