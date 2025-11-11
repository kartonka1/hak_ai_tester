import base64
import json
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.services.config import get_settings
from backend.services.schemas import TestCase, ReviewTestResponse, ReviewSuggestion


class AIClient:
	def __init__(self) -> None:
		self.settings = get_settings()
		self.provider = (self.settings.ai_provider or "openai").lower()
		self.base_url = self.settings.openai_base_url or "https://api.openai.com/v1"
		self.api_key = self.settings.openai_api_key
		self.model = self.settings.openai_model

	def _headers(self) -> dict:
		if self.provider == "openai":
			if not self.api_key:
				raise RuntimeError("OPENAI_API_KEY is not configured")
			return {
				"Authorization": f"Bearer {self.api_key}",
				"Content-Type": "application/json",
			}
		# Ollama does not require auth
		return {"Content-Type": "application/json"}

	@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
	async def _chat(self, messages: List[dict], response_format: str | None = None) -> str:
		if self.provider == "openai":
			payload: dict = {
				"model": self.model,
				"messages": messages,
				"temperature": 0.2,
			}
			if response_format == "json":
				payload["response_format"] = {"type": "json_object"}
			async with httpx.AsyncClient(timeout=60.0) as client:
				resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=payload)
				resp.raise_for_status()
				data = resp.json()
				return data["choices"][0]["message"]["content"]
		# Ollama chat
		model = self.settings.ollama_model
		base = self.settings.ollama_base_url.rstrip("/")
		ollama_payload = {
			"model": model,
			"messages": messages,
			"options": {
				"temperature": 0.2,
			},
			"stream": False,
		}
		async with httpx.AsyncClient(timeout=120.0) as client:
			resp = await client.post(f"{base}/api/chat", headers=self._headers(), json=ollama_payload)
			resp.raise_for_status()
			data = resp.json()
			# Ollama returns {"message":{"role":"assistant","content":"..."}}
			if "message" in data and "content" in data["message"]:
				return data["message"]["content"]
			# Fallback if choices-like
			if "choices" in data:
				return data["choices"][0]["message"]["content"]
			return str(data)

	async def generate_test_cases(self, description: str, lang: str = "ru", want_markdown: bool = False) -> tuple[list[TestCase], str | None]:
		system = (
			"Ты — помощник тестировщика. На основе описания фичи сгенерируй 1-3 тест-кейса. "
			"Формат JSON: {\"test_cases\":[{\"title\":\"...\",\"steps\":[\"...\"],\"expected\":\"...\"}]}. "
			"Язык: " + lang
		)
		user = f"Описание фичи:\n{description}"
		content = await self._chat(
			[
				{"role": "system", "content": system},
				{"role": "user", "content": user},
			],
			response_format="json",
		)
		data = json.loads(content)
		items = data.get("test_cases", [])
		result: List[TestCase] = []
		for item in items:
			title = item.get("title") or "Тест"
			steps = [s for s in item.get("steps", []) if isinstance(s, str)]
			expected = item.get("expected") or ""
			result.append(TestCase(title=title, steps=steps, expected=expected))
		md: str | None = None
		if want_markdown:
			md_parts = []
			for c in result:
				md_parts.append(f"### {c.title}\n\n- Шаги:\n" + "\n".join([f"  - {s}" for s in c.steps]) + f"\n\n- Ожидаемо: {c.expected}\n")
			md = "\n".join(md_parts)
		return result, md

	async def generate_playwright_code(self, test_case: TestCase, language: str = "ts", base_url: str | None = None) -> str:
		lang_name = "TypeScript" if language == "ts" else "JavaScript"
		system = (
			f"Сгенерируй {lang_name} тест на Playwright для браузера. "
			"Используй @playwright/test. Импортируй { test, expect }. "
			"Добавь стабильные локаторы, ожидания и проверку ожидаемого результата. "
			"Если указан base_url, используй относительные пути."
		)
		user = json.dumps(
			{
				"test_case": test_case.model_dump(),
				"language": language,
				"base_url": base_url,
			},
			ensure_ascii=False,
			indent=2,
		)
		code = await self._chat(
			[
				{"role": "system", "content": system},
				{"role": "user", "content": user},
			]
		)
		return code.strip()

	async def generate_playwright_python_code(self, test_case: TestCase, base_url: str | None = None) -> str:
		system = (
			"Сгенерируй Python тест на Playwright (pytest + playwright). "
			"Импортируй pytest и используй фикстуру page. "
			"Добавь стабильные локаторы, ожидания и проверку ожидаемого результата. "
			"Если указан base_url, используй относительные пути."
		)
		user = json.dumps(
			{
				"test_case": test_case.model_dump(),
				"language": "python",
				"base_url": base_url,
			},
			ensure_ascii=False,
			indent=2,
		)
		code = await self._chat(
			[
				{"role": "system", "content": system},
				{"role": "user", "content": user},
			]
		)
		return code.strip()

	async def generate_demo_app(self, description: str) -> dict:
		system = (
			"Создай минимальное веб-приложение (index.html, script.js, styles.css) для демонстрации сценария. "
			"index.html должен подключать script.js и styles.css. Код должен быть самодостаточный и простой."
		)
		user = description
		content = await self._chat(
			[
				{"role": "system", "content": system},
				{"role": "user", "content": user},
			],
			response_format=None,
		)
		# Простой эвристический парсинг: разделы ---index.html---, ---script.js---, ---styles.css---
		files = {"index.html": "", "script.js": "", "styles.css": ""}
		current = None
		for line in content.splitlines():
			h = line.strip().lower()
			if "index.html" in h:
				current = "index.html"; continue
			if "script.js" in h:
				current = "script.js"; continue
			if "styles.css" in h:
				current = "styles.css"; continue
			if current:
				files[current] += line + "\n"
		return files

	async def review_test_code(self, code: str) -> ReviewTestResponse:
		system = (
			"Ты — код-ревьюер тестов на Playwright. Проанализируй код: найди проблемы стабильности, "
			"повторы, плохие локаторы, отсутствующие ожидания. Верни JSON: "
			"{\"summary\":\"...\",\"score\":0-100,\"suggestions\":[{\"title\":\"...\",\"comment\":\"...\",\"diff\":\"...\"}]}."
		)
		user = code
		content = await self._chat(
			[
				{"role": "system", "content": system},
				{"role": "user", "content": user},
			],
			response_format="json",
		)
		data = json.loads(content)
		suggestions = [
			ReviewSuggestion(
				title=item.get("title") or "Предложение",
				comment=item.get("comment") or "",
				diff=item.get("diff"),
			)
			for item in data.get("suggestions", [])
		]
		score = data.get("score", 70)
		summary = data.get("summary", "")
		return ReviewTestResponse(summary=summary, score=score, suggestions=suggestions)


