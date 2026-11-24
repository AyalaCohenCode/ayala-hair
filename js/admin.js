// מסך ניהול תורים למנהלת
(function () {
  var A = window.AyalaAPI, cfg = A.cfg;
  var $ = function (id) { return document.getElementById(id); };
  var TOKEN_KEY = "ayala-admin-token";
  var token = null;
  try { token = sessionStorage.getItem(TOKEN_KEY); } catch (e) {}

  var QUICK = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"];
  var picked = [];

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function show(loggedIn) {
    $("login").hidden = loggedIn;
    $("panel").hidden = !loggedIn;
    $("logout").hidden = !loggedIn;
    if (loggedIn) load();
  }

  function call(path, opts) {
    opts = opts || {};
    opts.token = token;
    return A.api(path, opts).catch(function (e) {
      if (e.status === 401) { logout(); throw new Error("צריך להתחבר מחדש."); }
      throw e;
    });
  }

  function logout() {
    token = null;
    try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
    show(false);
  }

  // ----- כניסה -----
  if (!cfg.API_URL) {
    var n = $("login-error");
    n.textContent = "עוד לא הוגדרה כתובת השרת בקובץ js/config.js.";
    n.hidden = false;
  }

  $("login").addEventListener("submit", async function (ev) {
    ev.preventDefault();
    var err = $("login-error"), btn = $("login-btn");
    err.hidden = true;
    if (!$("pw").value) { err.textContent = "צריך להקליד סיסמה."; err.hidden = false; return; }
    btn.disabled = true; btn.textContent = "מתחברת…";
    try {
      var res = await A.api("/api/admin/login", { method: "POST", body: { password: $("pw").value } });
      token = res.token;
      try { sessionStorage.setItem(TOKEN_KEY, token); } catch (e) {}
      $("pw").value = "";
      show(true);
    } catch (e) {
      err.textContent = e.message; err.hidden = false;
    } finally {
      btn.disabled = false; btn.textContent = "כניסה";
    }
  });
  $("logout").addEventListener("click", logout);

  // ----- הוספת שעות -----
  function renderQuick() {
    var box = $("quick-times");
    box.textContent = "";
    var all = QUICK.slice();
    picked.forEach(function (t) { if (all.indexOf(t) < 0) all.push(t); });
    all.sort();
    all.forEach(function (t) {
      var b = el("button", "chip", t);
      b.type = "button";
      b.setAttribute("aria-pressed", picked.indexOf(t) >= 0 ? "true" : "false");
      b.addEventListener("click", function () {
        var i = picked.indexOf(t);
        if (i >= 0) picked.splice(i, 1); else picked.push(t);
        renderQuick();
      });
      box.appendChild(b);
    });
  }

  $("add-custom-btn").addEventListener("click", function () {
    var v = $("add-custom").value;
    if (v && picked.indexOf(v) < 0) { picked.push(v); renderQuick(); }
    $("add-custom").value = "";
  });

  // ברירת מחדל: מחר
  var tm = new Date(); tm.setDate(tm.getDate() + 1);
  $("add-day").value = tm.getFullYear() + "-" + String(tm.getMonth() + 1).padStart(2, "0") + "-" + String(tm.getDate()).padStart(2, "0");

  $("add-form").addEventListener("submit", async function (ev) {
    ev.preventDefault();
    var msg = $("add-msg");
    msg.className = "notice"; msg.hidden = true;
    var day = $("add-day").value;
    if (!day || !picked.length) {
      msg.className = "notice notice--error";
      msg.textContent = !day ? "צריך לבחור תאריך." : "צריך לבחור לפחות שעה אחת.";
      msg.hidden = false; return;
    }
    try {
      var created = await call("/api/admin/slots", { method: "POST", body: { day: day, times: picked } });
      msg.className = "notice notice--ok";
      msg.textContent = created.length
        ? "נוספו " + created.length + " שעות ל" + A.dayLabel(day) + "."
        : "השעות האלה כבר קיימות ב" + A.dayLabel(day) + ".";
      msg.hidden = false;
      picked = []; renderQuick(); load();
    } catch (e) {
      msg.className = "notice notice--error"; msg.textContent = e.message; msg.hidden = false;
    }
  });

  // ----- רשימת השעות -----
  async function act(fn) {
    $("list-error").hidden = true;
    try { await fn(); await load(); }
    catch (e) { $("list-error").textContent = e.message; $("list-error").hidden = false; }
  }

  function row(s) {
    var r = el("div", "slot-row");
    var who = el("div", "who");
    who.appendChild(el("span", "time", A.hhmm(s.start)));
    if (s.booking) {
      var b = s.booking;
      who.appendChild(el("span", null, b.name + " · " + b.treatment));
      var tel = el("a", null, b.phone);
      tel.href = "tel:" + b.phone; tel.dir = "ltr"; tel.style.alignSelf = "flex-start";
      who.appendChild(tel);
    }
    r.appendChild(who);

    var actions = el("div", "actions");
    if (!s.booking) {
      actions.appendChild(el("span", "badge badge--free", "פנוי"));
      var del = el("button", "btn btn--danger btn--small", "מחיקה");
      del.type = "button";
      del.setAttribute("aria-label", "מחיקת השעה " + A.hhmm(s.start) + " ב" + A.dayLabel(s.day));
      del.addEventListener("click", function () {
        act(function () { return call("/api/admin/slots/" + s.id, { method: "DELETE" }); });
      });
      actions.appendChild(del);
    } else {
      var paid = s.booking.paid;
      actions.appendChild(el("span", "badge " + (paid ? "badge--paid" : "badge--wait"), paid ? "שולם" : "ממתין לתשלום"));
      var tog = el("button", paid ? "btn btn--outline btn--small" : "btn btn--main btn--small", paid ? "ביטול סימון" : "סימון כשולם");
      tog.type = "button";
      tog.addEventListener("click", function () {
        act(function () { return call("/api/admin/bookings/" + s.booking.id, { method: "PATCH", body: { paid: !paid } }); });
      });
      actions.appendChild(tog);
      var cancel = el("button", "btn btn--danger btn--small", "ביטול תור");
      cancel.type = "button";
      cancel.addEventListener("click", function () {
        if (!window.confirm("לבטל את התור של " + s.booking.name + "? השעה תחזור להיות פנויה.")) return;
        act(function () { return call("/api/admin/bookings/" + s.booking.id, { method: "DELETE" }); });
      });
      actions.appendChild(cancel);
      var wa = el("a", "btn btn--outline btn--small", "וואטסאפ");
      var num = s.booking.phone.replace(/^0/, "972");
      wa.href = "https://wa.me/" + num; wa.target = "_blank"; wa.rel = "noopener";
      actions.appendChild(wa);
    }
    r.appendChild(actions);
    return r;
  }

  async function load() {
    $("list-error").hidden = true;
    var slots;
    try { slots = await call("/api/admin/slots"); }
    catch (e) { $("list-error").textContent = e.message; $("list-error").hidden = false; return; }

    var booked = slots.filter(function (s) { return s.booking; });
    $("st-free").textContent = slots.length - booked.length;
    $("st-booked").textContent = booked.length;
    $("st-wait").textContent = booked.filter(function (s) { return !s.booking.paid; }).length;
    $("empty").hidden = slots.length > 0;

    var list = $("list");
    list.textContent = "";
    var current = null, group = null;
    slots.forEach(function (s) {
      if (s.day !== current) {
        current = s.day;
        group = el("div", "day-group");
        group.appendChild(el("h3", null, A.dayLabel(s.day)));
        list.appendChild(group);
      }
      group.appendChild(row(s));
    });
  }

  $("refresh").addEventListener("click", load);

  renderQuick();
  show(!!token);
})();
