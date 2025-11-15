from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.services.schemas import (
    GenerateTestCasesRequest,
    GenerateTestCasesResponse,
    GenerateTestCodeRequest,
    GenerateTestCodeResponse,
    ReviewTestRequest,
    ReviewTestResponse,
    SaveLocalRequest,
    SaveLocalResponse,
    SaveGithubRequest,
    SaveGithubResponse,
)
from backend.services.ai import AIClient
from backend.services.playwright_gen import PlaywrightGenerator
from backend.services.github import GithubSaver
from backend.services.storage import LocalStorage
from backend.services.config import get_settings
from backend.services.templates import get_template, list_templates
from backend.services.code_formatter import CodeFormatter
from fastapi import Body
from typing import Dict, Any
import os
from backend.services.git_local import LocalGit
from backend.services.test_runner import TestRunner


app = FastAPI(title="AI Test Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздача статических файлов frontend
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except Exception:
    pass  # Если папка не существует, пропускаем


@app.get("/")
def root():
    """Главная страница - возвращает frontend"""
    try:
        return FileResponse("frontend/index.html")
    except FileNotFoundError:
        return {
            "message": "AI Test Assistant API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
            "frontend": "Откройте frontend/index.html в браузере или установите frontend в папку frontend/"
        }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/templates")
def get_templates():
    """Получить список доступных шаблонов"""
    return {"templates": list_templates()}


@app.post("/generate/test-cases", response_model=GenerateTestCasesResponse)
async def generate_test_cases(payload: GenerateTestCasesRequest):
    try:
        print(f"[DEBUG] Получен запрос на генерацию тест-кейсов: provider={payload.ai_provider}, model={payload.ai_model}")
        ai = AIClient(provider=payload.ai_provider, model=payload.ai_model)
        print(f"[DEBUG] AIClient создан, начинаю генерацию...")
        cases, md = await ai.generate_test_cases(
            payload.description, payload.lang or "ru", want_markdown=(payload.format == "markdown")
        )
        print(f"[DEBUG] Генерация завершена, получено {len(cases)} тест-кейсов")
        return GenerateTestCasesResponse(test_cases=cases, markdown=md)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(exc)}")

@app.post("/git/push")
def git_push(body: Dict[str, Any] = Body(default={})):
    message = body.get("message") or "chore: generated files"
    remote = body.get("remote") or "origin"
    branch = body.get("branch") or "main"
    try:
        git = LocalGit(get_settings().default_repo_root)
        sha = git.add_commit_push(message=message, remote_name=remote, branch=branch)
        return {"commit": sha}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/tests/run")
def run_tests(body: Dict[str, Any] = Body(default={})):
    kind = (body.get("kind") or "ts").lower()
    cwd = body.get("cwd")
    try:
        result = TestRunner().run(kind=kind, cwd=cwd)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/generate/test-code", response_model=GenerateTestCodeResponse)
async def generate_test_code(payload: GenerateTestCodeRequest):
    try:
        # Использование шаблона, если указан
        test_case = payload.test_case
        if payload.template:
            template = get_template(payload.template)
            if template:
                template_params = payload.template_params or {}
                test_case = template.generate_test_case(template_params)
            else:
                raise HTTPException(status_code=400, detail=f"Шаблон '{payload.template}' не найден")
        
        ai = AIClient(provider=payload.ai_provider, model=payload.ai_model)
        language = (payload.language or "ts").lower()
        
        if language == "python":
            code = await ai.generate_playwright_python_code(test_case, base_url=payload.base_url)
            filename = "test_" + test_case.title.lower().replace(" ", "_") + ".py"
        else:
            generator = PlaywrightGenerator()
            code = await generator.generate_code_from_test_case(
                test_case=test_case,
                language=language,
                ai_client=ai,
                base_url=payload.base_url,
            )
            ext = "ts" if language == "ts" else "js"
            filename = "test_" + test_case.title.lower().replace(" ", "_") + f".spec.{ext}"
        
        # Форматирование кода
        code = CodeFormatter.format_code(code, language)
        
        # optionally save
        if payload.target_path:
            storage = LocalStorage()
            storage.save_file(payload.target_path, code)
        return GenerateTestCodeResponse(code=code, suggested_filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации кода: {str(exc)}")


@app.post("/review/test", response_model=ReviewTestResponse)
async def review_test(payload: ReviewTestRequest):
    try:
        ai = AIClient()
        result = await ai.review_test_code(payload.code)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(exc)}")


@app.post("/save/local", response_model=SaveLocalResponse)
async def save_local(payload: SaveLocalRequest):
    storage = LocalStorage()
    try:
        saved_path = storage.save_file(payload.relative_path, payload.content)
        return SaveLocalResponse(path=saved_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/generate/demo-app")
async def generate_demo_app(body: Dict[str, Any] = Body(...)):
    description: str = body.get("description") or ""
    out_dir: str = body.get("out_dir") or "demo_app"
    ai = AIClient()
    storage = LocalStorage()
    try:
        files = await ai.generate_demo_app(description)
        for name, content in files.items():
            storage.save_file(os.path.join(out_dir, name), content)
        return {"saved": [os.path.join(out_dir, k) for k in files.keys()]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/save/github", response_model=SaveGithubResponse)
async def save_github(payload: SaveGithubRequest):
    settings = get_settings()
    saver = GithubSaver(settings.github_token)
    try:
        res = await saver.create_or_update_file(
            owner=payload.owner,
            repo=payload.repo,
            path=payload.path,
            content=payload.content,
            message=payload.message or "chore: add/update autogenerated test",
            branch=payload.branch or "main",
        )
        return SaveGithubResponse(
            content_sha=res.get("content", {}).get("sha"),
            commit_sha=res.get("commit", {}).get("sha"),
            html_url=res.get("content", {}).get("html_url"),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


