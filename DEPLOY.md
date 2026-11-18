# Как запустить бота 24/7 без своего ПК

## Как бот работает сейчас (Bothost + Neon)

- **Хостинг:** Bothost (bothost.ru), тариф «Базовый» (99 ₽/мес; бесплатный тариф Bothost сейчас отключён).
  Бот `@tahta_rayon_bot`, регион Нидерланды.
- **Код:** открытый репозиторий https://github.com/salikme/rayony-bot (ветка `main`). Секретов в нём нет.
- **Сохранения игроков:** бесплатная база Postgres на neon.tech. Бот сам создаёт таблицу `saves`.
- **Секреты** заданы в Bothost, а не в коде:
  - токен бота — вкладка «Токен»;
  - `DATABASE_URL` (строка подключения к Neon) — вкладка «Переменные».

### Как обновить игру
1. Поменяйте `engine.py` / `bot.py` у себя.
2. Отправьте изменения на GitHub (в папке проекта):
   ```
   git add -A
   git commit -m "что поменял"
   git push
   ```
3. В Bothost: бот → вкладка «Репозиторий» → **«Сохранить и пересобрать»** (2–5 минут).
Прогресс игроков в базе при этом не пропадает.

### Важно
- Не запускайте бота одновременно у себя на ПК — Telegram выдаст ошибку `Conflict`.
- Файлы `token.txt` и `database_url.txt` в репозиторий не попадают (они в `.gitignore`) — не выкладывайте их.
- Локально (без `database_url.txt` и `DATABASE_URL`) бот хранит сохранения в папке `saves/`.

---

## Вариант А — свой VPS (надёжно, ~150–300 ₽/мес)

Подойдёт любой самый дешёвый Linux-сервер (Ubuntu 22/24, 1 ядро, 512 МБ–1 ГБ RAM):
Timeweb Cloud, Aeza, Beget, Selectel, Hetzner и т.п. Сохранения игроков лежат прямо на диске сервера — ничего не теряется.

### 1. Залить файлы на сервер
На своём ПК, в папке проекта (PowerShell):
```
ssh root@IP_СЕРВЕРА "mkdir -p /opt/rayony"
scp bot.py engine.py requirements.txt token.txt rayony-bot.service root@IP_СЕРВЕРА:/opt/rayony/
```
(Если хотите перенести текущие сохранения игроков — `scp -r saves root@IP_СЕРВЕРА:/opt/rayony/`.)

### 2. Установить и запустить (на сервере)
```
ssh root@IP_СЕРВЕРА
apt update && apt install -y python3 python3-venv
cd /opt/rayony
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp rayony-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now rayony-bot
```
Всё. Бот работает круглосуточно и сам перезапускается после падения или перезагрузки сервера.

### Полезные команды
- `systemctl status rayony-bot` — работает ли
- `journalctl -u rayony-bot -f` — логи в реальном времени
- `systemctl restart rayony-bot` — перезапуск после обновления `bot.py`/`engine.py` (сначала залить их заново через `scp`)

**Важно:** не запускайте бота одновременно на ПК и на сервере — Telegram выдаст ошибку `Conflict`.

---

## Вариант Б — облачная платформа с Docker (без настройки сервера)

В проекте есть `Dockerfile`. Подойдёт любой хостинг, который умеет запускать Docker-контейнер
как фоновый процесс (worker) и даёт постоянный диск: Railway, Fly.io, Amvera, Timeweb Apps и др.

1. Загрузите проект на GitHub (**без** `token.txt` и `gemini.txt` — они не должны попасть в интернет).
2. Создайте на платформе новый сервис из этого репозитория — она соберёт `Dockerfile` сама.
3. Добавьте переменную окружения `BOT_TOKEN` = ваш токен от BotFather.
4. Подключите постоянный диск (Volume) к пути `/data` — иначе при каждом перезапуске
   прогресс игроков будет теряться.
5. Бот не открывает HTTP-порт, поэтому тип сервиса — **Worker / Background**, а не Web.

Бесплатные «веб-сервисы», которые засыпают без трафика (Render Free и подобные), для этого бота не подходят.
