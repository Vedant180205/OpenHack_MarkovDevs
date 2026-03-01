from pydantic import BaseModel, Field
from typing import List

class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., description="The user prompt describing a business practice.")

class AnalyzeResponse(BaseModel):
    harmful: bool = Field(..., description="True if a violation occurred, False otherwise.")
    articles: List[str] = Field(..., description="List of violated CCPA sections. Must be empty if harmful is False.")