-- SentinelAI Supabase schema
-- Target project: https://yevnlrajklfkqjhcrdps.supabase.co
--
-- This file creates the app-owned schema on top of Supabase Auth:
-- - auth.users remains the source of truth for identity/password/session handling
-- - public.users stores SentinelAI profile/trust data
-- - public.events stores forensic activity logs
-- - public.alerts stores security alerts
--
-- Apply this in Supabase SQL Editor or via Supabase CLI.

create extension if not exists pgcrypto;
create extension if not exists citext;

create schema if not exists app_private;

create table if not exists public.users (
    id uuid primary key references auth.users (id) on delete cascade,
    email citext not null unique,
    trust_score integer not null default 100 check (trust_score >= 0 and trust_score <= 100),
    status text not null default 'active' check (status in ('active', 'quarantined', 'blocked')),
    registered_at timestamptz not null default now(),
    last_login_at timestamptz,
    last_ip text,
    is_admin boolean not null default false,
    typing_variance_ms double precision,
    time_to_complete_sec double precision,
    mouse_move_count integer,
    keypress_count integer,
    ml_anomaly_score double precision,
    triggered_flags jsonb not null default '[]'::jsonb,
    updated_at timestamptz not null default now()
);

create table if not exists public.events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    action text not null,
    ip_address text,
    country text,
    user_agent text,
    trust_score_at_time integer,
    created_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.alerts (
    id uuid primary key default gen_random_uuid(),
    type text not null,
    severity text not null check (severity in ('low', 'medium', 'high', 'critical')),
    description text,
    affected_user_ids jsonb not null default '[]'::jsonb,
    resolved boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists users_status_idx on public.users (status);
create index if not exists users_trust_score_idx on public.users (trust_score);
create index if not exists users_is_admin_idx on public.users (is_admin);
create index if not exists events_user_id_created_at_idx on public.events (user_id, created_at desc);
create index if not exists events_action_created_at_idx on public.events (action, created_at desc);
create index if not exists alerts_severity_created_at_idx on public.alerts (severity, created_at desc);
create index if not exists alerts_resolved_created_at_idx on public.alerts (resolved, created_at desc);

create or replace function app_private.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public, auth, app_private
as $$
begin
    insert into public.users (id, email)
    values (new.id, new.email)
    on conflict (id) do nothing;
    return new;
end;
$$;

create or replace function app_private.is_admin_user()
returns boolean
language sql
security definer
set search_path = public, auth, app_private
as $$
    select exists (
        select 1
        from public.users
        where id = auth.uid()
          and is_admin = true
    );
$$;

-- Keep the profile row in sync with Supabase Auth signups.
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function app_private.handle_new_auth_user();

alter table public.users enable row level security;
alter table public.events enable row level security;
alter table public.alerts enable row level security;

-- Users: own profile or admin profile access.
drop policy if exists "users can read own profile" on public.users;
create policy "users can read own profile"
on public.users
for select
using (auth.uid() = id);

drop policy if exists "admins can read all profiles" on public.users;
create policy "admins can read all profiles"
on public.users
for select
using (app_private.is_admin_user());

-- Events: admin-only reads. Writes happen through the service role.
drop policy if exists "admins can read events" on public.events;
create policy "admins can read events"
on public.events
for select
using (app_private.is_admin_user());

-- Alerts: admin-only reads. Writes happen through the service role.
drop policy if exists "admins can read alerts" on public.alerts;
create policy "admins can read alerts"
on public.alerts
for select
using (app_private.is_admin_user());

grant usage on schema public to authenticated;
grant usage on schema app_private to authenticated;
grant select on public.users to authenticated;
grant select on public.events to authenticated;
grant select on public.alerts to authenticated;

-- No public insert/update/delete grants are required.
-- The backend service role can write all tables directly and bypass RLS.
