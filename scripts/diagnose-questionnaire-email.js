#!/usr/bin/env node
/** בדיקה: האם GAS בפרודקשן שולח מייל שאלון אחרי Calendly */
const GAS =
  'https://script.google.com/macros/s/AKfycbx9oEJH0wO9wezg43EvBsX4unRFd8ELDRvcjL7alaXdyJpeA3pw1VirZUuw4VAMsKD39Q/exec';

async function get(params) {
  const r = await fetch(GAS + '?' + new URLSearchParams(params));
  const text = await r.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch (_) {}
  return { status: r.status, text, json };
}

async function postWebhook() {
  const r = await fetch(GAS, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event: 'invitee.created',
      payload: {
        invitee: { name: 'Diag Test', email: 'diag-test@example.com' },
        scheduled_event: { start_time: new Date().toISOString() },
      },
    }),
  });
  const text = await r.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch (_) {}
  return { status: r.status, text: text.slice(0, 200), json, isHtml: text.includes('<!DOCTYPE') };
}

(async () => {
  const calendly = await get({
    form_type: 'calendly_booking',
    name: 'Diag',
    email: 'diag@example.com',
  });
  const webhook = await postWebhook();

  const deployedNew =
    calendly.json &&
    (calendly.json.emailed !== undefined || calendly.json.questionnaire_url);

  console.log(JSON.stringify({ calendly_get: calendly, webhook_post: webhook, deployedNew }, null, 2));

  if (!deployedNew) {
    console.error('\nFAIL: GAS בפרודקשן לא מעודכן — אין MailApp / calendly_booking');
    console.error('גילעד חייב: להדביק Code.gs → Deploy → New version');
    process.exit(1);
  }
  if (webhook.isHtml) {
    console.error('\nWARN: Webhook POST נכשל — Calendly לא יכול לשלוח מיילים');
    process.exit(1);
  }
  console.log('\nOK: GAS מוכן לשליחת מייל שאלון');
})();
