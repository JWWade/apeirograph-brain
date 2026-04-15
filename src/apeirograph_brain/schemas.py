from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


ALLOWED_TENSION_LEVELS = {"low", "medium", "high"}
ALLOWED_STABILITY_LEVELS = {"stable", "balanced", "adventurous"}


def _normalize_pitch_classes(values: List[int]) -> List[int]:
    normalized = sorted({int(value) % 12 for value in values})
    if not normalized:
        raise ValueError("pitch_classes must contain at least one pitch class")
    return normalized


class ChordObject(BaseModel):
    root: str = Field(..., min_length=1)
    quality: str = Field(..., min_length=1)
    pitch_classes: List[int] = Field(..., min_items=1, max_items=12)
    label: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @validator("pitch_classes")
    def normalize_pitch_classes(cls, value: List[int]) -> List[int]:
        return _normalize_pitch_classes(value)


class ScaleContext(BaseModel):
    root: str = Field(..., min_length=1)
    mode: str = Field(..., min_length=1)
    diatonic_pitch_classes: List[int] = Field(..., min_items=1, max_items=12)

    @validator("diatonic_pitch_classes")
    def normalize_scale_pitch_classes(cls, value: List[int]) -> List[int]:
        return _normalize_pitch_classes(value)


class HarmonicTransform(BaseModel):
    operation: str = Field(..., min_length=1)
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ProgressionInput(BaseModel):
    chords: List[ChordObject] = Field(..., min_items=1)
    scale_context: Optional[ScaleContext] = None
    transform: Optional[HarmonicTransform] = None
    intent: Optional[str] = None


class ExplanationResponse(BaseModel):
    summary: str = Field(..., min_length=1)
    salient_properties: List[str] = Field(default_factory=list)
    tension_level: str = "medium"
    symmetry_note: str = Field(..., min_length=1)
    motion_note: str = Field(..., min_length=1)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    caveats: List[str] = Field(default_factory=list)

    @validator("tension_level")
    def validate_tension_level(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in ALLOWED_TENSION_LEVELS:
            raise ValueError("tension_level must be one of: low, medium, high")
        return normalized


class SuggestionCandidate(BaseModel):
    label: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    stability: str = "balanced"
    next_chord: ChordObject
    transform_hint: Optional[HarmonicTransform] = None

    @validator("stability")
    def validate_stability(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in ALLOWED_STABILITY_LEVELS:
            raise ValueError("stability must be one of: stable, balanced, adventurous")
        return normalized


class SuggestionResponse(BaseModel):
    advisory_note: str = Field(..., min_length=1)
    suggestions: List[SuggestionCandidate] = Field(..., min_items=1)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    caveats: List[str] = Field(default_factory=list)
