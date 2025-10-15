# app/models.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class GenerateRequest(BaseModel):
    """Модель запиту на генерацію сайтів."""
    
    topic: str = Field(
        ..., 
        min_length=3,
        max_length=200,
        description="Topic for website generation"
    )
    
    pages_count: int = Field(
        1, 
        ge=1, 
        le=30,
        description="Number of pages to generate (1-50)"
    )
    
    style: str = Field(
        default="educational",
        description="Content style: educational, marketing, technical, minimalist, creative, casual"
    )
    
    max_tokens: int = Field(
        default=1200,
        ge=500,
        le=3000,
        description="Maximum tokens for content generation"
    )
    
    temperature: float = Field(
        default=0.8,
        ge=0.1,
        le=1.5,
        description="Temperature for LLM (0.1-1.5, higher = more creative)"
    )
    
    top_p: float = Field(
        default=0.95,
        ge=0.1,
        le=1.0,
        description="Top-p sampling parameter"
    )
    
    generate_image: bool = Field(
        default=True,
        description="Whether to generate an image for the site"
    )
    
    # НОВЕ ПОЛЕ
    randomize_temperature: bool = Field(
        default=False,
        description="If True, randomly varies temperature for each generation (0.5-1.2 range)"
    )
    
    temperature_min: float = Field(
        default=0.5,
        ge=0.1,
        le=1.5,
        description="Minimum temperature when randomizing"
    )
    
    temperature_max: float = Field(
        default=1.2,
        ge=0.1,
        le=1.5,
        description="Maximum temperature when randomizing"
    )
    
    @field_validator('style')
    @classmethod
    def validate_style(cls, v: str) -> str:
        """Валідація та нормалізація стилю."""
        allowed_styles = [
            "educational", "marketing", "technical", 
            "minimalist", "creative", "casual"
        ]
        v_lower = v.lower().strip()
        
        if v_lower not in allowed_styles:
            raise ValueError(
                f"Style must be one of: {', '.join(allowed_styles)}. Got: {v}"
            )
        return v_lower
    
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Валідація та очищення topic."""
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Topic must be at least 3 characters long")
        
        # Перевірка на підозрілий контент (базова)
        forbidden_words = ['hack', 'exploit', 'malware', 'virus']
        if any(word in v.lower() for word in forbidden_words):
            raise ValueError("Topic contains forbidden keywords")
        
        return v
    
    @field_validator('temperature_max')
    @classmethod
    def validate_temp_range(cls, v: float, info) -> float:
        """Перевіряє, що temperature_max > temperature_min."""
        if 'temperature_min' in info.data:
            temp_min = info.data['temperature_min']
            if v <= temp_min:
                raise ValueError(f"temperature_max ({v}) must be greater than temperature_min ({temp_min})")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Machine Learning",
                "pages_count": 3,
                "style": "educational",
                "max_tokens": 1200,
                "temperature": 0.8,
                "top_p": 0.95,
                "generate_image": True,
                "randomize_temperature": True,
                "temperature_min": 0.5,
                "temperature_max": 1.2
            }
        }