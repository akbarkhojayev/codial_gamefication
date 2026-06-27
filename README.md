# Codial Academy - Gamification API

Django REST Framework asosida qurilgan academy/gamification API. Loyiha student, mentor, guruh, kurs, coin/point, davomat, kitob, yangilik, auction/product va admin boshqaruv oqimlarini qamrab oladi.

## Xususiyatlar

- JWT autentifikatsiya
- Role-based permission: admin, teacher, student
- Student va mentor profillari
- Kurs va guruh boshqaruvi
- Studentni guruhga qo'shish va guruhlar orasida ko'chirish
- Davomat olish
- Point/coin berish va tarixini ko'rish
- Leaderboard va active groups
- Admin boshqaruvi
- Swagger dokumentatsiyasi

## Tez Boshlash

### 1. Dependencies o'rnatish

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Migratsiya

```bash
python3 manage.py migrate
```

### 3. Superuser yaratish

```bash
python3 manage.py createsuperuser
```

### 4. Server ishga tushirish

```bash
python3 manage.py runserver
```

## Asosiy Endpointlar

### Auth

```http
POST /token/
POST /token/refresh/
GET /get/me/
```

### Users/Admin

```http
GET /users/
GET /admins/
POST /admins/add/
GET /admins/<id>/
PATCH /admins/<id>/
DELETE /admins/<id>/
```

### Courses, Mentors, Students, Groups

```http
GET /courses/
POST /courses/
GET /mentors/
POST /mentors/add/
GET /students/
POST /students/add/
POST /students/transfer/
GET /groups/
POST /groups/add/
POST /groups/<id>/students/add/
```

### Assessment va Davomat

```http
GET /api/teacher/assessment/<group_id>/?date=YYYY-MM-DD
POST /api/teacher/assessment/save/
POST /api/teacher/assessment/update/

GET /api/teacher/attendance/<group_id>/?date=YYYY-MM-DD
POST /api/teacher/attendance/save/
```

### Gamification

```http
GET /points/
POST /points/
GET /coin-history/
GET /leaderboard/
GET /active-groups/
GET /pointtypes/
```

### Content va Auction

```http
GET /books/
GET /news/
POST /news/add/
GET /auctions/
GET /products/
```

## Student Ko'chirish Misoli

```http
POST /students/transfer/
```

```json
{
  "student_id": 1,
  "from_group_id": 2,
  "to_group_id": 3,
  "note": "Frontend guruhiga o'tkazildi"
}
```

Admin istalgan guruhlar orasida ko'chira oladi. Teacher esa o'ziga biriktirilgan guruhdagi studentni boshqa faol guruhga ko'chira oladi.

## Davomat Misoli

```http
POST /api/teacher/attendance/save/
```

```json
{
  "group_id": 2,
  "date": "2026-06-27",
  "items": [
    {"student_id": 1, "status": "present"},
    {"student_id": 2, "status": "absent", "note": "Sababsiz"}
  ]
}
```

Statuslar: `present`, `absent`, `late`, `excused`.

## Loyiha Strukturasi

```text
.
├── core/              # Django settings va URL routing
├── main/              # Asosiy domain: users, groups, points, attendance
├── requirements.txt
└── manage.py
```

## Muammolar

### Django import error

Virtualenv aktivligini va dependencylar o'rnatilganini tekshiring:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Migration kerak bo'lsa

```bash
python3 manage.py migrate
```
