import argparse
import json
from backend.services.ai import AIClient
from backend.services.storage import LocalStorage
from backend.services.git_local import LocalGit
from backend.services.test_runner import TestRunner
from backend.services.schemas import TestCase


def main():
	parser = argparse.ArgumentParser(description="AI Test Assistant CLI")
	parser.add_argument("--requirements", type=str, required=True, help="Текстовые требования")
	parser.add_argument("--out", type=str, default="generated", help="Корневая папка для файлов")
	parser.add_argument("--lang", type=str, default="ru", help="Язык тест-кейсов (ru/en)")
	parser.add_argument("--format", type=str, default="json", choices=["json", "markdown"], help="Формат тест-кейсов")
	parser.add_argument("--target", type=str, default="python", choices=["python", "ts", "js"], help="Цель генерации автотеста")
	parser.add_argument("--push", action="store_true", help="Сделать git commit и push")
	parser.add_argument("--ai-provider", type=str, choices=["openai", "ollama"], help="Провайдер ИИ. По умолчанию берется из окружения.")
	parser.add_argument("--ai-model", type=str, help="Модель ИИ. По умолчанию берется из окружения.")
	args = parser.parse_args()

	ai = AIClient(provider=args.ai_provider, model=args.ai_model)
	storage = LocalStorage()

	# 1) Test cases
	cases, md = asyncio_run(ai.generate_test_cases(args.requirements, args.lang, want_markdown=(args.format == "markdown")))
	if args.format == "markdown" and md:
		storage.save_file(f"{args.out}/test_cases.md", md)
	else:
		data = {"test_cases": [c.model_dump() for c in cases]}
		storage.save_file(f"{args.out}/test_cases.json", json.dumps(data, ensure_ascii=False, indent=2))

	# choose first case for demo
	tc = cases[0] if cases else TestCase(title="Автотест", steps=["Открыть /"], expected="Страница загружается")

	# 2) Test code
	if args.target == "python":
		code = asyncio_run(ai.generate_playwright_python_code(tc, base_url=None))
		path = f"{args.out}/python_tests/test_{tc.title.lower().replace(' ', '_')}.py"
	elif args.target == "ts":
		from backend.services.playwright_gen import PlaywrightGenerator
		code = asyncio_run(PlaywrightGenerator().generate_code_from_test_case(tc, "ts", ai, None))
		path = f"{args.out}/tests/e2e/test_{tc.title.lower().replace(' ', '_')}.spec.ts"
	else:
		from backend.services.playwright_gen import PlaywrightGenerator
		code = asyncio_run(PlaywrightGenerator().generate_code_from_test_case(tc, "js", ai, None))
		path = f"{args.out}/tests/e2e/test_{tc.title.lower().replace(' ', '_')}.spec.js"
	storage.save_file(path, code)

	# 3) Demo app
	files = asyncio_run(ai.generate_demo_app(args.requirements))
	for name, content in files.items():
		storage.save_file(f"{args.out}/demo_app/{name}", content)

	# 4) Optional git push
	if args.push:
		sha = LocalGit(args.out).add_commit_push(message="feat: generated tests and demo", branch="main")
		print("Pushed commit:", sha)

	print("Done. Files saved under:", args.out)


def asyncio_run(coro):
	try:
		import asyncio
		return asyncio.run(coro)
	except RuntimeError:
		# If already in loop, create new loop
		loop = asyncio.new_event_loop()
		try:
			return loop.run_until_complete(coro)
		finally:
			loop.close()


if __name__ == "__main__":
	main()


