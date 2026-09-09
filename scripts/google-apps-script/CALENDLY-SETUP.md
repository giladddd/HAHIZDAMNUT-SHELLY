# הגדרת Calendly + מייל שאלון

## למה המייל לא מגיע (בדקנו בפועל)

ה-GAS החי מחזיר רק `{"status":"ok"}` — **בלי** `emailed: true`.
כלומר: הקוד ששולח מייל (`MailApp`) **לא פרוס** ב-Google Apps Script.

## שלב 1 — Deploy של Code.gs (חובה למייל)

1. [script.google.com](https://script.google.com) → הפרויקט של גילעד
2. הדבק את `Code.gs` (מהריפו)
3. החלף `YOUR_SPREADSHEET_ID_HERE` ב-ID האמיתי של הגיליון
4. **Deploy → New deployment → Web app**
   - Execute as: Me
   - Who has access: **Anyone**
5. וודא שה-URL תואם ל-`hahizd-common.js`

**בדיקה:** הרץ מהמחשב:
```bash
node scripts/diagnose-questionnaire-email.js
```
אם עדיין FAIL — ה-deploy לא הצליח.

## שלב 2 — Redirect אחרי קביעה (פתרון מיידי בלי מייל)

Calendly → Event type (30min) → **Confirmation page** →
**Redirect to an external site**:

```
https://hahizdamnut-shelly.com/booking-confirmed.html
```

אחרי כל קביעה — הלקוח רואה כפתור לשאלון מיד.

(אפשר גם ישירות: `https://hahizdamnut-shelly.com/pre-meeting.html`)

## שלב 3 — Webhook למייל (חובה אם רוצים מייל אוטומטי)

Calendly → **Integrations → Webhooks** → Create webhook

| שדה | ערך |
|-----|-----|
| URL | אותו URL של Web App (exec) |
| Events | `invitee.created` |

## שלב 4 — גיבוי במייל Calendly (⭐ הכי מהיר אם כבר מגיע מייל מ-Calendly)

**זו הסיבה הנפוצה:** מגיע מייל אישור מ-Calendly, אבל **בלי** קישור לשאלון — כי התבנית לא עודכנה.

Calendly → **Event types** → **30min** → **Notifications** (או **Workflows**)

ערוך **Confirmation email** / **Email confirmation to invitee** והוסף:

```
📋 לפני הפגישה — מלא שאלון הכנה (2–3 דקות):
https://hahizdamnut-shelly.com/pre-meeting.html
```

טקסט מלא מוכן: `calendly-confirmation-email-he.txt`

> אם אין אפשרות לערוך מייל (תוכנית חינמית) — השתמש בשלב 2 (Redirect) במקום.

## איפה הלקוח מקבל את הקישור

| דרך | מתי |
|-----|-----|
| **Redirect** אחרי Calendly | מיד בדפדפן (שלב 2) |
| **מייל GAS** | למייל מ-Calendly (שלב 1+3) |
| **מייל Calendly** | במייל אישור (שלב 4) |
