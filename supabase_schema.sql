-- =====================================================
-- Multivagas — Schema Supabase
-- Execute no SQL Editor do Supabase Dashboard
-- =====================================================

-- ── Extensões ─────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ── Tabela: vagas ──────────────────────────────────
create table if not exists vagas (
  id               text primary key,
  titulo           text,
  empresa          text,
  descricao        text,
  url              text,
  score            integer default 0,
  plataforma       text,
  idioma_vaga      text,
  pcd_detectado    boolean default false,
  curriculo_path   text,
  cover_path       text,
  tags             jsonb default '[]',
  localidade       text,
  salario          text,
  data_publicacao  text,
  status           text default 'nova',
  skills_presentes jsonb default '[]',
  gaps             jsonb default '[]',
  recomendacao     text,
  created_at       timestamptz default now(),
  updated_at       timestamptz default now()
);

-- ── Tabela: candidaturas ───────────────────────────
create table if not exists candidaturas (
  id               text primary key,
  vaga_id          text references vagas(id) on delete set null,
  vaga_titulo      text,
  titulo           text,
  empresa          text,
  url_vaga         text,
  plataforma       text,
  score            integer,
  pcd_detectado    boolean default false,
  idioma_vaga      text,
  tipo_candidatura text default 'email',
  status           text default 'aplicada',
  data_aplicacao   timestamptz,
  data_followup    date,
  curriculo_path   text,
  cover_path       text,
  ats              text,
  keywords         jsonb default '[]',
  email_gerado     jsonb default '{}',
  historico        jsonb default '[]',
  created_at       timestamptz default now(),
  updated_at       timestamptz default now()
);

-- ── Tabela: curriculo (linha única id=1) ───────────
create table if not exists curriculo (
  id         integer primary key default 1,
  dados      jsonb not null default '{}',
  updated_at timestamptz default now()
);

-- ── Tabela: config (linha única id=1) ─────────────
create table if not exists config (
  id                    integer primary key default 1,
  score_minimo          integer default 80,
  cap_por_empresa       integer default 3,
  idioma_preferencial   text default 'pt',
  termos_busca          jsonb default '[]',
  fontes_ativas         jsonb default '{}',
  updated_at            timestamptz default now()
);

-- ── Tabela: vaga_status (status local por vaga) ───
create table if not exists vaga_status (
  vaga_key   text primary key,
  status     text default 'nova',
  updated_at timestamptz default now()
);

-- ── Triggers: updated_at automático ───────────────
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger vagas_updated_at
  before update on vagas
  for each row execute function set_updated_at();

create trigger candidaturas_updated_at
  before update on candidaturas
  for each row execute function set_updated_at();

create trigger curriculo_updated_at
  before update on curriculo
  for each row execute function set_updated_at();

create trigger config_updated_at
  before update on config
  for each row execute function set_updated_at();

create trigger vaga_status_updated_at
  before update on vaga_status
  for each row execute function set_updated_at();

-- ── Row Level Security (RLS) ───────────────────────
-- Habilita RLS em todas as tabelas (necessário para anon key funcionar)
alter table vagas        enable row level security;
alter table candidaturas enable row level security;
alter table curriculo    enable row level security;
alter table config       enable row level security;
alter table vaga_status  enable row level security;

-- Políticas: anon key tem leitura e escrita total (projeto pessoal)
-- Se quiser autenticação futura, troque por políticas baseadas em auth.uid()
create policy "anon_all_vagas"        on vagas        for all using (true) with check (true);
create policy "anon_all_candidaturas" on candidaturas for all using (true) with check (true);
create policy "anon_all_curriculo"    on curriculo    for all using (true) with check (true);
create policy "anon_all_config"       on config       for all using (true) with check (true);
create policy "anon_all_vaga_status"  on vaga_status  for all using (true) with check (true);

-- ── Índices úteis ──────────────────────────────────
create index if not exists idx_vagas_score       on vagas(score desc);
create index if not exists idx_vagas_plataforma  on vagas(plataforma);
create index if not exists idx_vagas_idioma      on vagas(idioma_vaga);
create index if not exists idx_vagas_pcd         on vagas(pcd_detectado);
create index if not exists idx_cand_status       on candidaturas(status);
create index if not exists idx_cand_followup     on candidaturas(data_followup);
create index if not exists idx_cand_vaga_id      on candidaturas(vaga_id);

-- ── Linha inicial de config ────────────────────────
insert into config (id, score_minimo, cap_por_empresa, idioma_preferencial, termos_busca, fontes_ativas)
values (
  1, 80, 3, 'pt',
  '["design engineer","design systems engineer","frontend designer","ui engineer","ux engineer","design technologist","product designer","designer ux","designer ui","ux/ui designer","web designer","design engineer ai"]',
  '{"remotive":true,"remoteok":true,"arbeitnow":true,"wwr":true,"linkedin":true,"adzuna":true,"jooble":true,"gupy":true,"catho":false}'
)
on conflict (id) do nothing;
