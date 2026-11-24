# האתר של איילה – החלקות אורגניות ושיקום שיער

אתר תדמית + מערכת קביעת תורים.

## מבנה
| חלק | טכנולוגיה | איפה רץ |
|---|---|---|
| האתר (`index.html`, `services.html`, ...) | HTML, CSS, JavaScript | GitHub Pages |
| קביעת תור (`booking.html`) וניהול (`admin.html`) | JavaScript שמדבר עם השרת | GitHub Pages |
| השרת (`backend/`) | Python, FastAPI, SQLAlchemy | Render (חינם) |
| מסד הנתונים | PostgreSQL | Supabase (חינם) |

## קבצים חשובים
- `js/config.js` – כתובת השרת, מספר וואטסאפ ופרטי בנק. **זה הקובץ היחיד שצריך לשנות כדי לחבר את האתר לשרת.**
- `styles.css` – כל העיצוב. הצבעים בראש הקובץ.
- `backend/app/main.py` – כל הנתיבים של השרת.
- `backend/app/models.py` – הטבלאות במסד הנתונים.
- `.github/workflows/keep-alive.yml` – פונה לשרת כל 3 ימים כדי שמסד הנתונים לא יירדם.

## הרצה מקומית של השרת
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # ב-Windows: .venv\Scripts\activate
pip install -r requirements.txt pytest httpx
ADMIN_PASSWORD=1234 SECRET_KEY=dev uvicorn app.main:app --reload --port 8001
```
בלי `DATABASE_URL` השרת משתמש בקובץ SQLite מקומי.
תיעוד אוטומטי של כל הנתיבים: http://localhost:8001/docs

בדיקות: `python -m pytest -q` (מתוך התיקייה `backend`).

## הגדרה ראשונה
ראי את `SETUP.md`.
