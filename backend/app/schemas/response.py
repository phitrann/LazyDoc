from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LanguageItem(BaseModel):
    name: str
    percentage: float


class Overview(BaseModel):
    name: str
    owner: str
    description: str | None = None
    stars: int
    forks: int
    last_updated: datetime | None = None
    url: str
    default_branch: str


class Insights(BaseModel):
    primary_language: str | None = None
    languages: list[LanguageItem] = []
    license_name: str | None = None
    has_license: bool = False
    dependency_files: list[str] = []


class Activity(BaseModel):
    recent_commits_last_7_days: int
    recent_commits_last_30_days: int
    last_commit_date: datetime | None = None
    total_contributors: int
    active_contributors_last_30_days: int


class Structure(BaseModel):
    total_files: int
    has_readme: bool
    has_license: bool
    top_directories: list[str] = []


class ResearchData(BaseModel):
    overview: Overview
    insights: Insights
    activity: Activity
    structure: Structure


class RateLimit(BaseModel):
    remaining: int
    limit: int
    reset_unix_timestamp: int
    reset_in_seconds: int


class ResearchSuccessResponse(BaseModel):
    status: Literal["success", "partial"]
    data: ResearchData
    warnings: list[str] = []
    rate_limit: RateLimit | None = None


class APIErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_code: str
    message: str
    retry_after_seconds: int | None = None


class DocumentationSection(BaseModel):
    title: str
    summary: str
    content: list[str]


class DocumentationData(BaseModel):
    overview: Overview
    insights: Insights
    activity: Activity
    structure: Structure
    sections: list[DocumentationSection]
    markdown: str
    readme_summary: str | None = None
    recommendations: list[str] = []
    risk_observations: list[str] = []


class DocumentationSuccessResponse(BaseModel):
    status: Literal["success", "partial"]
    data: DocumentationData
    warnings: list[str] = []
    rate_limit: RateLimit | None = None
