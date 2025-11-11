import subprocess
import tempfile
import os
from typing import Optional


class CodeFormatter:
	"""Форматирование и линтинг кода автотестов"""
	
	@staticmethod
	def format_typescript(code: str) -> str:
		"""Форматирование TypeScript кода с помощью prettier"""
		try:
			with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
				f.write(code)
				temp_path = f.name
			
			try:
				# Попытка использовать prettier
				result = subprocess.run(
					['npx', '--yes', 'prettier', '--write', temp_path],
					capture_output=True,
					text=True,
					timeout=10
				)
				if result.returncode == 0:
					with open(temp_path, 'r', encoding='utf-8') as f:
						formatted = f.read()
					return formatted
			except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
				# Если prettier недоступен, возвращаем исходный код
				pass
			finally:
				if os.path.exists(temp_path):
					os.unlink(temp_path)
		except Exception:
			pass
		
		return code
	
	@staticmethod
	def format_javascript(code: str) -> str:
		"""Форматирование JavaScript кода с помощью prettier"""
		try:
			with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
				f.write(code)
				temp_path = f.name
			
			try:
				result = subprocess.run(
					['npx', '--yes', 'prettier', '--write', temp_path],
					capture_output=True,
					text=True,
					timeout=10
				)
				if result.returncode == 0:
					with open(temp_path, 'r', encoding='utf-8') as f:
						formatted = f.read()
					return formatted
			except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
				pass
			finally:
				if os.path.exists(temp_path):
					os.unlink(temp_path)
		except Exception:
			pass
		
		return code
	
	@staticmethod
	def format_python(code: str) -> str:
		"""Форматирование Python кода с помощью black"""
		try:
			with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
				f.write(code)
				temp_path = f.name
			
			try:
				# Попытка использовать black
				result = subprocess.run(
					['black', '--quiet', temp_path],
					capture_output=True,
					text=True,
					timeout=10
				)
				if result.returncode == 0:
					with open(temp_path, 'r', encoding='utf-8') as f:
						formatted = f.read()
					return formatted
			except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
				# Если black недоступен, пробуем ruff format
				try:
					result = subprocess.run(
						['ruff', 'format', temp_path],
						capture_output=True,
						text=True,
						timeout=10
					)
					if result.returncode == 0:
						with open(temp_path, 'r', encoding='utf-8') as f:
							formatted = f.read()
						return formatted
				except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
					pass
			finally:
				if os.path.exists(temp_path):
					os.unlink(temp_path)
		except Exception:
			pass
		
		return code
	
	@staticmethod
	def format_code(code: str, language: str) -> str:
		"""Форматирование кода в зависимости от языка"""
		lang = language.lower()
		if lang == "ts" or lang == "typescript":
			return CodeFormatter.format_typescript(code)
		elif lang == "js" or lang == "javascript":
			return CodeFormatter.format_javascript(code)
		elif lang == "python":
			return CodeFormatter.format_python(code)
		return code

