from pydantic import BaseModel


class RepositoryRequest(BaseModel):
    repository_url: str
