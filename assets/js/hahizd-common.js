/**
 * Shared client utilities for ההזדמנות שלי static site.
 * Forms send to Google Apps Script via GET (reliable cross-origin).
 */
(function () {
  'use strict';

  var HAHIZD_SHEETS_URL =
    'https://script.google.com/macros/s/AKfycbwjc_eLPFBQsXtbHNV4Th6YqDs2nlTeUUS6_D0BDtL9ck7qsXn42fPgWS_xKmrvdvEy/exec';

  var SESSION_KEY = 'hahizd_session';
  var RATE_KEY = 'hahizd_rl';
  var PHONES_KEY = 'hahizd_phones';
  var RATE_MAX = 10;
  var RATE_WINDOW_MS = 10 * 60 * 1000;
  var SESSION_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
  var SESSION_REVERIFY_MS = 24 * 60 * 60 * 1000;

  function normalizePhone(phone) {
    return String(phone || '')
      .replace(/[\s\-()]/g, '')
      .replace(/\D/g, '')
      .replace(/^0+/, '');
  }

  function isValidPhone(phone) {
    return normalizePhone(phone).length >= 9;
  }

  var CALENDLY_URL = 'https://calendly.com/giladunna/30min';

  function checkRateLimit() {
    try {
      var now = Date.now();
      var times = JSON.parse(localStorage.getItem(RATE_KEY) || '[]');
      times = times.filter(function (t) {
        return now - t < RATE_WINDOW_MS;
      });
      if (times.length >= RATE_MAX) return false;
      times.push(now);
      localStorage.setItem(RATE_KEY, JSON.stringify(times));
      return true;
    } catch (e) {
      return true;
    }
  }

  function savePhoneUX(phone) {
    try {
      var norm = normalizePhone(phone);
      var saved = JSON.parse(localStorage.getItem(PHONES_KEY) || '[]');
      if (saved.indexOf(norm) === -1) saved.push(norm);
      localStorage.setItem(PHONES_KEY, JSON.stringify(saved));
    } catch (e) {}
  }

  function getSession() {
    try {
      var raw = localStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      var s = JSON.parse(raw);
      if (!s || !s.phone || !s.name || !s.ts) return null;
      if (Date.now() - s.ts > SESSION_MAX_AGE_MS) {
        localStorage.removeItem(SESSION_KEY);
        return null;
      }
      return s;
    } catch (e) {
      return null;
    }
  }

  function setSession(name, phone) {
    var stored = isValidPhone(phone) ? normalizePhone(phone) : phone;
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({ name: name, phone: stored, ts: Date.now() })
    );
  }

  function clearSession() {
    localStorage.removeItem(SESSION_KEY);
  }

  function paramsFromPayload(payload) {
    var p = new URLSearchParams();
    Object.keys(payload).forEach(function (k) {
      if (payload[k] != null && payload[k] !== '') p.append(k, payload[k]);
    });
    return p;
  }

  function honeypotValue(el) {
    if (!el || !el.value.trim()) return '';
    return el.dataset.userFilled === '1' ? el.value.trim() : '';
  }

  function initHoneypotFields() {
    document.querySelectorAll('input[name="_hp"]').forEach(function (el) {
      el.setAttribute('autocomplete', 'off');
      el.setAttribute('data-lpignore', 'true');
      el.setAttribute('data-1p-ignore', 'true');
      el.addEventListener('input', function () {
        el.dataset.userFilled = '1';
      });
    });
  }

  function hahizdRequest(payload, preferJson) {
    if (payload._hp) {
      return Promise.resolve(preferJson ? { ok: true, found: false } : { ok: true });
    }
    var isFormSubmit = !payload.action && payload.form_type !== 'calendly_booking';
    if (isFormSubmit && !checkRateLimit()) {
      return Promise.reject(new Error('rate_limit'));
    }
    var qs = paramsFromPayload(payload).toString();
    return fetch(HAHIZD_SHEETS_URL + '?' + qs, { method: 'GET' }).then(function (r) {
      if (!r.ok) throw new Error('get_failed');
      if (preferJson) return r.json();
      return { ok: true };
    });
  }

  function hahizdSubmit(payload) {
    return hahizdRequest(payload, false);
  }

  function hahizdLookup(name, phone) {
    return hahizdRequest(
      { action: 'lookup', name: name, phone: normalizePhone(phone) },
      true
    );
  }

  function hahizdCodeLookup(code) {
    return hahizdRequest({ action: 'code_lookup', code: code }, true);
  }

  function hahizdVisit(phone) {
    return hahizdRequest({ action: 'visit', phone: normalizePhone(phone) }, false).catch(
      function () {}
    );
  }

  var HP_STYLE =
    'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;' +
    'clip:rect(0,0,0,0);white-space:nowrap;border:0;opacity:0;pointer-events:none';

  function resetHorizontalScroll() {
    window.scrollTo(0, window.scrollY || 0);
    document.documentElement.scrollLeft = 0;
    document.body.scrollLeft = 0;
  }

  resetHorizontalScroll();
  document.addEventListener('DOMContentLoaded', initHoneypotFields);
  document.addEventListener('DOMContentLoaded', renderNavUser);
  window.addEventListener('load', initHoneypotFields);
  window.addEventListener('load', resetHorizontalScroll);
  window.addEventListener('pageshow', resetHorizontalScroll);

  (function injectHpStyle() {
    var s = document.createElement('style');
    s.textContent = 'input[name="_hp"]{' + HP_STYLE + '}';
    document.head.appendChild(s);
  })();

  function initNav(options) {
    options = options || {};
    var hamburger = document.getElementById('navHamburger');
    var drawer = document.getElementById('navDrawer');
    var overlay = document.getElementById('navOverlay');
    if (hamburger && drawer && overlay) {
      var drawerOpen = false;
      function openDrawer() {
        drawerOpen = true;
        hamburger.classList.add('open');
        drawer.classList.add('open');
        overlay.classList.add('open');
        if (options.lockBodyOnDrawer !== false) document.body.style.overflow = 'hidden';
        hamburger.setAttribute('aria-expanded', 'true');
      }
      function closeDrawer() {
        drawerOpen = false;
        hamburger.classList.remove('open');
        drawer.classList.remove('open');
        overlay.classList.remove('open');
        if (options.lockBodyOnDrawer !== false) document.body.style.overflow = '';
        hamburger.setAttribute('aria-expanded', 'false');
      }
      hamburger.addEventListener('click', function () {
        drawerOpen ? closeDrawer() : openDrawer();
      });
      overlay.addEventListener('click', closeDrawer);
      document.querySelectorAll('.drawer-link, .nav-drawer .btn').forEach(function (l) {
        l.addEventListener('click', closeDrawer);
      });
    }
    if (options.scrollNavbar !== false) {
      window.addEventListener('scroll', function () {
        var nb = document.getElementById('navbar');
        if (nb) nb.classList.toggle('scrolled', window.scrollY > 10);
      });
    }
  }

  function renderNavUser() {
    var hamburger = document.getElementById('navHamburger');
    if (!hamburger) return;
    var existing = document.getElementById('navUserChip');
    if (existing) existing.remove();

    var s = getSession();
    var chip = document.createElement('div');
    chip.id = 'navUserChip';
    chip.style.cssText = 'display:flex;align-items:center;gap:8px;flex-shrink:0';

    if (s) {
      chip.innerHTML =
        '<button onclick="window.haHizdLogout()" style="font-size:.78rem;color:#EF4444;background:none;border:1px solid #FCA5A5;border-radius:50px;padding:4px 12px;cursor:pointer;font-family:inherit;font-weight:600">התנתק</button>';
    } else {
      chip.innerHTML =
        '<button onclick="window.haHizdShowAuth()" style="font-size:.82rem;color:#1A56A0;background:none;border:2px solid #1A56A0;border-radius:50px;padding:6px 16px;cursor:pointer;font-family:inherit;font-weight:700">התחבר</button>';
    }
    hamburger.parentNode.insertBefore(chip, hamburger);
  }

  window.haHizdLogout = function () {
    clearSession();
    renderNavUser();
    // Reset button state
    var btn = document.getElementById('authBtn');
    var btnTxt = document.getElementById('authBtnTxt');
    var spin = document.getElementById('authSpin');
    if (btn) btn.disabled = false;
    if (btnTxt) btnTxt.style.display = '';
    if (spin) spin.style.display = 'none';
    // Clear fields
    ['authName','authPhone','authCode'].forEach(function(id){
      var el = document.getElementById(id);
      if (el) { el.value = ''; el.classList.remove('auth-err'); }
    });
    var terms = document.getElementById('authTerms');
    if (terms) terms.checked = false;
    var errEl = document.getElementById('authError');
    if (errEl) errEl.style.display = 'none';
    var o = document.getElementById('authOverlay');
    if (o) { o.style.opacity = '1'; o.style.display = 'flex'; }
    document.body.style.overflow = 'hidden';
    var topBar = document.getElementById('authTopBar');
    if (topBar) topBar.classList.add('visible');
    showAuthView('Login');
  };

  function injectAuthCloseBtn() {
    var card = document.querySelector('.auth-card');
    if (!card || document.getElementById('authCloseBtn')) return;

    // Make card compact so it fits on screen
    card.style.cssText += ';padding:24px 28px;max-height:90vh;overflow-y:auto';

    function closeOverlay() {
      var o = document.getElementById('authOverlay');
      if (o) { o.style.transition='opacity .3s'; o.style.opacity='0'; setTimeout(function(){ o.style.display='none'; o.style.opacity='1'; },320); }
      var topBar = document.getElementById('authTopBar');
      if (topBar) topBar.classList.remove('visible');
      document.body.style.overflow = '';
    }

    // Top row: X (right) + חזרה לדף הבית (left)
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:8px';

    var closeBtn = document.createElement('button');
    closeBtn.id = 'authCloseBtn';
    closeBtn.setAttribute('aria-label', 'סגור');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = 'background:none;border:none;font-size:1.2rem;color:#94A3B8;cursor:pointer;padding:4px 6px;border-radius:6px;line-height:1;transition:color .2s';
    closeBtn.onmouseover = function(){ closeBtn.style.color='#1A56A0'; };
    closeBtn.onmouseout = function(){ closeBtn.style.color='#94A3B8'; };
    closeBtn.onclick = function(){
      var session = getSession();
      if (session) { closeOverlay(); } else { window.history.back(); }
    };

    var homeLink = document.createElement('a');
    homeLink.href = 'hahazdamnut.html';
    homeLink.innerHTML = '← חזרה לדף הבית';
    homeLink.style.cssText = 'font-size:.8rem;color:#64748B;text-decoration:none;font-weight:600;transition:color .2s';
    homeLink.onmouseover = function(){ homeLink.style.color='#1A56A0'; };
    homeLink.onmouseout = function(){ homeLink.style.color='#64748B'; };

    row.appendChild(closeBtn);
    row.appendChild(homeLink);
    card.insertBefore(row, card.firstChild);
  }

  window.haHizdShowAuth = function () {
    var o = document.getElementById('authOverlay');
    if (!o) { window.location.href = 'employment.html'; return; }
    injectAuthCloseBtn();
    var btn = document.getElementById('authBtn');
    var btnTxt = document.getElementById('authBtnTxt');
    var spin = document.getElementById('authSpin');
    if (btn) btn.disabled = false;
    if (btnTxt) btnTxt.style.display = '';
    if (spin) spin.style.display = 'none';
    var errEl = document.getElementById('authError');
    if (errEl) errEl.style.display = 'none';
    o.style.opacity = '1';
    o.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    showAuthView('Login');
  };

  function grantAuthAccess(name, phone) {
    setSession(name, phone);
    savePhoneUX(phone);
    hahizdVisit(phone);
    document.documentElement.style.visibility = '';
    renderNavUser();
    document.body.style.overflow = '';
    var topBar = document.getElementById('authTopBar');
    if (topBar) topBar.classList.remove('visible');
    var o = document.getElementById('authOverlay');
    if (o) {
      o.style.transition = 'opacity .4s ease';
      o.style.opacity = '0';
      setTimeout(function () {
        o.style.display = 'none';
      }, 420);
    }
  }

  function showAuthView(view) {
    ['Login', 'Reg', 'Success'].forEach(function (x) {
      var el = document.getElementById('authView' + x);
      if (el) el.style.display = x === view ? '' : 'none';
    });
    var verifying = document.getElementById('authVerifying');
    if (verifying) verifying.style.display = 'none';
  }

  function showAuthVerifying(show) {
    var verifying = document.getElementById('authVerifying');
    if (!verifying && show) {
      verifying = document.createElement('div');
      verifying.id = 'authVerifying';
      verifying.style.cssText = 'text-align:center;padding:32px 16px';
      verifying.innerHTML =
        '<div class="auth-spin" style="display:block;margin:0 auto 16px;width:28px;height:28px;border-width:3px"></div>' +
        '<p style="color:#64748B;font-size:.95rem">בודק הרשאות...</p>';
      var card = document.querySelector('.auth-card');
      if (card) card.appendChild(verifying);
    }
    if (verifying) verifying.style.display = show ? 'block' : 'none';
    if (show) {
      ['Login', 'Reg', 'Success'].forEach(function (x) {
        var el = document.getElementById('authView' + x);
        if (el) el.style.display = 'none';
      });
    }
  }

  function initProtectedAuth() {
    var overlay = document.getElementById('authOverlay');
    if (!overlay) return;

    // If fresh session exists — grant immediately, no UI flicker
    var session = getSession();
    if (session && Date.now() - session.ts < SESSION_REVERIFY_MS) {
      grantAuthAccess(session.name, session.phone);
      renderNavUser();
      return;
    }

    renderNavUser();
    injectAuthCloseBtn();
    document.documentElement.style.visibility = '';
    var topBar = document.getElementById('authTopBar');
    document.body.style.overflow = 'hidden';
    overlay.style.display = 'flex';
    if (topBar) topBar.classList.add('visible');

    function bindEnter(ids, fn) {
      ids.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
          el.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') fn();
          });
        }
      });
    }

    window.authShowReg = function () {
      showAuthView('Reg');
      setTimeout(function () {
        var f = document.getElementById('regName');
        if (f) f.focus();
      }, 50);
    };
    window.authShowLogin = function () {
      showAuthView('Login');
    };

    bindEnter(['authName', 'authPhone'], function () {
      window.doAuthLogin();
    });
    bindEnter(['regName', 'regPhone'], function () {
      window.doAuthReg();
    });

    window.doAuthLogin = function () {
      var nameEl = document.getElementById('authName');
      var phoneEl = document.getElementById('authPhone');
      var codeEl = document.getElementById('authCode');
      var termsEl = document.getElementById('authTerms');
      var errEl = document.getElementById('authErr');
      var name = nameEl ? nameEl.value.trim() : '';
      var phone = phoneEl ? phoneEl.value : '';
      var code = codeEl ? codeEl.value.trim() : '';
      if (nameEl) nameEl.classList.remove('auth-err');
      if (phoneEl) phoneEl.classList.remove('auth-err');
      if (codeEl) codeEl.classList.remove('auth-err');
      if (errEl) errEl.style.display = 'none';

      // תנאי שימוש חובה
      if (termsEl && !termsEl.checked) {
        termsEl.style.outline = '2px solid #EF4444';
        if (errEl) { errEl.textContent = 'יש לאשר את תנאי השימוש להמשך'; errEl.style.display = 'block'; }
        setTimeout(function(){ termsEl.style.outline = ''; }, 3000);
        return;
      }

      var usingCode = code.length > 0;
      var ok = true;

      if (!usingCode) {
        if (name.length < 2) { if (nameEl) nameEl.classList.add('auth-err'); ok = false; }
        if (!isValidPhone(phone)) { if (phoneEl) phoneEl.classList.add('auth-err'); ok = false; }
      }
      if (!ok) return;

      var btn = document.getElementById('authBtn');
      var btnTxt = document.getElementById('authBtnTxt');
      var spin = document.getElementById('authSpin');
      if (btnTxt) btnTxt.style.display = 'none';
      if (spin) spin.style.display = 'block';
      if (btn) btn.disabled = true;

      function onFail() {
        if (btnTxt) btnTxt.style.display = '';
        if (spin) spin.style.display = 'none';
        if (btn) btn.disabled = false;
        if (errEl) errEl.style.display = 'block';
      }

      if (usingCode) {
        // כניסה דרך קוד ארגוני
        hahizdCodeLookup(code)
          .then(function (d) {
            if (d && d.found) {
              grantAuthAccess(d.orgName || code, code);
            } else {
              onFail();
            }
          })
          .catch(onFail);
      } else {
        // כניסה דרך שם + טלפון — בודק approved
        hahizdLookup(name, phone)
          .then(function (d) {
            if (d && d.found && d.approved) {
              grantAuthAccess(name, phone);
            } else {
              onFail();
            }
          })
          .catch(onFail);
      }
    };

    window.doAuthReg = function () {
      var nameEl = document.getElementById('regName');
      var phoneEl = document.getElementById('regPhone');
      var notesEl = document.getElementById('regNotes');
      var errEl = document.getElementById('regErr');
      var name = nameEl ? nameEl.value.trim() : '';
      var phone = phoneEl ? phoneEl.value.trim() : '';
      var notes = notesEl ? notesEl.value.trim().slice(0, 500) : '';
      if (nameEl) nameEl.classList.remove('auth-err');
      if (phoneEl) phoneEl.classList.remove('auth-err');
      if (errEl) errEl.style.display = 'none';
      var ok = true;
      if (name.length < 2) {
        if (nameEl) nameEl.classList.add('auth-err');
        ok = false;
      }
      if (!isValidPhone(phone)) {
        if (phoneEl) phoneEl.classList.add('auth-err');
        ok = false;
      }
      if (!ok) {
        if (errEl) errEl.style.display = 'block';
        return;
      }

      var btn = document.getElementById('regBtn');
      var btnTxt = document.getElementById('regBtnTxt');
      var spin = document.getElementById('regSpin');
      if (btnTxt) btnTxt.style.display = 'none';
      if (spin) spin.style.display = 'block';
      if (btn) btn.disabled = true;

      hahizdSubmit({
        name: name,
        phone: phone,
        notes: notes,
        timestamp: new Date().toLocaleString('he-IL'),
        form_type: 'lead',
        _hp: honeypotValue(document.querySelector('#authViewReg [name="_hp"]')),
      })
        .then(function () {
          showAuthView('Success');
          setSession(name, phone);
          savePhoneUX(phone);
          document.body.style.overflow = '';
          setTimeout(function () {
            grantAuthAccess(name, phone);
          }, 2000);
        })
        .catch(function () {
          if (btnTxt) btnTxt.style.display = '';
          if (spin) spin.style.display = 'none';
          if (btn) btn.disabled = false;
          if (errEl) {
            errEl.textContent = 'שגיאה בשליחה, נסה שוב';
            errEl.style.display = 'block';
          }
        });
    };

    var session = getSession();
    if (session) {
      var age = Date.now() - session.ts;
      if (age < SESSION_REVERIFY_MS) {
        // Session fresh — grant immediately, no GAS round-trip
        grantAuthAccess(session.name, session.phone);
      } else {
        // Session older than 24h — re-verify once against GAS
        // Org-code sessions store phone=code (non-numeric) — re-verify via code_lookup
        showAuthVerifying(true);
        var isOrgSession = !isValidPhone(session.phone);
        var verifyPromise = isOrgSession
          ? hahizdCodeLookup(session.phone)
          : hahizdLookup(session.name, session.phone);
        verifyPromise
          .then(function (d) {
            if (d && d.found) {
              grantAuthAccess(session.name, session.phone);
            } else {
              clearSession();
              showAuthVerifying(false);
              showAuthView('Login');
            }
          })
          .catch(function () {
            // On network error, trust the existing session
            grantAuthAccess(session.name, session.phone);
          });
      }
    } else {
      overlay.style.display = 'flex';
      showAuthView('Login');
    }
  }

  function initRegModal(options) {
    options = options || {};
    var formId = options.formId || 'rmForm';
    var successId = options.successId || 'rmSuccess';
    var modalId = options.modalId || 'regModal';

    window.openRegModal = function () {
      document.getElementById(modalId).classList.add('open');
      document.body.style.overflow = 'hidden';
      var f = document.getElementById('rmName');
      if (f) f.focus();
    };
    window.closeRegModal = function () {
      document.getElementById(modalId).classList.remove('open');
      document.body.style.overflow = '';
    };

    var modal = document.getElementById(modalId);
    if (modal) {
      modal.addEventListener('click', function (e) {
        if (e.target === modal) window.closeRegModal();
      });
    }

    ['rmName', 'rmPhone'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') window.submitRegModal();
        });
      }
    });

    window.submitRegModal = function () {
      var nameEl = document.getElementById('rmName');
      var phoneEl = document.getElementById('rmPhone');
      var notesEl = document.getElementById('rmNotes');
      var termsEl = document.getElementById('rmTerms');
      var name = nameEl ? nameEl.value.trim() : '';
      var phone = phoneEl ? phoneEl.value.trim() : '';
      var notes = notesEl ? notesEl.value.trim().slice(0, 500) : '';
      if (nameEl) nameEl.classList.remove('reg-err');
      if (phoneEl) phoneEl.classList.remove('reg-err');
      var ok = true;
      if (name.length < 2) {
        if (nameEl) nameEl.classList.add('reg-err');
        ok = false;
      }
      if (!isValidPhone(phone)) {
        if (phoneEl) phoneEl.classList.add('reg-err');
        ok = false;
      }
      if (termsEl && !termsEl.checked) {
        termsEl.style.outline = '2px solid #EF4444';
        setTimeout(function(){ termsEl.style.outline = ''; }, 2000);
        ok = false;
      }
      if (!ok) return;

      var btn = document.getElementById('rmBtn') || document.querySelector('#' + modalId + ' .reg-btn');
      var btnTxt = document.getElementById('rmBtnTxt');
      var spin = document.getElementById('rmSpin');
      if (btn) btn.disabled = true;
      if (btnTxt) btnTxt.style.display = 'none';
      if (spin) spin.style.display = 'block';
      else if (btn) btn.textContent = 'שולח...';

      var hpEl = document.querySelector('#' + formId + ' [name="_hp"]');
      hahizdSubmit({
        name: name,
        phone: phone,
        notes: notes,
        timestamp: new Date().toLocaleString('he-IL'),
        form_type: options.formType || 'lead',
        _hp: honeypotValue(hpEl),
      })
        .then(function () {
          savePhoneUX(phone);
          var formEl = document.getElementById(formId);
          var successEl = document.getElementById(successId);
          if (formEl) formEl.style.display = 'none';
          if (successEl) {
            successEl.style.display = 'block';
          } else {
            window.closeRegModal();
            alert('תודה! קיבלנו את הפרטים. נחזור אליך בהקדם.');
          }
        })
        .catch(function () {
          if (btnTxt) btnTxt.style.display = '';
          if (spin) spin.style.display = 'none';
          if (btn) {
            btn.disabled = false;
            if (!btnTxt && !spin) btn.textContent = 'שלח ← קבע פגישה';
          }
          alert('שגיאה בשליחה. בדוק חיבור לאינטרנט ונסה שוב.');
        });
    };
  }

  function initContactForm(formId, options) {
    options = options || {};
    formId = formId || 'contactForm';
    var form = document.getElementById(formId);
    if (!form) return;

    var notesEl = document.getElementById(options.notesId || 'fNotes');
    var notesCount = document.getElementById(options.notesCountId || 'notesCount');
    if (notesEl && notesCount) {
      notesEl.addEventListener('input', function () {
        notesCount.textContent = notesEl.value.length;
      });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var nameEl = document.getElementById(options.nameId || 'fName');
      var phoneEl = document.getElementById(options.phoneId || 'fPhone');
      var name = nameEl ? nameEl.value.trim() : '';
      var phone = phoneEl ? phoneEl.value.trim() : '';
      var notes = notesEl ? notesEl.value.trim().slice(0, 500) : '';

      var nameOk = name.length >= 2;
      var phoneOk = isValidPhone(phone);

      if (nameEl) nameEl.classList.toggle('error', !nameOk);
      var errName = document.getElementById(options.errNameId || 'errName');
      if (errName) errName.classList.toggle('show', !nameOk);

      if (phoneEl) phoneEl.classList.toggle('error', !phoneOk);
      var errPhone = document.getElementById(options.errPhoneId || 'errPhone');
      if (errPhone) errPhone.classList.toggle('show', !phoneOk);

      if (!nameOk || !phoneOk) return;

      var btn = document.getElementById(options.btnId || 'cfBtn');
      var btnText = document.getElementById(options.btnTextId || 'cfBtnText');
      var spinner = document.getElementById(options.spinnerId || 'cfSpinner');
      if (btn) btn.disabled = true;
      if (btnText) btnText.style.display = 'none';
      if (spinner) spinner.style.display = 'inline-flex';

      var hpEl = form.querySelector('[name="_hp"]');
      hahizdSubmit({
        name: name,
        phone: phone,
        notes: notes,
        timestamp: new Date().toLocaleString('he-IL'),
        form_type: options.formType || 'contact',
        _hp: honeypotValue(hpEl),
      })
        .then(function () {
          var content = document.getElementById(options.contentId || 'cfContent');
          var success = document.getElementById(options.successId || 'cfSuccess');
          if (content) content.style.display = 'none';
          if (success) {
            success.classList.add('show');
          }
        })
        .catch(function () {
          if (btn) btn.disabled = false;
          if (btnText) btnText.style.display = 'inline';
          if (spinner) spinner.style.display = 'none';
          if (errPhone) {
            errPhone.textContent = 'שגיאה בשליחה, נסה שוב';
            errPhone.classList.add('show');
          }
        });
    });
  }

  window.Hahizd = {
    SHEETS_URL: HAHIZD_SHEETS_URL,
    CALENDLY_URL: CALENDLY_URL,
    submit: hahizdSubmit,
    lookup: hahizdLookup,
    codeLookup: hahizdCodeLookup,
    visit: hahizdVisit,
    honeypotValue: honeypotValue,
    initNav: initNav,
    initProtectedAuth: initProtectedAuth,
    initRegModal: initRegModal,
    initContactForm: initContactForm,
    normalizePhone: normalizePhone,
    getSession: getSession,
    clearSession: clearSession,
  };
})();
