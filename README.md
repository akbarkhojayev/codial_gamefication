# Codial Academy - Analytics API

Django REST Framework asosida qurilgan analytics API. **Ollama'siz**, faqat Django va Database bilan ishlaydi.

## ✨ Xususiyatlar

- ✅ **Ollama'siz** - Hech qanday AI kerak emas
- ✅ **Tez** - Database'dan to'g'ridan-to'g'ri ma'lumot oladi
- ✅ **Har qanday savol** - Savol tahlil qiladi va javob beradi
- ✅ **Qidiruv** - Ism, kurs, guruh bo'yicha qidirish
- ✅ **Analytics** - Talabalar, mentorlar, kurslar statistikasi
- ✅ **Logging** - Barcha so'rovlarni log qiladi
- ✅ **Django Admin** - Oson boshqarish
- ✅ **REST API** - Swagger dokumentatsiyasi

## 🚀 Tez Boshlash

### 1. Dependencies o'rnatish
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Migratsiya
```bash
python manage.py migrate
```

### 3. Superuser yaratish
```bash
python manage.py createsuperuser
```

### 4. Server ishga tushirish
```bash
python manage.py runserver
```

## 📚 API Endpoints

### Health Check
```bash
GET /api/ai/health/
```

### Analytics (Savol bilan)
```bash
POST /api/ai/analytics/
{
  "question": "Eng ko'p ball to'plagan talabalar kimlar?"
}
```

### Qidiruv
```bash
POST /api/ai/search/
{
  "search": "Ali"
}
```

### Talabalar
```bash
GET /api/ai/students/
```

### Kurslar
```bash
GET /api/ai/courses/
```

### Guruhlar
```bash
GET /api/ai/groups/
```

## 🎯 Qanday Ishlaydi?

```
API so'rov: "Eng ko'p ball to'plagan talabalar?"
    ↓
QueryAnalyzer tahlil qiladi
    ↓
Database'dan: SELECT * FROM student ORDER BY point DESC
    ↓
Javob: Top talabalar
    ↓
JSON formatida qaytaradi
```

## 📊 Qo'llab-quvvatlanadigan Savol Turlari

- ✅ "Eng ko'p ball to'plagan talabalar?"
- ✅ "Eng kam ball to'plagan talabalar?"
- ✅ "Jami nechta talaba?"
- ✅ "Talabalar ro'yxati"
- ✅ "Mentorlar haqida"
- ✅ "Kurslar haqida"
- ✅ "Guruhlar haqida"
- ✅ "Kitoblar haqida"
- ✅ "Balllar haqida"
- ✅ "Ali" (qidiruv)

## 🔧 Konfiguratsiya

Hech qanday konfiguratsiya kerak emas! Faqat Django settings.py'da database sozlamalarini tekshiring.

## 📖 Loyihaning Strukturasi

```
.
├── ai/                          # AI bo'limi
│   ├── models.py               # QueryLog model
│   ├── views.py                # API views
│   ├── urls.py                 # URL routing
│   ├── admin.py                # Admin panel
│   ├── services/               # Business logic
│   │   ├── query_analyzer.py   # Savol tahlili
│   │   └── formatter.py        # Response formatting
│   └── utils/                  # Utilities
│       ├── validators.py       # Input validation
│       └── dates.py            # Date utilities
├── main/                        # Main app
├── core/                        # Django settings
├── requirements.txt            # Python dependencies
└── manage.py
```

## 🚨 Muammolar va Yechimlar

### Database error
```bash
python manage.py migrate
```

### Django error
```bash
python manage.py runserver --verbosity 3
```

### Admin panel'ga kirish
```
http://localhost:8000/admin/
```

## 📞 Savol-Javoblar

**Q: Ollama kerakmi?**
A: Yo'q, Ollama'siz ishlaydi.

**Q: Qancha tez?**
A: Juda tez, 1-2 soniya.

**Q: Qancha RAM kerak?**
A: Minimal 2GB, tavsiya 4GB+

**Q: Qancha disk kerak?**
A: Minimal 1GB

**Q: Internet kerakmi?**
A: Yo'q, lokal ishlaydi.

## 📝 Litsenziya

MIT License

## 🤝 Hissa Qo'shish

Pull request'larni qabul qilamiz!
