import subprocess
import sys
import os
from typing import Literal


class TestRunner:
	def run(self, kind: Literal["ts", "js", "python"] = "ts", cwd: str | None = None) -> dict:
		if kind in ("ts", "js"):
			cmd = ["npx", "playwright", "test"]
			run_cwd = cwd or os.path.join("tests")
		else:
			cmd = [sys.executable, "-m", "pytest", "-q"]
			run_cwd = cwd or os.path.join("python_tests")
		try:
			proc = subprocess.run(cmd, cwd=run_cwd, capture_output=True, text=True, check=False)
			return {
				"returncode": proc.returncode,
				"stdout": proc.stdout,
				"stderr": proc.stderr,
			}
		except Exception as exc:
			return {"returncode": -1, "stdout": "", "stderr": str(exc)}


