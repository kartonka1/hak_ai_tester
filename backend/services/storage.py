import os
from pathlib import Path
from backend.services.config import get_settings


class LocalStorage:
	def __init__(self) -> None:
		self.settings = get_settings()
		self.root = Path(self.settings.default_repo_root).resolve()

	def save_file(self, relative_path: str, content: str) -> str:
		if relative_path.startswith("/") or relative_path.startswith("\\"):
			raise ValueError("relative_path must be relative")
		full_path = (self.root / relative_path).resolve()
		if self.root not in full_path.parents and self.root != full_path:
			raise ValueError("Path traversal detected")
		full_path.parent.mkdir(parents=True, exist_ok=True)
		full_path.write_text(content, encoding="utf-8", newline="\n")
		return str(full_path)


