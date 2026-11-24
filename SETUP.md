# הגדרה ראשונה של מערכת התורים

3 שלבים. כל אחד לוקח בערך 10–15 דקות. הכל בחינם.

---

## שלב 1: מסד נתונים ב-Supabase

**מה זה?** המקום שבו נשמרים השעות והתורים.

1. נכנסים ל-supabase.com ← **Start your project** ← נרשמים עם חשבון GitHub.
2. **New project**:
   - Name: `ayala-booking`
   - Database Password: לוחצים **Generate a password** ושומרים אותה בצד.
     (אם בוחרים לבד – רק אותיות באנגלית ומספרים, בלי סימנים.)
   - Region: **Central EU (Frankfurt)** – הכי קרוב לישראל.
   - לוחצים **Create new project** ומחכים כדקה.
3. למעלה לוחצים **Connect**.
4. בוחרים **Session pooler** ומעתיקים את הכתובת. היא נראית ככה:
   `postgresql://postgres.xxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres`
5. מחליפים את `[YOUR-PASSWORD]` (כולל הסוגריים המרובעים) בסיסמה מסעיף 2.
6. שומרים את הכתובת המלאה בצד. **לא מעלים אותה ל-GitHub!**

> למה Session pooler? כי Render מתחבר רק דרך סוג חיבור שנקרא IPv4, וזה החיבור שתומך בו.

---

## שלב 2: השרת ב-Render

**מה זה?** המחשב באינטרנט שמריץ את קוד ה-Python בתיקייה `backend`.

1. נכנסים ל-render.com ← נרשמים עם חשבון GitHub.
2. **New** ← **Web Service** ← בוחרים את הריפו `ayala-hair`.
   (אם הוא לא מופיע: **Configure account** ונותנים ל-Render גישה לריפו.)
3. ממלאים:
   | שדה | מה לכתוב |
   |---|---|
   | Name | `ayala-booking` |
   | Region | **Frankfurt (EU Central)** |
   | Branch | `main` |
   | Root Directory | `backend` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | **Free** |
4. למטה, ב-**Environment Variables**, מוסיפים 4 משתנים (**Add Environment Variable**):
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | הכתובת המלאה משלב 1 |
   | `ADMIN_PASSWORD` | הסיסמה שאיתה תיכנסי למסך הניהול |
   | `SECRET_KEY` | לוחצים **Generate** (מחרוזת אקראית ארוכה) |
   | `ALLOWED_ORIGINS` | `https://ayalacohencode.github.io` |
5. **Deploy Web Service**. מחכים כמה דקות עד שכתוב **Live** בירוק.
6. למעלה מופיעה הכתובת של השרת, למשל `https://ayala-booking.onrender.com`. מעתיקים אותה.
7. בדיקה: פותחים בדפדפן את הכתובת + `/health`. צריך להופיע: `{"ok":true}`

---

## שלב 3: חיבור האתר לשרת

1. ב-GitHub, בריפו `ayala-hair`, פותחים את `js/config.js` ← עיפרון ✏️.
2. משנים את השורה:
   `API_URL: "",`
   ל:
   `API_URL: "https://ayala-booking.onrender.com",`
   (הכתובת משלב 2, **בלי** `/` בסוף.)
3. אפשר למלא באותו קובץ גם את פרטי הבנק.
4. **Commit changes**.
5. אחרי דקה-שתיים:
   - נכנסים ל-`.../admin.html`, מתחברים עם `ADMIN_PASSWORD`, ומוסיפים שעות.
   - נכנסים ל-`.../booking.html` ובודקים שהשעות מופיעות.

---

## חשוב לדעת

- **השרת נרדם.** בגרסה החינמית, אחרי 15 דקות בלי שימוש השרת "נרדם", ולוקח לו עד דקה להתעורר.
  האתר שולח לשרת "בוקר טוב" ברגע שמישהי נכנסת לאתר, כך שבדרך כלל הוא יהיה ער עד שהיא תגיע לקביעת תור.
- **מסד הנתונים נרדם אחרי שבוע בלי שימוש.** הקובץ `.github/workflows/keep-alive.yml` פונה אליו כל 3 ימים, כדי שזה לא יקרה.
  - GitHub עוצר פעולות מתוזמנות בריפו שלא היה בו שינוי 60 יום. אם זה קורה, נכנסים ל-**Actions** ומפעילים מחדש.
- **הסיסמאות נשמרות רק ב-Render**, לא בקוד. הריפו ציבורי, אז אף פעם לא כותבים סיסמה בקובץ.
- **שינוי סיסמת מנהלת:** Render ← השרת ← **Environment** ← משנים את `ADMIN_PASSWORD` ← **Save** (השרת מתעדכן לבד).
