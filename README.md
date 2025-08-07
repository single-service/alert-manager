# Сервис alert manager

## Описание

Сервис АПИ , который отправляет уведомления в телеграм бот.
Интегрируется с metabase вебхуками
Ссылка в DockerHub https://hub.docker.com/repository/docker/singleservice/alert-manager/general
Ссылка в github https://github.com/single-service/alert-manager

## Установка

Для локального тестирования. Понадобится tuna.am
tuna http 8005 --subdomain=alert-manager
https://alert-manager.ru.tuna.am

1. Поднимаем tuna
2. Добавляем envs
3. Запускаем docker compose
4. Настраиваем metabase, коннектим к нужной базе данных
5. Настраиваем в metabase канал с вебхуком
6. Настраиваем алерт
7. Для наполнения данными тестовой базы , есть скрипт в корне проекта

