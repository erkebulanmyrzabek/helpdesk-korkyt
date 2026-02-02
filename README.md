# 🎓 Helpdesk System | Korkyt Ata University

![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)

Современная система обработки заявок (Helpdesk) для университета Коркыт Ата. Позволяет преподавателям подавать заявки на техническое обслуживание, а специалистам поддержки — оперативно их решать.

---

## ✨ Основные возможности

### 👨‍🏫 Для Преподавателей (Teacher)
- **Создание заявок:** Удобная форма с выбором корпуса и кабинета.
- **Медиа-вложения:** 
  - 📸 Прикрепление фото (Drag & Drop, Ctrl+V из буфера).
  - 🎥 Прикрепление видео.
- **Статус:** Отслеживание статуса заявки (Открыта, В работе, Выполнена).
- **История:** Просмотр отчетов о выполнении с фотоотчетами от техподдержки.

### 🛠 Для Техподдержки (Helpdesk)
- **Дэшборд:**
  - 📥 **Свободные заявки:** Общий пул новых заявок.
  - ⚡ **В работе:** Личные задачи специалиста.
  - ✅ **История:** Архив выполненных задач.
- **Взятие в работу:** Назначение заявки на себя в один клик.
- **Отчетность:** Завершение заявки с обязательным комментарием и фотоотчетом.

### 👨‍💼 Для Администратора (Admin)
- **Расширенная статистика:**
  - Общая сводка и распределение заявок по статусам.
  - Статистика по категориям (компьютеры, интернет и т.д.).
  - Производительность хелпдесков (количество выполненных заявок).
  - Активность учителей (созданные и выполненные заявки).
  - Среднее время выполнения заявок.
- **Все заявки:** Полный список всех тикетов в системе с временем выполнения.
- **Управление пользователями:** 
  - Создание аккаунтов (Teacher, Helpdesk, Admin).
  - Удаление пользователей.

---

## 📱 Интерфейс и UX

Проект полностью адаптирован под мобильные устройства:
- **Responsive Design:** Удобно использовать как на ПК, так и на смартфоне.
- **Мобильное меню:** Адаптивная навигация.
- **Улучшенный UX:** Крупные кнопки, интуитивные иконки (Bootstrap Icons).

---

## 🚀 Запуск проекта

### Предварительные требования
- Python 3.10+
- Node.js 16+

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd helpdesk
```

### 2. Бэкенд (Django)

```bash
cd backend

# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# Установка зависимостей
pip install -r ../requirements.txt

# Миграции БД
python3 manage.py migrate

# Создание тестовых пользователей (опционально)
python3 create_users.py

# Запуск сервера
python3 manage.py runserver
```

### 3. Фронтенд (Vue 3)

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск сервера разработки
npm run dev
```

Приложение будет доступно по адресу: `http://localhost:5173`

---

## 🔑 Тестовые аккаунты

| Роль | Логин | Пароль |
| :--- | :--- | :--- |
| **Учитель** | `teacher` | `teacher` |
| **Хелпдеск** | `helpdesk` | `helpdesk` |
| **Админ** | `admin` | `admin` |

---

## 🏗 Структура проекта

```
helpdesk/
├── backend/                 # Django Project
│   ├── core/               # Project Settings
│   ├── tickets/            # App: Models, Views, Serializers
│   ├── media/              # User uploads (Photos/Videos)
│   └── manage.py
├── frontend/                # Vue 3 Project
│   ├── src/
│   │   ├── views/          # Vue Pages (Login, Dashboard)
│   │   ├── stores/         # Pinia State (Auth)
│   │   ├── router/         # Vue Router
│   │   └── assets/         # Global Styles (theme.css)
│   └── package.json
└── requirements.txt         # Python dependencies
```

---

## 🎨 Стек технологий

- **Frontend:** Vue.js 3 (Composition API), Vite, Pinia, Bootstrap 5, Bootstrap Icons.
- **Backend:** Django 5, Django Rest Framework (DRF).
- **Database:** SQLite (default) / PostgreSQL (production ready).
- **Authentication:** Token Authentication (DRF).
- **Email:** SMTP (Gmail) для пересылки входящих писем.

---

## 📧 Настройка SMTP (Email Forwarding)

Система поддерживает автоматическую пересылку входящих писем с `erkemyzraa@gmail.com` на `myrzabekerkebulanakt@gmail.com`.

### Настройка:

1. **Создайте App Password в Gmail:**
   - Перейдите в [Google Account Settings](https://myaccount.google.com/apppasswords)
   - Создайте пароль приложения для "Почта"

2. **Установите переменные окружения:**
   ```bash
   export EMAIL_HOST_PASSWORD='your-app-password-here'
   ```

3. **Запустите проверку почты (через cron или вручную):**
   ```bash
   cd backend
   python3 manage.py check_email
   ```

   Для автоматической проверки каждые 5 минут добавьте в crontab:
   ```bash
   */5 * * * * cd /path/to/helpdesk/backend && source .venv/bin/activate && python3 manage.py check_email
   ```

---

## ⏱️ Отслеживание времени выполнения

Система автоматически записывает:
- **Время начала работы:** Когда хелпдеск берет заявку в работу.
- **Время завершения:** Когда заявка помечается как выполненная.
- **Длительность:** Автоматически вычисляется и отображается в админ-панели.

---

<p align="center">
  <sub>Developed for Korkyt Ata University</sub>
</p>

