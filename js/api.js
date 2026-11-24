// פונקציות משותפות לדיבור עם השרת
(function () {
  var cfg = window.AYALA || {};

  // השרת החינמי "נרדם" אחרי 15 דקות בלי שימוש. ברגע שמישהי נכנסת לאתר -
  // שולחים לו "בוקר טוב", כדי שעד שהיא תגיע לקביעת תור הוא כבר יהיה ער.
  if (cfg.API_URL) {
    try { fetch(cfg.API_URL + "/health", { mode: "cors" }).catch(function () {}); } catch (e) {}
  }

  // קריאה לשרת. מחזירה את התשובה כ-JSON, או זורקת שגיאה עם הודעה בעברית.
  async function api(path, options) {
    options = options || {};
    var headers = { "Content-Type": "application/json" };
    if (options.token) headers["Authorization"] = "Bearer " + options.token;
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, options.timeout || 90000);
    var res;
    try {
      res = await fetch(cfg.API_URL + path, {
        method: options.method || "GET",
        headers: headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal
      });
    } catch (e) {
      throw new Error("אין חיבור לשרת כרגע. נסי שוב בעוד רגע.");
    } finally {
      clearTimeout(timer);
    }
    if (res.status === 204) return null;
    var data = null;
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) {
      var msg = "משהו השתבש. נסי שוב.";
      if (data && typeof data.detail === "string") msg = data.detail;
      else if (data && Array.isArray(data.detail) && data.detail[0]) {
        var m = String(data.detail[0].msg || "");
        msg = m.replace(/^Value error, /, "") || msg;
      }
      var err = new Error(msg);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  var DAYS = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];

  // "2026-12-02" -> "יום רביעי, 2.12"
  function dayLabel(iso, short) {
    var p = iso.split("-");
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    var date = (+p[2]) + "." + (+p[1]);
    return short ? DAYS[d.getDay()].charAt(0) + "׳ " + date : "יום " + DAYS[d.getDay()] + ", " + date;
  }

  // "13:00:00" -> "13:00"
  function hhmm(t) { return String(t).slice(0, 5); }

  function waLink(text) {
    return "https://wa.me/" + cfg.WHATSAPP + "?text=" + encodeURIComponent(text);
  }

  window.AyalaAPI = { api: api, dayLabel: dayLabel, hhmm: hhmm, waLink: waLink, cfg: cfg };
})();
