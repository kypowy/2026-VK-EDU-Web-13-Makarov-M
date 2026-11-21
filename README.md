# 2026-VK-EDU-Web-13-Makarov-M

# ДЗ_3
## Локальный запуск

## Запуск через Docker Compose

0. в каталоге \web-qna переименуйте .env.example в .env, либо же создайте свой .env по примеру
1. Выполните команду:
   docker compose up --build
2. Заполните БД командой docker compose exec web python manage.py fill_db [ratio] //вместо ratio подставьте значение
3. Приведите БД к согласованному состоянию командой docker compose exec web python manage.py recalc_ratings 
4. Откройте в браузере: http://127.0.0.1:8000
