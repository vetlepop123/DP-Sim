-- Ledertavle for DP-Sim. Kjør dette én gang i Supabase: SQL Editor -> New query -> Run.

create table if not exists public.scores (
  id           bigint generated always as identity primary key,
  created_at   timestamptz not null default now(),
  name         text not null check (char_length(name) between 1 and 20),
  time_s       real not null check (time_s >= 0 and time_s < 36000),
  level        int  not null default 1 check (level between 1 and 10000),
  category     text not null check (char_length(category) <= 100),
  weather      text,
  radius       int,
  speed        real,
  progressive  boolean,
  heading_rule boolean,
  heading_tol  int,
  failures     boolean,
  mode         text
);

create index if not exists scores_category_time_idx on public.scores (category, time_s desc);

-- Alle kan lese og legge til resultater, men ingen kan endre eller slette dem via API-et.
grant select, insert on public.scores to anon;
alter table public.scores enable row level security;

drop policy if exists "Alle kan lese" on public.scores;
create policy "Alle kan lese" on public.scores for select to anon using (true);

drop policy if exists "Alle kan legge til" on public.scores;
create policy "Alle kan legge til" on public.scores for insert to anon with check (true);
