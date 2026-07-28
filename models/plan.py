

from __future__ import annotations

from pydantic import BaseModel, Field


class RepositoryAnalysis(BaseModel):
    """Structured understanding of the target repository."""

    framework: str = Field(description="Primary framework/runtime, e.g. Express, Fastify")
    database: str = Field(default="unknown", description="Database or storage layer in use")
    entry_point: str = Field(description="Relative path to the app's entry file")
    models: list[str] = Field(default_factory=list, description="Relative paths of data model files")
    controllers: list[str] = Field(default_factory=list, description="Relative paths of controller/handler files")
    routes: list[str] = Field(default_factory=list, description="Relative paths of route definition files")
    config_files: list[str] = Field(default_factory=list, description="Relative paths of configuration files")
    notes: str = Field(default="", description="Any other useful architectural observations")


class ImplementationPlan(BaseModel):
    """The plan produced by the Planner before any code is touched."""

    reasoning: str = Field(description="Why this approach satisfies the request with minimal change")
    features: list[str] = Field(description="Discrete features/behaviors to implement")
    files_to_modify: list[str] = Field(description="Relative paths of files that must change")
    steps: list[str] = Field(description="Ordered execution steps the editor should follow")


class FileEdit(BaseModel):
    """Result of editing a single file."""

    path: str
    original_content: str
    updated_content: str

    @property
    def changed(self) -> bool:
        return self.original_content != self.updated_content
