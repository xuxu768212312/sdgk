from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SubjectCheckRequest(BaseModel):
    year: int | None = 2026
    edition: str | None = None
    level: str = "本科"
    subjects: str | list[str]
    school_code: str | None = None
    major_code: str | None = None
    school_name: str | None = None
    major_name: str | None = None


class RegionCheckRequest(BaseModel):
    regions: str | list[str]
    school_name: str | None = None
    school_code: str | None = None


class CandidateGenerateRequest(BaseModel):
    profile: dict[str, Any]
    hard_region: bool = False


class PlanGenerateRequest(BaseModel):
    profile: dict[str, Any] | None = None
    student_file: str | None = None
    out_dir: str | None = None
    risk_profile: Literal["conservative", "standard", "aggressive", "opportunistic"] = "standard"
    hard_region: bool = False
    slots: int = Field(default=96, ge=1, le=96)


class SearchRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=20, ge=1, le=200)
