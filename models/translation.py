from pydantic import BaseModel, Field

class TranslationMapElement(BaseModel):
    id: str = Field(..., description="Unique identifier for reconstruction. Do not modify.")
    text: str = Field(..., description="Original text with formatting tags like <i> or <b>")

class TranslationMap(BaseModel):
    elements: list[TranslationMapElement]