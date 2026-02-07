# Twilio SMS Setup Guide

## 🔧 Environment Variables Required

Add these to your Railway environment variables:

```env
# Twilio SMS Configuration
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Database (auto-set by Railway PostgreSQL plugin)
DATABASE_URL=postgresql://...

# Existing variables (keep these)
FLASK_SECRET_KEY=...
ADMIN_PASSWORD=...
GOOGLE_CREDENTIALS_JSON=...
CALENDAR_ID=...
SENDGRID_API_KEY=...
FROM_EMAIL=...
```

---

## 📱 Getting Twilio Credentials

### Step 1: Create Twilio Account

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for free account
3. Verify your email and phone number

### Step 2: Get Your Credentials

After logging in to Twilio Console:

1. **Dashboard** → You'll see:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click "Show" to reveal)

2. Copy these values:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   ```

### Step 3: Get a Phone Number

#### Option A: Trial Number (Free, Limited)

1. Twilio Console → **Phone Numbers** → **Manage** → **Buy a number**
2. Choose a number (country: United States or Israel)
3. Click "Buy" (free with trial account)
4. Copy the number in format: `+1234567890`

**Trial Limitations:**
- Can only send to verified phone numbers
- Message includes "Sent from your Twilio trial account"
- Limited to 500 SMS per month

#### Option B: Paid Number (Production)

1. Add payment method to Twilio account
2. Buy a phone number ($1-2/month)
3. No limitations on who you can send to
4. No trial message prefix

### Step 4: Verify Israeli Phone Numbers (Trial Only)

If using trial account, you must verify recipient numbers:

1. Twilio Console → **Phone Numbers** → **Manage** → **Verified Caller IDs**
2. Click "Add a new number"
3. Enter phone in format: `+972501234567`
4. You'll receive verification code via SMS
5. Enter code to verify

**Important:** Verify YOUR phone number and any test numbers before deploying!

---

## 🚀 Railway Deployment

### Set Environment Variables

**Method 1: Railway Dashboard**
```
1. Go to your Railway project
2. Click "Variables" tab
3. Add each variable:
   - TWILIO_ENABLED = true
   - TWILIO_ACCOUNT_SID = ACxxxxx...
   - TWILIO_AUTH_TOKEN = your_token
   - TWILIO_PHONE_NUMBER = +1234567890
```

**Method 2: Railway CLI**
```bash
railway variables set TWILIO_ENABLED=true
railway variables set TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxx
railway variables set TWILIO_AUTH_TOKEN=your_token_here
railway variables set TWILIO_PHONE_NUMBER=+1234567890
```

### Deploy

```bash
git add .
git commit -m "Add Twilio SMS notifications

- Replace WhatsApp with Twilio SMS for OTP
- Add SMS booking confirmations
- Add SMS reminders (day before + morning)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

---

## 🧪 Testing

### Test OTP Flow

1. Visit your site
2. Try to book appointment → Identity overlay appears
3. Enter phone → Click "שלח קוד אימות"
4. Check SMS on your phone
5. Enter OTP code → Should verify successfully

**If SMS doesn't arrive:**
- Check Railway logs: `railway logs | grep Twilio`
- If trial account: Verify the phone number in Twilio Console
- Check phone format: Must be +972XXXXXXXXX for Israel

### Test in Mock Mode (Development)

Set `TWILIO_ENABLED=false` in `.env`:

```env
TWILIO_ENABLED=false
```

Run app:
```bash
python app.py
```

OTP codes will print to console:
```
[Twilio][OTP] MOCK MODE - Code for 0501234567: 123456
```

---

## 📊 SMS Message Examples

### OTP Message
```
קוד האימות שלך ב-LISHAI SIMANI: 123456
תוקף: 5 דקות.
```

### Booking Confirmation
```
שלום Sara!

התור שלך אושר בהצלחה ב-LISHAI SIMANI Beauty Studio

📅 תאריך: 15/02/2026
🕐 שעה: 14:00
💅 שירות: לק ג'ל

📍 כתובת: משעול הרקפת 3, קרני שומרון
📞 טלפון: 051-5656295

לביטול תור, התקשרי אלינו.

תודה שבחרת בנו! 💖
```

### Day Before Reminder
```
שלום Sara!

תזכורת: מחר יש לך תור ב-LISHAI SIMANI Beauty Studio

📅 15/02/2026 בשעה 14:00
💅 לק ג'ל

📍 משעול הרקפת 3, קרני שומרון

מצפים לראותך! 💖

לביטול - התקשרי ל-051-5656295
```

### Morning Reminder
```
בוקר טוב Sara!

תזכורת: היום יש לך תור ב-LISHAI SIMANI Beauty Studio

🕐 בשעה 14:00
💅 לק ג'ל

📍 משעול הרקפת 3, קרני שומרון

נתראה בקרוב! 💖
```

---

## 💰 Pricing (as of 2026)

### Twilio SMS Costs

| Item | Cost |
|------|------|
| Phone Number | $1-2/month |
| SMS (Outbound - US) | $0.0075/message |
| SMS (Outbound - Israel) | $0.12/message |

### Estimated Monthly Cost

Assuming 100 bookings/month:
- 100 OTP messages × $0.12 = $12
- 100 confirmations × $0.12 = $12
- 200 reminders × $0.12 = $24
- Phone number = $2

**Total: ~$50/month**

**Trial account includes:**
- $15.50 credit (free)
- Approximately 129 messages to Israel

---

## 🔒 Security Best Practices

### DO:
✅ Store credentials in Railway environment variables
✅ Use `TWILIO_ENABLED=false` for local development
✅ Keep Auth Token secret (never commit to Git)
✅ Rotate Auth Token periodically
✅ Use separate Twilio accounts for dev/prod

### DON'T:
❌ Hardcode credentials in source code
❌ Commit `.env` file to Git
❌ Share Auth Token in chat/email
❌ Use same credentials for multiple projects
❌ Enable Twilio in production without testing first

---

## 🐛 Troubleshooting

### SMS Not Sending

**Symptom:** OTP not received, no error in logs

**Check:**
1. Railway logs: `railway logs | grep Twilio`
2. Twilio Console → **Monitor** → **Logs** → **Errors**
3. Phone number format: Must be +972XXXXXXXXX
4. Trial account: Phone must be verified

### Error: "Unable to create record"

**Cause:** Invalid phone number format

**Fix:** Ensure phone is in format `+972501234567` (no spaces, dashes)

### Error: "Authenticate"

**Cause:** Wrong Account SID or Auth Token

**Fix:**
1. Verify credentials in Twilio Console
2. Copy-paste carefully (no extra spaces)
3. Redeploy Railway app after updating variables

### Trial Account Limitations

**Symptom:** Can't send to customer phones

**Fix:**
1. Verify each customer's phone in Twilio Console
2. **OR** Upgrade to paid account ($20 minimum)

### Messages Delayed

**Cause:** High volume or carrier delays

**Fix:**
- Twilio queues messages automatically
- Check Twilio Console → Monitor → Logs for delivery status
- Israeli carriers may have 1-2 minute delays

---

## 📈 Monitoring

### Check SMS Delivery

**Twilio Console:**
1. Monitor → Logs → Messages
2. See delivery status for each SMS
3. Track costs in real-time

**Railway Logs:**
```bash
railway logs | grep Twilio
```

Look for:
```
[Twilio][OTP] SMS sent successfully. SID: SMxxxxxxxxx
[Twilio][SMS] Sent successfully. SID: SMxxxxxxxxx
```

### Set Up Alerts

**Twilio Console:**
1. Monitor → Alerts
2. Create alert for:
   - Failed messages
   - Low balance
   - High usage

---

## 🔄 Switching from WhatsApp to Twilio

If you previously used WhatsApp OTP:

### Changes Made:
1. ✅ `whatsapp_otp_db.py` → `twilio_otp.py` created
2. ✅ `whatsapp_service.py` → `twilio_sms_service.py` created
3. ✅ `app.py` imports updated
4. ✅ `requirements.txt` updated with `twilio` library

### Environment Variables:
- ❌ Remove: `WHATSAPP_ENABLED`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- ✅ Add: `TWILIO_ENABLED`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### No Database Changes Needed
All database tables remain the same. The switch is transparent.

---

## 🆘 Support Resources

- **Twilio Docs:** [twilio.com/docs](https://www.twilio.com/docs)
- **SMS Quickstart:** [twilio.com/docs/sms/quickstart/python](https://www.twilio.com/docs/sms/quickstart/python)
- **Twilio Support:** support@twilio.com
- **Community Forum:** [support.twilio.com](https://support.twilio.com)

---

**Last Updated:** 2026-02-05
