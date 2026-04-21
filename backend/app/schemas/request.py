from pydantic import BaseModel
from typing import Literal


class RepositoryRequest(BaseModel):
    repository_url: str
    force_regenerate: bool = False
    ai_section: Literal["all", "readme_summary", "recommendations", "risk_observations"] = "all"
