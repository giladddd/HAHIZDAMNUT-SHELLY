/**
 * גילעד — להדביק ב-Apps Script ולפרסם (Deploy → New version).
 * אחרי קביעת פגישה ב-Calendly: מייל עם קישור לשאלון pre-meeting.html
 *
 * חובה: Calendly → Integrations → Webhooks → invitee.created → URL של Web App
 * (בלי webhook — המייל עם השאלון לא יישלח אחרי קביעת פגישה)
 */
var SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE';
var SHEET_NAME = 'שאלונים';
var QUESTIONNAIRE_URL = 'https://hahizdamnut-shelly.com/pre-meeting.html';

function doGet(e) {
  return handleRequest(e);
}

function doPost(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    var calendly = parseCalendlyWebhook_(e);
    if (calendly) {
      return jsonResponse_(handleCalendlyBooking_(calendly));
    }

    var params = parseParams_(e);
    var action = (params.action || '').toLowerCase();

    if (action === 'lookup') {
      return jsonResponse_(lookupLead_(params.name, params.phone));
    }

    if (action === 'visit') {
      return jsonResponse_(recordVisit_(params.phone));
    }

    if (params.form_type === 'calendly_booking') {
      return jsonResponse_(
        handleCalendlyBooking_({
          name: params.name,
          email: params.email,
          eventTime: params.event_time || '',
        })
      );
    }

    return jsonResponse_(appendLead_(params));
  } catch (err) {
    return jsonResponse_({ ok: false, status: 'error', error: String(err) });
  }
}

function parseCalendlyWebhook_(e) {
  if (!e || !e.postData || !e.postData.contents) return null;
  var ct = (e.postData.type || '').toLowerCase();
  if (ct.indexOf('application/json') === -1) return null;
  try {
    var json = JSON.parse(e.postData.contents);
    if (json.event !== 'invitee.created') return null;
    var payload = json.payload || {};
    var invitee = payload.invitee || payload;
    var email = String(invitee.email || '').trim();
    var name = String(invitee.name || '').trim();
    if (!email) return null;

    var eventTime = '';
    var scheduled = payload.scheduled_event || {};
    if (scheduled.start_time) {
      try {
        eventTime = Utilities.formatDate(
          new Date(scheduled.start_time),
          'Asia/Jerusalem',
          'dd/MM/yyyy HH:mm'
        );
      } catch (ignore) {
        eventTime = String(scheduled.start_time);
      }
    }

    return { name: name, email: email, eventTime: eventTime };
  } catch (ignore) {
    return null;
  }
}

function parseParams_(e) {
  var params = {};
  if (e && e.parameter) {
    Object.keys(e.parameter).forEach(function (k) {
      params[k] = e.parameter[k];
    });
  }
  if (e && e.postData && e.postData.contents) {
    var body = e.postData.contents;
    var ct = (e.postData.type || '').toLowerCase();
    if (ct.indexOf('application/x-www-form-urlencoded') !== -1) {
      body.split('&').forEach(function (pair) {
        var idx = pair.indexOf('=');
        if (idx === -1) return;
        var key = decodeURIComponent(pair.substring(0, idx).replace(/\+/g, ' '));
        var val = decodeURIComponent(pair.substring(idx + 1).replace(/\+/g, ' '));
        params[key] = val;
      });
    } else if (ct.indexOf('application/json') !== -1) {
      try {
        var json = JSON.parse(body);
        Object.keys(json).forEach(function (k) {
          params[k] = json[k];
        });
      } catch (ignore) {}
    }
  }
  return params;
}

function getSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow([
      'timestamp',
      'name',
      'phone',
      'notes',
      'email',
      'form_type',
      'source',
      'expect',
      'career_score',
      'finance_score',
      'personal_score',
      'last_visit',
    ]);
  }
  return sheet;
}

function normalizePhone_(phone) {
  return String(phone || '')
    .replace(/[\s\-()]/g, '')
    .replace(/\D/g, '')
    .replace(/^0+/, '');
}

function lookupLead_(name, phone) {
  var norm = normalizePhone_(phone);
  var sheet = getSheet_();
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return { found: false };

  var targetName = String(name || '').trim().toLowerCase();
  for (var i = 1; i < data.length; i++) {
    var rowName = String(data[i][1] || '').trim().toLowerCase();
    var rowPhone = normalizePhone_(data[i][2]);
    if (rowPhone === norm && rowName === targetName) {
      return { found: true };
    }
  }
  return { found: false };
}

function recordVisit_(phone) {
  var norm = normalizePhone_(phone);
  var sheet = getSheet_();
  var data = sheet.getDataRange().getValues();
  var now = new Date().toLocaleString('he-IL');
  var lastCol = data[0] ? data[0].length : 12;

  for (var i = 1; i < data.length; i++) {
    if (normalizePhone_(data[i][2]) === norm) {
      sheet.getRange(i + 1, lastCol).setValue(now);
      return { ok: true, updated: true };
    }
  }
  return { ok: true, updated: false };
}

function buildQuestionnaireUrl_(name, email) {
  var parts = [];
  if (name) parts.push('name=' + encodeURIComponent(String(name).trim()));
  if (email) parts.push('email=' + encodeURIComponent(String(email).trim()));
  return parts.length ? QUESTIONNAIRE_URL + '?' + parts.join('&') : QUESTIONNAIRE_URL;
}

function buildQuestionnaireEmailHtml_(name, questionnaireUrl, eventTime) {
  name = String(name || '').trim() || 'חבר/ה';
  var meetingLine = eventTime
    ? '<p style="margin:0 0 16px;font-size:15px;color:#334155;line-height:1.7;">📅 <strong>מועד הפגישה:</strong> ' +
      eventTime +
      '</p>'
    : '';

  return (
    '<div dir="rtl" style="font-family:Arial,Heebo,sans-serif;background:#F2F7FD;padding:24px;">' +
    '<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;padding:28px 24px;box-shadow:0 4px 24px rgba(0,0,0,.08);">' +
    '<p style="margin:0 0 8px;font-size:13px;font-weight:700;color:#1A56A0;">📋 לפני הפגישה</p>' +
    '<h1 style="margin:0 0 12px;font-size:24px;color:#0F172A;">שאלון הכנה למפגש</h1>' +
    '<p style="margin:0 0 18px;font-size:15px;color:#64748B;line-height:1.7;">היי ' +
    name +
    ', תודה שקבעת פגישה עם גלעד!<br/>לפני שניפגש — מלא/י את השאלון הקצר. זה יעזור לנו להתאים את הפגישה בדיוק אליך.</p>' +
    meetingLine +
    '<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px 18px;margin:0 0 22px;">' +
    '<p style="margin:0 0 10px;font-size:14px;font-weight:700;color:#0F172A;">בשאלון תענה/י על:</p>' +
    '<ul style="margin:0;padding-right:20px;color:#334155;font-size:14px;line-height:1.8;">' +
    '<li>איך הגעת אלינו ומה תפס אותך</li>' +
    '<li>מה היית רוצה לקבל מהפגישה</li>' +
    '<li>מסלול תעסוקתי, תוכנית כלכלית וניהול עצמי (1–10)</li>' +
    '</ul></div>' +
    '<p style="text-align:center;margin:0 0 22px;">' +
    '<a href="' +
    questionnaireUrl +
    '" style="display:inline-block;background:#1A56A0;color:#fff;text-decoration:none;font-weight:700;font-size:16px;padding:14px 28px;border-radius:50px;">מלא שאלון הכנה ←</a>' +
    '</p>' +
    '<p style="margin:0;font-size:13px;color:#64748B;line-height:1.7;text-align:center;">אם הכפתור לא עובד, העתק/י את הקישור:<br/>' +
    '<a href="' +
    questionnaireUrl +
    '" style="color:#1A56A0;word-break:break-all;">' +
    questionnaireUrl +
    '</a></p>' +
    '<p style="margin:24px 0 0;font-size:13px;color:#94A3B8;text-align:center;">גלעד — ההזדמנות שלי</p>' +
    '</div></div>'
  );
}

function buildQuestionnaireEmailText_(name, questionnaireUrl, eventTime) {
  name = String(name || '').trim() || 'חבר/ה';
  var lines = [
    'היי ' + name + ',',
    '',
    'תודה שקבעת פגישה עם גלעד!',
    'לפני שניפגש — מלא/י את שאלון ההכנה (כמה דקות):',
    '',
  ];
  if (eventTime) lines.push('מועד הפגישה: ' + eventTime, '');
  lines.push(
    questionnaireUrl,
    '',
    'בשאלון: איך הגעת אלינו, מה תרצה מהפגישה, ושאלות קצרות על תעסוקה/כלכלה/ניהול עצמי.',
    '',
    'נתראה בקרוב!',
    'גלעד — ההזדמנות שלי'
  );
  return lines.join('\n');
}

function sendQuestionnaireEmail_(name, email, eventTime) {
  email = String(email || '').trim();
  if (!email || email.indexOf('@') === -1) return false;

  var questionnaireUrl = buildQuestionnaireUrl_(name, email);
  var subject = 'שאלון הכנה לפגישה — ההזדמנות שלי';
  var htmlBody = buildQuestionnaireEmailHtml_(name, questionnaireUrl, eventTime);
  var body = buildQuestionnaireEmailText_(name, questionnaireUrl, eventTime);

  MailApp.sendEmail({
    to: email,
    subject: subject,
    body: body,
    htmlBody: htmlBody,
  });
  return true;
}

function handleCalendlyBooking_(data) {
  data = data || {};
  var name = data.name || '';
  var email = data.email || '';
  var eventTime = data.eventTime || '';

  var emailed = false;
  try {
    emailed = sendQuestionnaireEmail_(name, email, eventTime);
  } catch (err) {
    Logger.log('sendQuestionnaireEmail failed: ' + err);
  }

  var sheet = getSheet_();
  sheet.appendRow([
    new Date().toLocaleString('he-IL'),
    name || '',
    '',
    eventTime ? 'calendly: ' + eventTime : 'calendly booking',
    email || '',
    'calendly_booking',
    'calendly',
    '',
    '',
    '',
    '',
    '',
  ]);

  return { ok: true, status: 'ok', emailed: emailed, questionnaire_url: buildQuestionnaireUrl_(name, email) };
}

function appendLead_(params) {
  if (params._hp) {
    return { ok: true, status: 'ok', skipped: 'honeypot' };
  }

  var sheet = getSheet_();
  sheet.appendRow([
    params.timestamp || new Date().toLocaleString('he-IL'),
    params.name || '',
    params.phone || '',
    params.notes || '',
    params.email || '',
    params.form_type || 'lead',
    params.source || '',
    params.expect || '',
    params.career_score || '',
    params.finance_score || '',
    params.personal_score || '',
    '',
  ]);

  return { ok: true, status: 'ok' };
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
