"""בדיקות לשרת. מריצים מתוך התיקייה backend:  python -m pytest -q"""
import os
import tempfile
from datetime import date, datetime, timedelta

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{_db.name}")
os.environ["ADMIN_PASSWORD"] = "test-pass"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

TOMORROW = (date.today() + timedelta(days=1)).isoformat()


def client():
    return TestClient(app)


def admin_headers(c):
    r = c.post("/api/admin/login", json={"password": "test-pass"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health():
    with client() as c:
        assert c.get("/health?db_check=true").json() == {"ok": True}


def test_wrong_password():
    with client() as c:
        assert c.post("/api/admin/login", json={"password": "nope"}).status_code == 401
        assert c.get("/api/admin/slots").status_code == 401
        assert c.get("/api/admin/slots", headers={"Authorization": "Bearer admin.9999999999.bad"}).status_code == 401


def test_full_flow():
    with client() as c:
        h = admin_headers(c)
        r = c.post("/api/admin/slots", json={"day": TOMORROW, "times": ["09:00", "13:00", "13:00"]}, headers=h)
        assert r.status_code == 201
        assert len(r.json()) == 2  # הכפילות לא נוספה
        # הוספה חוזרת של אותה שעה לא יוצרת כפילות
        assert c.post("/api/admin/slots", json={"day": TOMORROW, "times": ["09:00"]}, headers=h).json() == []

        free = c.get("/api/slots").json()
        ids = [s["id"] for s in free if s["day"] == TOMORROW]
        assert len(ids) == 2

        booking = {"slot_id": ids[0], "name": " רחל  כהן ", "phone": "054-123-4567", "treatment": "שורשים"}
        r = c.post("/api/bookings", json=booking)
        assert r.status_code == 201, r.text

        # אי אפשר לקבוע את אותה שעה פעמיים
        assert c.post("/api/bookings", json=booking).status_code == 409
        assert ids[0] not in [s["id"] for s in c.get("/api/slots").json()]

        slots = c.get("/api/admin/slots", headers=h).json()
        booked = next(s for s in slots if s["id"] == ids[0])
        assert booked["booking"]["name"] == "רחל כהן"
        assert booked["booking"]["phone"] == "0541234567"
        bid = booked["booking"]["id"]

        assert c.patch(f"/api/admin/bookings/{bid}", json={"paid": True}, headers=h).json()["paid"] is True
        # אי אפשר למחוק שעה שיש בה תור בלי force
        assert c.delete(f"/api/admin/slots/{ids[0]}", headers=h).status_code == 409
        # ביטול התור מחזיר את השעה לרשימת הפנויות
        assert c.delete(f"/api/admin/bookings/{bid}", headers=h).status_code == 204
        assert ids[0] in [s["id"] for s in c.get("/api/slots").json()]
        assert c.delete(f"/api/admin/slots/{ids[1]}", headers=h).status_code == 204


def test_validation():
    with client() as c:
        h = admin_headers(c)
        sid = c.post("/api/admin/slots", json={"day": TOMORROW, "times": ["17:00"]}, headers=h).json()[0]["id"]
        bad = [
            {"slot_id": sid, "name": "א", "phone": "0541234567", "treatment": "שורשים"},
            {"slot_id": sid, "name": "רחל", "phone": "123", "treatment": "שורשים"},
            {"slot_id": sid, "name": "רחל", "phone": "0541234567", "treatment": "משהו אחר"},
        ]
        for b in bad:
            assert c.post("/api/bookings", json=b).status_code == 422
        assert c.post("/api/bookings", json={**bad[0], "slot_id": 999999, "name": "רחל"}).status_code == 404


def test_past_slots_hidden():
    with client() as c:
        h = admin_headers(c)
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        sid = c.post("/api/admin/slots", json={"day": yesterday, "times": ["10:00"]}, headers=h).json()[0]["id"]
        assert sid not in [s["id"] for s in c.get("/api/slots").json()]
        r = c.post("/api/bookings", json={"slot_id": sid, "name": "רחל", "phone": "0541234567", "treatment": "שורשים"})
        assert r.status_code == 404
