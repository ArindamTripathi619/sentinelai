# Deployment Checklist — SentinelAI Supabase Migration

## Phase 1: Apply Supabase Schema

### Option A: Via Supabase Web UI (Recommended if CLI install fails)
1. Go to https://app.supabase.com and log in
2. Select your project (URL will have project-ref, e.g., `yevnlrajklfkqjhcrdps`)
3. Open **SQL Editor** → click **New query**
4. Copy the contents of `supabase/schema.sql` and paste into the editor
5. Click **Run** and wait for completion
6. Check for errors in the results panel
7. Verify tables appear in **Database** → **Table editor**: `users`, `events`, `alerts`

### Option B: Via Supabase CLI (if installed)
```bash
cd /home/DevCrewX/Projects/sentinelai
supabase login
supabase link --project-ref <project-ref>  # Find in Supabase dashboard URL
supabase db push
```

---

## Phase 2: Set Environment Variables in Vercel

You need to collect the following values from your Supabase project:
- **VITE_SUPABASE_URL** — Project URL from Supabase dashboard (Settings → API → Project URL)
- **VITE_SUPABASE_ANON_KEY** — Anon key from Settings → API → Project API keys (copy "anon public" key)
- **SUPABASE_URL** — Same as VITE_SUPABASE_URL
- **SUPABASE_SERVICE_ROLE_KEY** — Service role key from Settings → API → Project API keys ⚠️ **KEEP SECRET**
- **DATABASE_URL** — Connection string from Settings → Database → Connection pooling or direct (Postgres connection string)

### Set via Vercel CLI

```bash
cd /home/DevCrewX/Projects/sentinelai

# For production environment
vercel env add VITE_SUPABASE_URL production
# (paste your Supabase URL)

vercel env add VITE_SUPABASE_ANON_KEY production
# (paste your anon key)

vercel env add SUPABASE_URL production
# (paste your Supabase URL)

vercel env add SUPABASE_SERVICE_ROLE_KEY production
# (paste your service role key) ⚠️ SECRET

vercel env add DATABASE_URL production
# (paste your Postgres connection string) ⚠️ SECRET
```

### Or set via Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Select the **sentinelai** project
3. Go to **Settings** → **Environment Variables**
4. Add each variable above (repeat for **Production** and **Preview/Development** if needed)

---

## Phase 3: Redeploy to Vercel

After setting environment variables:

```bash
# Option 1: Deploy via CLI (from project root)
vercel --prod

# Option 2: Push to GitHub, and Vercel will auto-deploy
git add .
git commit -m "chore: prepare for Supabase migration deployment"
git push origin main  # (or your main branch)
```

---

## Phase 4: Verify Deployment

After deployment completes:

1. **Check frontend loads**: Visit your Vercel project URL in the browser
2. **Test signup**: Create a new account; watch for Supabase auth success
3. **Check backend /sync**: Frontend should POST behavioral payload to `/sync` after signup
4. **Verify database**: Log into Supabase dashboard and check:
   - `public.users` table has a new row for your signup
   - `public.events` table has events logged
   - `public.alerts` table shows any alerts created (if trust score is low)
5. **Dashboard access**: After login, check if dashboard loads and shows alerts/events

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Schema already exists" error | Use `IF NOT EXISTS` in SQL statements or drop existing tables first |
| "Permission denied" on schema creation | Ensure you're using the correct Supabase user role (Admin or service role) |
| Frontend shows auth error | Check that `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set in Vercel env |
| Backend `/sync` fails | Check that `SUPABASE_SERVICE_ROLE_KEY` and `DATABASE_URL` are set on backend |
| Trust score not persisting | Verify `DATABASE_URL` points to the correct Postgres database |
| Frontend can't reach backend | Check CORS policy in backend and ensure backend is deployed |

---

## Files Ready for Deployment

- ✅ `supabase/schema.sql` — Schema ready to apply
- ✅ `supabase/migrations/20260502_init_schema.sql` — Migration file ready for CLI push
- ✅ `backend/` — Updated with Postgres/Supabase support
- ✅ `frontend/` — Updated with Supabase Auth integration

---

## Next Steps

1. **Choose deployment method**: Web UI (simplest) or CLI (if CLI installs)
2. **Apply schema** to your Supabase project
3. **Collect environment values** from Supabase dashboard
4. **Set Vercel env vars** (CLI or dashboard)
5. **Redeploy** to Vercel
6. **Test end-to-end** (signup → backend /sync → dashboard)

**Estimated time**: 15–30 minutes depending on method choice.
