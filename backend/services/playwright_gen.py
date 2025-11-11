from backend.services.schemas import TestCase
from backend.services.ai import AIClient


HEADER_TS = "import { test, expect } from '@playwright/test';\n"
HEADER_JS = "const { test, expect } = require('@playwright/test');\n"


class PlaywrightGenerator:
	async def generate_code_from_test_case(
		self,
		test_case: TestCase,
		language: str,
		ai_client: AIClient,
		base_url: str | None = None,
	) -> str:
		code_body = await ai_client.generate_playwright_code(test_case, language=language, base_url=base_url)
		header = HEADER_TS if language == "ts" else HEADER_JS
		if code_body.startswith("import ") or code_body.startswith("const {"):
			return code_body
		return header + "\n" + code_body.strip() + "\n"


