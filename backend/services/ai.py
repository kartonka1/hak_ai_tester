import base64
import json
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.services.config import get_settings
from backend.services.schemas import TestCase, ReviewTestResponse, ReviewSuggestion


class AIClient:
	def __init__(self, provider: str | None = None, model: str | None = None) -> None:
		self.settings = get_settings()
		self.provider = (provider or self.settings.ai_provider or "openai").lower()
		if self.provider not in {"openai", "ollama"}:
			raise ValueError(f"Unsupported AI provider '{self.provider}'. Используйте 'openai' или 'ollama'.")
		self.base_url = self.settings.openai_base_url or "https://api.openai.com/v1"
		# Ollama не требует ключа, но нуждается в корректном базовом URL
		self.ollama_base_url = (self.settings.ollama_base_url or "http://localhost:11434").rstrip("/")
		self.api_key = self.settings.openai_api_key
		# Переопределение модели в зависимости от провайдера
		if model:
			self.model = model
		elif self.provider == "ollama":
			self.model = self.settings.ollama_model
		else:
			self.model = self.settings.openai_model

	def _headers(self) -> dict:
		if self.provider == "openai":
			if not self.api_key:
				raise ValueError("OPENAI_API_KEY is not configured. Установите переменную окружения или выберите Ollama.")
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
		model = self.model or self.settings.ollama_model
		base = self.ollama_base_url
		ollama_payload = {
			"model": model,
			"messages": messages,
			"options": {
				"temperature": 0.2,
			},
			"stream": False,
		}
		if response_format == "json":
			ollama_payload["format"] = "json"
		print(f"[DEBUG] Отправка запроса к Ollama: {base}/api/chat, model={model}")
		async with httpx.AsyncClient(timeout=120.0) as client:
			resp = await client.post(f"{base}/api/chat", headers=self._headers(), json=ollama_payload)
			print(f"[DEBUG] Ответ от Ollama получен, статус: {resp.status_code}")
			resp.raise_for_status()
			data = resp.json()
			print(f"[DEBUG] Данные от Ollama распарсены")
			# Ollama returns {"message":{"role":"assistant","content":"..."}}
			if "message" in data and "content" in data["message"]:
				return data["message"]["content"]
			# Fallback if choices-like
			if "choices" in data:
				return data["choices"][0]["message"]["content"]
			return str(data)

	async def generate_test_cases(self, description: str, lang: str = "ru", want_markdown: bool = False) -> tuple[list[TestCase], str | None]:
		examples = {
			"ru": {
				"positive": {
					"title": "Успешная авторизация с валидными данными",
					"steps": ["Открыть страницу /login", "Ввести email: user@example.com", "Ввести пароль: Passw0rd!", "Нажать кнопку 'Войти'"],
					"expected": "Редирект на /dashboard, отображается приветственное сообщение"
				},
				"negative": {
					"title": "Попытка входа с неверным паролем",
					"steps": ["Открыть страницу /login", "Ввести email: user@example.com", "Ввести пароль: wrongpass", "Нажать кнопку 'Войти'"],
					"expected": "Отображается ошибка 'Неверные учетные данные', пользователь остается на странице логина"
				}
			},
			"en": {
				"positive": {
					"title": "Successful login with valid credentials",
					"steps": ["Open /login page", "Enter email: user@example.com", "Enter password: Passw0rd!", "Click 'Login' button"],
					"expected": "Redirect to /dashboard, welcome message is displayed"
				},
				"negative": {
					"title": "Login attempt with invalid password",
					"steps": ["Open /login page", "Enter email: user@example.com", "Enter password: wrongpass", "Click 'Login' button"],
					"expected": "Error message 'Invalid credentials' is displayed, user remains on login page"
				}
			}
		}
		
		ex = examples.get(lang, examples["ru"])
		system = (
			f"Ты — эксперт по тестированию безопасности. На основе описания фичи сгенерируй 1-5 тест-кейсов, включая позитивные и негативные сценарии. "
			f"Формат JSON: {{\"test_cases\":[{{\"title\":\"...\",\"steps\":[\"...\"],\"expected\":\"...\"}}]}}. "
			f"Язык: {lang}. "
			f"Примеры:\n"
			f"Позитивный: {json.dumps(ex['positive'], ensure_ascii=False)}\n"
			f"Негативный: {json.dumps(ex['negative'], ensure_ascii=False)}\n"
			f"Важно: шаги должны быть конкретными и проверяемыми, ожидаемый результат — четким."
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
		
		# Few-shot примеры для стабильных локаторов
		example_ts = """import { test, expect } from '@playwright/test';

test('Успешная авторизация', async ({ page }) => {
  // Используй стабильные локаторы: data-testid, role, или getByText/getByLabel
  await page.goto('/login');
  
  // Предпочтительно: data-testid или role-based локаторы
  await page.getByTestId('email-input').fill('user@example.com');
  await page.getByTestId('password-input').fill('Passw0rd!');
  await page.getByRole('button', { name: 'Войти' }).click();
  
  // Всегда добавляй ожидания перед проверками
  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.getByText('Добро пожаловать')).toBeVisible();
});"""
		
		example_js = """const { test, expect } = require('@playwright/test');

test('Успешная авторизация', async ({ page }) => {
  await page.goto('/login');
  await page.getByTestId('email-input').fill('user@example.com');
  await page.getByTestId('password-input').fill('Passw0rd!');
  await page.getByRole('button', { name: 'Войти' }).click();
  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.getByText('Добро пожаловать')).toBeVisible();
});"""
		
		example_code = example_ts if language == "ts" else example_js
		
		system = (
			f"Сгенерируй {lang_name} тест на Playwright для браузера. "
			f"Используй @playwright/test. Импортируй {{ test, expect }}. "
			f"КРИТИЧЕСКИ ВАЖНО:\n"
			f"1. Используй стабильные локаторы: getByTestId, getByRole, getByLabel, getByText (избегай CSS/XPath селекторов)\n"
			f"2. Всегда добавляй ожидания (await expect) перед проверками элементов\n"
			f"3. Используй waitFor для динамических элементов\n"
			f"4. Для навигации используй page.goto() с base_url если указан\n"
			f"5. Проверяй негативные сценарии (ошибки, валидация)\n"
			f"Пример хорошего теста:\n{example_code}\n"
			f"Если указан base_url, используй его в page.goto()."
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
		example_py = """import pytest
from playwright.sync_api import Page, expect

def test_successful_login(page: Page):
    # Используй стабильные локаторы: data-testid, role, или get_by_text/get_by_label
    page.goto('/login')
    
    # Предпочтительно: data-testid или role-based локаторы
    page.get_by_test_id('email-input').fill('user@example.com')
    page.get_by_test_id('password-input').fill('Passw0rd!')
    page.get_by_role('button', name='Войти').click()
    
    # Всегда добавляй ожидания перед проверками
    expect(page).to_have_url(r'.*dashboard')
    expect(page.get_by_text('Добро пожаловать')).to_be_visible()"""
		
		system = (
			"Сгенерируй Python тест на Playwright (pytest + playwright). "
			"Импортируй pytest и используй фикстуру page. "
			"КРИТИЧЕСКИ ВАЖНО:\n"
			"1. Используй стабильные локаторы: get_by_test_id, get_by_role, get_by_label, get_by_text (избегай CSS/XPath селекторов)\n"
			"2. Всегда добавляй ожидания (expect) перед проверками элементов\n"
			"3. Используй wait_for для динамических элементов\n"
			"4. Для навигации используй page.goto() с base_url если указан\n"
			"5. Проверяй негативные сценарии (ошибки, валидация)\n"
			f"Пример хорошего теста:\n{example_py}\n"
			"Если указан base_url, используй его в page.goto()."
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


