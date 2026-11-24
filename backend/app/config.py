"""הגדרות השרת. כל הערכים מגיעים ממשתני סביבה (Environment Variables) ב-Render,
כדי שסיסמאות לא יישמרו בקוד שנמצא ב-GitHub."""
import os

# כתובת מסד הנתונים. בלי הגדרה - קובץ SQLite מקומי, לבדיקות במחשב.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# הסיסמה של המנהלת
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# מפתח סודי לחתימה על הכניסה של המנהלת. מחרוזת ארוכה ואקראית.
SECRET_KEY = os.getenv("SECRET_KEY", "")

# מאילו אתרים מותר לפנות לשרת, מופרד בפסיקים
ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://ayalacohencode.github.io,http://localhost:8000,http://127.0.0.1:8000",
).split(",") if o.strip()]

# אזור הזמן של העסק
TIMEZONE = "Asia/Jerusalem"

# כמה זמן הכניסה של המנהלת תקפה (בשעות)
TOKEN_HOURS = 12

# כמה ימים קדימה לקוחות יכולות לראות תורים
DAYS_AHEAD = 60

TREATMENTS = ["שיקום שיער", "החלקה אורגנית משקמת", "שורשים"]


def sqlalchemy_url(url: str) -> str:
    """Supabase נותן כתובת שמתחילה ב-postgresql:// - SQLAlchemy צריך לדעת באיזה דרייבר להשתמש."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url
