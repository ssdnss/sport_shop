# Атлетика — интернет-магазин спортивных товаров

1. Откройте папку проекта в VS Code

bash
cd /путь/до/папки/с/проектом

2. Создайте виртуальное окружение
bash
python -m venv venv

3. Активируйте виртуальное окружение
Windows (Git Bash / VS Code Bash):

bash
source venv/Scripts/activate
macOS / Linux:

bash
source venv/bin/activate
После активации в начале строки терминала появится (venv)

4. Установите зависимости
bash
pip install -r requirements.txt

5. Примените миграции базы данных
bash
python manage.py makemigrations
python manage.py migrate

6. Создайте суперпользователя (администратора)
bash
python manage.py createsuperuser
Введите:

Имя пользователя (например: admin)

Email (например: admin@example.com)

Пароль (не менее 8 символов)

7. Запустите сервер разработки
bash
python manage.py runserver

8. Откройте сайт в браузере
Пользовательская часть: http://127.0.0.1:8000/

Административная панель: http://127.0.0.1:8000/admin/

Учётные записи для тестирования
Роль	Логин	Пароль
Администратор	admin	(тот, что задали при createsuperuser)
Обычный пользователь	(зарегистрируйтесь через форму)	—
