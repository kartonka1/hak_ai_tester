from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class GenerateTestCasesRequest(BaseModel):
	description: str = Field(..., description="Текстовое описание фичи/сценария")
	lang: Optional[str] = Field(default="ru", description="Язык результата (ru/en)")
	format: Optional[Literal["json", "markdown"]] = Field(default="json", description="Формат результата")


class TestCase(BaseModel):
	title: str
	steps: List[str]
	expected: str


class GenerateTestCasesResponse(BaseModel):
	test_cases: List[TestCase]
	markdown: Optional[str] = None


class GenerateTestCodeRequest(BaseModel):
	test_case: TestCase
	language: Optional[str] = Field(default="ts", description="ts, js или python")
	base_url: Optional[str] = Field(default=None, description="Базовый URL приложения")
	target_path: Optional[str] = Field(default=None, description="Куда сохранить файл (опц.)")


class GenerateTestCodeResponse(BaseModel):
	code: str
	suggested_filename: Optional[str] = None


class ReviewTestRequest(BaseModel):
	code: str


class ReviewSuggestion(BaseModel):
	title: str
	comment: str
	diff: Optional[str] = None


class ReviewTestResponse(BaseModel):
	summary: str
	score: int = Field(ge=0, le=100)
	suggestions: List[ReviewSuggestion]


class SaveLocalRequest(BaseModel):
	relative_path: str = Field(..., description="Путь относительно DEFAULT_REPO_ROOT")
	content: str


class SaveLocalResponse(BaseModel):
	path: str


class SaveGithubRequest(BaseModel):
	owner: str
	repo: str
	path: str
	content: str
	message: Optional[str] = None
	branch: Optional[str] = None


class SaveGithubResponse(BaseModel):
	content_sha: Optional[str] = None
	commit_sha: Optional[str] = None
	html_url: Optional[str] = None


