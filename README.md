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
- **Статистика:** Общая сводка и распределение заявок по статусам.
- **Все заявки:** Полный список всех тикетов в системе с фильтрацией.
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
| **Учитель** | `teacher` | `teacher123` |
| **Хелпдеск** | `helpdesk` | `helpdesk123` |
| **Админ** | `admin` | `admin123` |

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

---

<p align="center">
  <sub>Developed for Korkyt Ata University</sub>
</p>

