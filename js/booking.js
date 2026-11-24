// דף קביעת תור ללקוחות
(function () {
  var A = window.AyalaAPI, cfg = A.cfg;
  var $ = function (id) { return document.getElementById(id); };

  var state = { treatment: null, day: null, slot: null, slots: [] };

  // אם עוד לא הוגדרה כתובת שרת - מציגים קביעה בוואטסאפ
  if (!cfg.API_URL) {
    $("booking-form").hidden = true;
    $("no-api").hidden = false;
    $("no-api-wa").href = A.waLink("היי איילה, אשמח לקבוע תור.");
    return;
  }

  // יוצר כפתור בחירה (chip)
  function chip(label, pressed, onClick, sub) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.setAttribute("aria-pressed", pressed ? "true" : "false");
    b.textContent = label;
    if (sub) { var s = document.createElement("small"); s.textContent = sub; b.appendChild(s); }
    b.addEventListener("click", onClick);
    return b;
  }

  // ----- 1. טיפול -----
  var pre = parseInt(new URLSearchParams(location.search).get("t"), 10);
  if (cfg.TREATMENTS[pre]) state.treatment = cfg.TREATMENTS[pre];

  function renderTreatments() {
    var box = $("treatments");
    box.textContent = "";
    cfg.TREATMENTS.forEach(function (t) {
      box.appendChild(chip(t, state.treatment === t, function () {
        state.treatment = t; renderTreatments(); renderSummary();
      }));
    });
  }

  // ----- 2. יום -----
  function days() {
    var seen = [];
    state.slots.forEach(function (s) { if (seen.indexOf(s.day) < 0) seen.push(s.day); });
    return seen;
  }

  function renderDays() {
    var box = $("days");
    box.textContent = "";
    var list = days();
    $("no-slots").hidden = list.length > 0;
    list.forEach(function (d) {
      var count = state.slots.filter(function (s) { return s.day === d; }).length;
      box.appendChild(chip(A.dayLabel(d), state.day === d, function () {
        state.day = d; state.slot = null;
        renderDays(); renderTimes(); renderSummary();
        $("step-time").scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, count === 1 ? "שעה אחת פנויה" : count + " שעות פנויות"));
    });
  }

  // ----- 3. שעה -----
  function renderTimes() {
    var box = $("times");
    box.textContent = "";
    $("step-time").hidden = !state.day;
    state.slots.filter(function (s) { return s.day === state.day; }).forEach(function (s) {
      box.appendChild(chip(A.hhmm(s.start), state.slot && state.slot.id === s.id, function () {
        state.slot = s; renderTimes(); renderSummary();
        $("details").scrollIntoView({ behavior: "smooth", block: "nearest" });
      }));
    });
  }

  function renderSummary() {
    $("details").hidden = !state.slot;
    if (!state.slot) return;
    $("summary").textContent = (state.treatment || "בחרי טיפול למעלה") + " · " +
      A.dayLabel(state.slot.day) + " בשעה " + A.hhmm(state.slot.start);
  }

  async function loadSlots() {
    $("loading").hidden = false;
    $("load-error").hidden = true;
    try {
      state.slots = await A.api("/api/slots");
      // אם השעה שנבחרה כבר לא פנויה - מנקים את הבחירה
      if (state.day && days().indexOf(state.day) < 0) state.day = null;
      if (state.slot && !state.slots.some(function (s) { return s.id === state.slot.id; })) state.slot = null;
      renderDays(); renderTimes(); renderSummary();
    } catch (e) {
      var box = $("load-error");
      box.textContent = e.message + " ";
      var retry = document.createElement("button");
      retry.type = "button"; retry.className = "btn btn--outline btn--small"; retry.textContent = "לנסות שוב";
      retry.addEventListener("click", loadSlots);
      box.appendChild(retry);
      box.hidden = false;
    } finally {
      $("loading").hidden = true;
    }
  }

  // ----- 4. שליחה -----
  $("details").addEventListener("submit", async function (ev) {
    ev.preventDefault();
    var err = $("submit-error");
    err.hidden = true;
    var name = $("b-name").value.trim();
    var phone = $("b-phone").value.trim();
    var problem = !state.treatment ? "צריך לבחור טיפול (שלב 1)." :
      name.length < 2 ? "צריך למלא שם." :
      phone.replace(/\D/g, "").length < 9 ? "צריך למלא מספר טלפון תקין." : "";
    if (problem) { err.textContent = problem; err.hidden = false; return; }

    var btn = $("submit");
    btn.disabled = true; btn.textContent = "שולחת…";
    try {
      var res = await A.api("/api/bookings", {
        method: "POST",
        body: { slot_id: state.slot.id, name: name, phone: phone, treatment: state.treatment }
      });
      showDone(res, name);
    } catch (e) {
      err.textContent = e.message;
      err.hidden = false;
      if (e.status === 409 || e.status === 404) { state.slot = null; loadSlots(); }
    } finally {
      btn.disabled = false; btn.textContent = "אישור התור";
    }
  });

  function addRow(dl, k, v) {
    var dt = document.createElement("dt"); dt.textContent = k;
    var dd = document.createElement("dd"); dd.textContent = v;
    dl.appendChild(dt); dl.appendChild(dd);
  }

  function showDone(res, name) {
    $("booking-form").hidden = true;
    var when = A.dayLabel(res.day) + " בשעה " + A.hhmm(res.start);
    var dl = $("done-details");
    addRow(dl, "טיפול", res.treatment);
    addRow(dl, "מתי", when);
    addRow(dl, "כתובת", "הנרי מורגנטאו 11, ירושלים");

    var bank = cfg.BANK || {};
    if (bank.account) {
      var b = $("bank-details");
      if (bank.amount) addRow(b, "סכום", bank.amount);
      if (bank.bankName) addRow(b, "בנק", bank.bankName);
      if (bank.branch) addRow(b, "סניף", bank.branch);
      addRow(b, "מספר חשבון", bank.account);
      if (bank.owner) addRow(b, "על שם", bank.owner);
      $("bank").hidden = false;
    }
    $("done-wa").href = A.waLink("היי איילה, קבעתי תור באתר: " + res.treatment + ", " + when + ". שם: " + name);
    $("done").hidden = false;
    $("done").focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  renderTreatments();
  loadSlots();
})();
