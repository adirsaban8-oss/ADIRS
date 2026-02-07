# 🚀 Quick Deployment Guide

## Step 1: Add PostgreSQL to Railway

1. Go to your Railway project dashboard
2. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway automatically sets `DATABASE_URL` environment variable

**✅ Done!** No manual database setup needed - migrations run automatically.

---

## Step 2: Verify Environment Variables

Check that these are set in Railway:

### Already Set (don't change):
- `FLASK_SECRET_KEY`
- `ADMIN_PASSWORD`
- `GOOGLE_CREDENTIALS_JSON`
- `CALENDAR_ID`
- `SENDGRID_API_KEY`
- `FROM_EMAIL`

### Auto-Set by Railway:
- `DATABASE_URL` (PostgreSQL plugin sets this)
- `PORT` (Railway sets this)

### Optional (WhatsApp):
- `WHATSAPP_ENABLED=true`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_OTP_TEMPLATE=otp_verification`

---

## Step 3: Deploy Code

```bash
git add .
git commit -m "Add PostgreSQL customer management system

- PostgreSQL database with customers, appointments, otp_codes tables
- Customer registration with phone uniqueness
- WhatsApp OTP authentication (5-min expiry, 3 attempts max)
- Admin customers tab with search
- Personalized home page greeting
- Waze navigation button
- Business rules: one active appointment per customer
- Automatic database migrations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push
```

Railway automatically deploys when you push.

---

## Step 4: Verify Deployment

### Check Logs
```bash
railway logs
```

**Look for:**
```
[Database] Using PostgreSQL database
[Database] Connection pool initialized
[Database] Migrations completed successfully
```

### Test Health Endpoint
```bash
curl https://your-app.railway.app/health
```

**Expected response:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-05T...",
  "email": true,
  "calendar": true,
  "whatsapp": true
}
```

---

## Step 5: Test Features

### 1. Customer Registration
- Visit your site
- Click booking → Identity overlay appears
- Click "חדשה כאן? לחצי להצטרפות"
- Fill: Name, Phone, Email
- Send OTP → Enter code
- ✅ Should save customer and log in

### 2. One Appointment Limit
- Book an appointment (should work)
- Try to book another (should block with message)
- ✅ Business rule enforced

### 3. Admin Panel
- Go to `/admin`
- Login with `ADMIN_PASSWORD`
- Click **"לקוחות"** tab
- ✅ Should see registered customers

### 4. Waze Button
- Complete a booking
- Success modal shows
- ✅ "נווט עם Waze" button appears

### 5. Personalized Greeting
- Log in as customer
- Go to home page
- ✅ "שלום, {Name}! 👋" appears

---

## 🐛 Troubleshooting

### Database Not Working

**Symptom:** Logs show `[Database] WARNING: Failed to initialize database pool`

**Fix:**
1. Verify PostgreSQL plugin is added in Railway
2. Check `DATABASE_URL` is set
3. Restart the app (redeploy)

### OTP Not Sending

**Symptom:** No OTP received via WhatsApp

**If `WHATSAPP_ENABLED=false` (dev mode):**
- ✅ This is expected
- Check Railway logs for: `[WhatsApp][OTP] MOCK MODE - Code for ...`
- OTP printed in logs

**If `WHATSAPP_ENABLED=true`:**
- Verify `WHATSAPP_ACCESS_TOKEN` is set
- Verify `WHATSAPP_PHONE_NUMBER_ID` is set
- Check Meta Business Suite for API errors

### Customers Not Appearing in Admin

**Symptom:** Admin "לקוחות" tab is empty

**Check:**
1. Database is enabled (see logs)
2. At least one customer registered
3. Hard refresh browser (Ctrl+Shift+R)

### Booking Fails

**Symptom:** Error when trying to book

**Check:**
1. User is logged in (identity overlay completed)
2. Date is 1-30 days ahead
3. No existing active appointment
4. Railway logs for specific error

---

## 📊 Monitoring

### Key Metrics to Watch

1. **Database Connections**
   ```bash
   railway logs | grep "Database"
   ```

2. **OTP Success Rate**
   ```bash
   railway logs | grep "OTP"
   ```

3. **Booking Errors**
   ```bash
   railway logs | grep "Booking error"
   ```

4. **Reminder Scheduler**
   ```bash
   railway logs | grep "reminder"
   ```

---

## 🔄 Rollback Plan

If something goes wrong:

### Option 1: Quick Rollback (Railway)
1. Go to Railway dashboard
2. Deployments → Find previous working version
3. Click "Redeploy"

### Option 2: Git Rollback
```bash
git revert HEAD
git push
```

### Option 3: Disable Database Mode
Temporarily remove PostgreSQL plugin in Railway.
App will fall back to Calendar-only mode automatically.

---

## 📞 Support Checklist

Before asking for help, check:

- [ ] Railway logs reviewed
- [ ] Health endpoint returns 200 OK
- [ ] Database `DATABASE_URL` is set
- [ ] Environment variables verified
- [ ] Browser console for frontend errors
- [ ] Tested in incognito mode (no cache)

---

## 🎉 Success Criteria

Your deployment is successful when:

✅ Health endpoint returns OK
✅ Database migrations show "completed successfully" in logs
✅ Customer registration works (test with your phone)
✅ Admin panel shows customers
✅ Booking enforcement works (one appointment limit)
✅ Waze button appears in booking confirmation
✅ Home page shows personalized greeting

---

**Estimated deployment time:** 5-10 minutes

**Questions?** See [DATABASE_SETUP.md](DATABASE_SETUP.md) or [ENV_VARIABLES.md](ENV_VARIABLES.md)
