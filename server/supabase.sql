-- Blipville accounts: paste all of this into Supabase → SQL Editor → New query → Run.
-- Players sign up with a username + password (no email is collected). Row Level Security makes sure
-- everyone can only read and change their own save and friends; usernames and Arena teams are public.

create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  username text unique not null check (username ~ '^[A-Za-z0-9_]{3,16}$'),
  created_at timestamptz not null default now()
);

create table if not exists public.saves (
  user_id uuid primary key references auth.users on delete cascade,
  data jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.teams (            -- your Arena team, so friends can battle it
  user_id uuid primary key references auth.users on delete cascade,
  username text not null,
  code text not null check (length(code) < 2000),
  wins integer not null default 0 check (wins >= 0),
  updated_at timestamptz not null default now()
);

create table if not exists public.friends (
  user_id uuid not null references auth.users on delete cascade,
  friend_id uuid not null references auth.users on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, friend_id),
  check (user_id <> friend_id)
);

alter table public.profiles enable row level security;
alter table public.saves enable row level security;
alter table public.teams enable row level security;
alter table public.friends enable row level security;

drop policy if exists "profiles are public" on public.profiles;
create policy "profiles are public" on public.profiles for select using (true);
drop policy if exists "make my profile" on public.profiles;
create policy "make my profile" on public.profiles for insert with check (auth.uid() = id);

drop policy if exists "my save" on public.saves;
create policy "my save" on public.saves for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "teams are public" on public.teams;
create policy "teams are public" on public.teams for select using (true);
drop policy if exists "my team" on public.teams;
create policy "my team" on public.teams for insert with check (auth.uid() = user_id);
drop policy if exists "update my team" on public.teams;
create policy "update my team" on public.teams for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "my friends" on public.friends;
create policy "my friends" on public.friends for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
