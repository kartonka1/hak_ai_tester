from typing import Dict, Any, Optional
from backend.services.schemas import TestCase


class TestTemplate:
	"""Базовый класс для шаблонов тестов"""
	name: str
	description: str
	category: str
	
	def generate_test_case(self, params: Dict[str, Any]) -> TestCase:
		"""Генерирует тест-кейс на основе параметров"""
		raise NotImplementedError


class AuthTemplate(TestTemplate):
	"""Шаблон для тестирования авторизации"""
	name = "auth"
	description = "Тестирование авторизации: логин, логаут, валидация"
	category = "security"
	
	def generate_test_case(self, params: Dict[str, Any]) -> TestCase:
		login_url = params.get("login_url", "/login")
		email = params.get("email", "user@example.com")
		password = params.get("password", "Passw0rd!")
		success_url = params.get("success_url", "/dashboard")
		
		# Позитивный кейс
		if params.get("type") == "positive":
			return TestCase(
				title="Успешная авторизация с валидными данными",
				steps=[
					f"Открыть страницу {login_url}",
					f"Ввести email: {email}",
					f"Ввести пароль: {password}",
					"Нажать кнопку 'Войти' или 'Login'"
				],
				expected=f"Редирект на {success_url}, отображается приветственное сообщение или имя пользователя"
			)
		# Негативный кейс - неверный пароль
		elif params.get("type") == "negative_password":
			return TestCase(
				title="Попытка входа с неверным паролем",
				steps=[
					f"Открыть страницу {login_url}",
					f"Ввести email: {email}",
					"Ввести пароль: wrongpassword",
					"Нажать кнопку 'Войти'"
				],
				expected="Отображается ошибка 'Неверные учетные данные' или 'Invalid credentials', пользователь остается на странице логина"
			)
		# Негативный кейс - валидация
		elif params.get("type") == "negative_validation":
			return TestCase(
				title="Попытка входа с пустыми полями",
				steps=[
					f"Открыть страницу {login_url}",
					"Оставить поля email и пароль пустыми",
					"Нажать кнопку 'Войти'"
				],
				expected="Отображаются сообщения валидации: 'Email обязателен' и 'Пароль обязателен'"
			)
		# Негативный кейс - неверный email
		else:
			return TestCase(
				title="Попытка входа с неверным форматом email",
				steps=[
					f"Открыть страницу {login_url}",
					"Ввести email: invalid-email",
					f"Ввести пароль: {password}",
					"Нажать кнопку 'Войти'"
				],
				expected="Отображается ошибка валидации 'Неверный формат email' или 'Invalid email format'"
			)


class FormTemplate(TestTemplate):
	"""Шаблон для тестирования форм"""
	name = "form"
	description = "Тестирование форм: заполнение, валидация, отправка"
	category = "forms"
	
	def generate_test_case(self, params: Dict[str, Any]) -> TestCase:
		form_url = params.get("form_url", "/form")
		fields = params.get("fields", [])
		submit_button = params.get("submit_button", "Отправить")
		
		if params.get("type") == "positive":
			steps = [f"Открыть страницу {form_url}"]
			for field in fields:
				field_name = field.get("name", "поле")
				field_value = field.get("value", "тестовое значение")
				steps.append(f"Заполнить поле '{field_name}': {field_value}")
			steps.append(f"Нажать кнопку '{submit_button}'")
			
			return TestCase(
				title="Успешная отправка формы",
				steps=steps,
				expected="Форма успешно отправлена, отображается сообщение об успехе или редирект"
			)
		else:  # negative validation
			steps = [f"Открыть страницу {form_url}"]
			# Оставляем обязательные поля пустыми
			required_fields = [f for f in fields if f.get("required", False)]
			if required_fields:
				steps.append(f"Оставить поле '{required_fields[0]['name']}' пустым")
			steps.append(f"Нажать кнопку '{submit_button}'")
			
			return TestCase(
				title="Валидация обязательных полей формы",
				steps=steps,
				expected=f"Отображается сообщение валидации для обязательного поля '{required_fields[0]['name'] if required_fields else 'поле'}'"
			)


class ListTemplate(TestTemplate):
	"""Шаблон для тестирования списков и таблиц"""
	name = "list"
	description = "Тестирование списков: отображение, фильтрация, сортировка, пагинация"
	category = "data"
	
	def generate_test_case(self, params: Dict[str, Any]) -> TestCase:
		list_url = params.get("list_url", "/list")
		item_count = params.get("item_count", 10)
		
		if params.get("type") == "display":
			return TestCase(
				title="Отображение списка элементов",
				steps=[
					f"Открыть страницу {list_url}",
					"Дождаться загрузки списка"
				],
				expected=f"Отображается список из {item_count} элементов, каждый элемент содержит необходимые данные"
			)
		elif params.get("type") == "filter":
			filter_value = params.get("filter_value", "test")
			return TestCase(
				title="Фильтрация списка",
				steps=[
					f"Открыть страницу {list_url}",
					f"Ввести в поле фильтра: {filter_value}",
					"Нажать кнопку 'Фильтровать' или дождаться автоматической фильтрации"
				],
				expected=f"Список отфильтрован, отображаются только элементы, соответствующие '{filter_value}'"
			)
		elif params.get("type") == "pagination":
			return TestCase(
				title="Пагинация списка",
				steps=[
					f"Открыть страницу {list_url}",
					"Прокрутить список до конца",
					"Нажать кнопку 'Следующая страница' или 'Next'"
				],
				expected="Загружается следующая страница списка, отображаются новые элементы"
			)
		else:  # sort
			return TestCase(
				title="Сортировка списка",
				steps=[
					f"Открыть страницу {list_url}",
					"Нажать на заголовок колонки для сортировки"
				],
				expected="Список отсортирован по выбранной колонке, элементы расположены в правильном порядке"
			)


class CRUDTemplate(TestTemplate):
	"""Шаблон для тестирования CRUD операций"""
	name = "crud"
	description = "Тестирование CRUD: создание, чтение, обновление, удаление"
	category = "data"
	
	def generate_test_case(self, params: Dict[str, Any]) -> TestCase:
		entity_name = params.get("entity_name", "элемент")
		base_url = params.get("base_url", "/items")
		
		op_type = params.get("type", "create")
		
		if op_type == "create":
			return TestCase(
				title=f"Создание нового {entity_name}",
				steps=[
					f"Открыть страницу {base_url}",
					"Нажать кнопку 'Создать' или 'Add'",
					"Заполнить форму создания",
					"Нажать кнопку 'Сохранить'"
				],
				expected=f"Новый {entity_name} успешно создан, отображается в списке"
			)
		elif op_type == "read":
			return TestCase(
				title=f"Просмотр деталей {entity_name}",
				steps=[
					f"Открыть страницу {base_url}",
					"Нажать на первый элемент в списке"
				],
				expected=f"Открывается страница с деталями {entity_name}, отображается вся необходимая информация"
			)
		elif op_type == "update":
			return TestCase(
				title=f"Обновление {entity_name}",
				steps=[
					f"Открыть страницу {base_url}",
					"Нажать на элемент в списке",
					"Нажать кнопку 'Редактировать' или 'Edit'",
					"Изменить данные",
					"Нажать кнопку 'Сохранить'"
				],
				expected=f"{entity_name} успешно обновлен, изменения отображаются в списке"
			)
		else:  # delete
			return TestCase(
				title=f"Удаление {entity_name}",
				steps=[
					f"Открыть страницу {base_url}",
					"Нажать кнопку 'Удалить' на элементе",
					"Подтвердить удаление в диалоге"
				],
				expected=f"{entity_name} успешно удален, больше не отображается в списке"
			)


# Реестр шаблонов
TEMPLATES: Dict[str, TestTemplate] = {
	"auth": AuthTemplate(),
	"form": FormTemplate(),
	"list": ListTemplate(),
	"crud": CRUDTemplate(),
}


def get_template(name: str) -> Optional[TestTemplate]:
	"""Получить шаблон по имени"""
	return TEMPLATES.get(name)


def list_templates() -> list[Dict[str, str]]:
	"""Получить список всех доступных шаблонов"""
	return [
		{
			"name": t.name,
			"description": t.description,
			"category": t.category
		}
		for t in TEMPLATES.values()
	]

