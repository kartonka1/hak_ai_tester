import base64
from typing import Any, Dict
import httpx
from backend.services.config import get_settings


class GithubSaver:
	def __init__(self, token: str | None) -> None:
		if not token:
			raise RuntimeError("GITHUB_TOKEN is not configured")
		self.token = token
		self.api_base = "https://api.github.com"

	def _headers(self) -> dict:
		return {
			"Authorization": f"Bearer {self.token}",
			"Accept": "application/vnd.github+json",
		}

	async def get_file_sha(self, owner: str, repo: str, path: str, branch: str) -> str | None:
		url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
		async with httpx.AsyncClient(timeout=30.0) as client:
			resp = await client.get(url, headers=self._headers())
			if resp.status_code == 404:
				return None
			resp.raise_for_status()
			data = resp.json()
			return data.get("sha")

	async def create_or_update_file(
		self,
		owner: str,
		repo: str,
		path: str,
		content: str,
		message: str,
		branch: str = "main",
	) -> Dict[str, Any]:
		url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
		sha = await self.get_file_sha(owner, repo, path, branch)
		body = {
			"message": message,
			"content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
			"branch": branch,
		}
		if sha:
			body["sha"] = sha
		async with httpx.AsyncClient(timeout=30.0) as client:
			resp = await client.put(url, headers=self._headers(), json=body)
			resp.raise_for_status()
			return resp.json()


