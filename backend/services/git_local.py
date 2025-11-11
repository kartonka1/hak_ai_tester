from typing import Optional
from git import Repo
from pathlib import Path


class LocalGit:
	def __init__(self, repo_root: str = ".") -> None:
		self.root = Path(repo_root).resolve()
		if not (self.root / ".git").exists():
			self.repo = Repo.init(self.root)
		else:
			self.repo = Repo(self.root)

	def add_commit_push(self, message: str = "chore: generated files", remote_name: str = "origin", branch: str = "main") -> str:
		self.repo.git.add(all=True)
		if self.repo.is_dirty(index=True, working_tree=True, untracked_files=True):
			self.repo.index.commit(message)
		# Ensure branch exists
		if self.repo.active_branch.name != branch:
			try:
				self.repo.git.checkout(branch)
			except Exception:
				self.repo.git.checkout("-b", branch)
		try:
			self.repo.git.push(remote_name, branch, set_upstream=True)
		except Exception:
			# Maybe remote is not set; user should configure remote beforehand
			pass
		return self.repo.head.commit.hexsha


