# Multivagas — Documentação Completa do Projeto

> Sistema multi-agente de automação de busca e candidatura para vagas de design/UX/UI remotas, com dashboard visual hospedado no Vercel e banco de dados no Supabase.

---

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura e Fluxo do Sistema](#2-arquitetura-e-fluxo-do-sistema)
3. [Estrutura de Diretórios](#3-estrutura-de-diretórios)
4. [Fases de Desenvolvimento](#4-fases-de-desenvolvimento)
5. [Arquivos Principais](#5-arquivos-principais)
   - [orchestrator.py](#orchestratorpy)
   - [api_server.py](#api_serverpy)
   - [scheduler.py](#schedulerpy)
   - [index.html](#indexhtml)
6. [Agentes](#6-agentes)
   - [agents/buscador.py](#agentsbuscadorpy)
   - [agents/curriculo.py](#agentscurriculopy)
   - [agents/gerador_pdf.py](#agentsgerador_pdfpy)
   - [agents/candidatura.py](#agentscandidaturapy)
   - [agents/analytics.py](#agentsanalyticspy)
   - [agents/notificador.py](#agentsnotificadorpy)
   - [agents/recruiter_finder.py](#agentsrecruiter_finderpy)
   - [agents/linkedin_msg.py](#agentslinkedin_msgpy)
   - [agents/gmail_sender.py](#agentsgmail_senderpy)
   - [agents/sheets_dashboard.py](#agentssheets_dashboardpy)
   - [agents/calendar_followup.py](#agentscalendar_followuppy)
   - [agents/google_auth.py](#agentsgoogle_authpy)
7. [Scrapers](#7-scrapers)
   - [agents/scrapers/gupy.py](#agentsscrapersgupy-py)
   - [agents/scrapers/catho.py](#agentsscraperscatho-py)
   - [agents/scrapers/pcd_online.py](#agentsscraperspcd_onlinepy)
   - [agents/scrapers/incluir_pcd.py](#agentsscrapersincluir_pcdpy)
8. [Banco de Dados — Supabase](#8-banco-de-dados--supabase)
   - [db/client.py](#dbclientpy)
   - [supabase_schema.sql](#supabase_schemasql)
9. [Dados e Configuração](#9-dados-e-configuração)
   - [data/curriculo.json](#datacurriculojson)
   - [data/vagas.json](#datavagasjson)
   - [data/candidaturas.json](#datacandidaturasjson)
   - [config/ats_database.json](#configats_databasejson)
10. [GitHub Actions](#10-github-actions)
    - [busca_diaria.yml](#busca_diariaml)
    - [gerar_curriculo.yml](#gerar_curriculoyml)
11. [Infraestrutura Web](#11-infraestrutura-web)
    - [vercel.json](#verceljson)
    - [assets/](#assets)
12. [Variáveis de Ambiente](#12-variáveis-de-ambiente)
13. [Como Executar Localmente](#13-como-executar-localmente)
14. [Comandos do Orchestrator](#14-comandos-do-orchestrator)
15. [Dashboard — Páginas e Funcionalidades](#15-dashboard--páginas-e-funcionalidades)
16. [Decisões de Arquitetura](#16-decisões-de-arquitetura)
17. [Dependências](#17-dependências)

---

## 1. Visão Geral do Projeto

O **Multivagas** é um sistema de automação construído em Python que resolve um problema real: encontrar e candidatar-se a vagas de design remotas de forma eficiente, personalizada e com rastreamento completo.

O projeto foi desenvolvido por **Gianny Dornelas** — Designer UX/UI, PCD (Deficiência Auditiva), freelancer, baseada em Vila Velha/ES — e automatiza todo o ciclo de candidatura em cinco etapas:

```
Buscar vagas → Filtrar e scorear → Gerar currículo personalizado → Registrar candidatura → Acompanhar follow-ups
```

### Por que foi criado

Candidaturas manuais para vagas remotas são repetitivas e demoram horas:
- Vasculhar dezenas de plataformas diferentes
- Adaptar o currículo para cada vaga manualmente
- Montar cover letters do zero
- Controlar quais vagas foram respondidas e quais precisam de follow-up

O Multivagas faz tudo isso automaticamente, usando a API da Anthropic (Claude) para adaptar o currículo e gerar cover letters personalizadas por vaga.

### Onde roda

| Componente | Onde fica |
|---|---|
| Dashboard (frontend) | [incluavagas.vercel.app](https://incluavagas.vercel.app) |
| Banco de dados | Supabase (PostgreSQL gerenciado) |
| Automação diária | GitHub Actions (cron 08:00 BRT) |
| API local (opcional) | `py api_server.py` na porta 5001 |
| Python backend | Executa localmente ou via GitHub Actions |

---

## 2. Arquitetura e Fluxo do Sistema

### Diagrama de fluxo

```
┌─────────────────────────────────────────────────────┐
│                   FONTES DE VAGAS                   │
│  Remotive · RemoteOK · Arbeitnow · WWR · LinkedIn   │
│  Adzuna BR · Jooble · Gupy · Catho · PCD Online    │
│  Incluir PCD                                         │
└────────────────────────┬────────────────────────────┘
                         │ httpx / Playwright / RSS
                         ▼
┌─────────────────────────────────────────────────────┐
│              agents/buscador.py                     │
│  · Normaliza vagas de todas as fontes               │
│  · Score 0-100 via Claude (fit com perfil)          │
│  · Detecta idioma, PCD, localidade                  │
│  · Salva em data/vagas.json                         │
│  · Sincroniza com Supabase (tabela vagas)           │
└────────────────────────┬────────────────────────────┘
                         │ vagas score >= 80
                         ▼
┌─────────────────────────────────────────────────────┐
│              agents/curriculo.py                    │
│  · Detecta ATS pela URL da vaga                     │
│  · Analisa Fit Cultural da empresa (Fase 5)         │
│  · Uma chamada ao Claude Haiku por vaga:            │
│    — Currículo JSON adaptado (keywords injetadas)   │
│    — Cover letter personalizada (tom + fit cultural)│
│  · Salva HTML em output/pdfs/                       │
│  · Salva TXT em output/covers/                      │
│  · Sincroniza curriculo_html e cover_text Supabase  │
└────────────────────────┬────────────────────────────┘
                         │ (paralelo: até 4 vagas)
                         ▼
┌─────────────────────────────────────────────────────┐
│              agents/gerador_pdf.py                  │
│  · Tenta wkhtmltopdf (local)                        │
│  · Fallback: Playwright (Chromium headless)         │
│  · Gera PDF em output/pdfs/                         │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              agents/candidatura.py                  │
│  · Registra candidatura em data/candidaturas.json   │
│  · Gera assunto + corpo de e-mail via Claude        │
│  · Define data_followup (+7 dias)                   │
│  · Sincroniza com Supabase (tabela candidaturas)    │
└────────────────────────┬────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
┌─────────────────┐       ┌───────────────────────┐
│  Dashboard      │       │  Notificações          │
│  index.html     │       │  · Digest email diário │
│  (Vercel)       │       │  · Follow-ups Calendar │
│  Supabase JS    │       │  · Sheets tracking     │
│  SDK direto     │       │  · LinkedIn msg (F5)   │
└─────────────────┘       └───────────────────────┘
```

### Modo offline-first

O dashboard funciona sem o `api_server.py` local rodando. Todos os dados importantes são sincronizados com o Supabase e o frontend se conecta diretamente ao banco usando o SDK JavaScript. A API local é usada apenas como acelerador (dispara buscas, gera currículos em tempo real via terminal).

---

## 3. Estrutura de Diretórios

```
MULTI VAGAS/
│
├── index.html                  ← Dashboard principal (SPA, serve no Vercel)
├── vercel.json                 ← Configuração de deploy estático
├── orchestrator.py             ← CLI principal — ponto de entrada de todos os comandos
├── api_server.py               ← Servidor HTTP local (porta 5001), conecta dashboard à Python
├── scheduler.py                ← Agendamento automático de tarefas
├── requirements.txt            ← Dependências Python
├── supabase_schema.sql         ← Schema SQL para criar as 5 tabelas no Supabase
├── DOCUMENTACAO.md             ← Este arquivo
│
├── agents/                     ← Módulos especializados por responsabilidade
│   ├── buscador.py             ← Fase 1: busca e scoring de vagas
│   ├── curriculo.py            ← Fase 2: adaptação de currículo + cover letter + Fit Cultural
│   ├── gerador_pdf.py          ← Fase 2: conversão HTML → PDF
│   ├── candidatura.py          ← Fase 2: registro de candidatura e geração de e-mail
│   ├── gmail_sender.py         ← Fase 3: envio de e-mails via Gmail API
│   ├── sheets_dashboard.py     ← Fase 3: sincronização com Google Sheets
│   ├── calendar_followup.py    ← Fase 3: criação de eventos no Google Calendar
│   ├── google_auth.py          ← Fase 3: autenticação OAuth2 Google
│   ├── recruiter_finder.py     ← Fase 4: busca de e-mail do recrutador
│   ├── analytics.py            ← Fase 4: métricas de performance das candidaturas
│   ├── notificador.py          ← Fase 4: digest diário de vagas por e-mail
│   ├── linkedin_msg.py         ← Fase 5: gerador de mensagem curta para LinkedIn
│   └── scrapers/
│       ├── gupy.py             ← Scraper do portal Gupy (Playwright)
│       ├── catho.py            ← Scraper do Catho (Playwright)
│       ├── pcd_online.py       ← Scraper PCD Online (httpx + BeautifulSoup)
│       └── incluir_pcd.py      ← Scraper Incluir PCD (httpx + BeautifulSoup)
│
├── db/
│   └── client.py               ← Cliente Supabase com todas as operações CRUD
│
├── data/                       ← Persistência local (JSON)
│   ├── curriculo.json          ← Currículo base — fonte da verdade
│   ├── vagas.json              ← Vagas coletadas e scoreadas
│   ├── candidaturas.json       ← Histórico de candidaturas
│   └── analytics_historico.json← Snapshots diários de métricas
│
├── config/
│   ├── ats_database.json       ← Regras de formatação por sistema ATS
│   ├── google_credentials.json ← OAuth2 Google (não commitar)
│   └── google_token.json       ← Token local Google (não commitar)
│
├── output/
│   ├── pdfs/                   ← Currículos em HTML e PDF gerados por vaga
│   └── covers/                 ← Cover letters em TXT geradas por vaga
│
├── assets/
│   └── inclua_logo_4.png       ← Logo do dashboard
│
└── .github/workflows/
    ├── busca_diaria.yml         ← Cron diário de busca (08:00 BRT, seg–sex)
    └── gerar_curriculo.yml      ← Geração de currículo sob demanda pelo GitHub Actions
```

---

## 4. Fases de Desenvolvimento

O projeto foi desenvolvido em cinco fases incrementais:

| Fase | Descrição | Módulos principais |
|------|-----------|-------------------|
| **1** | Busca e scoring de vagas | `buscador.py`, fontes gratuitas |
| **2** | Currículo adaptado + PDF + Candidatura | `curriculo.py`, `gerador_pdf.py`, `candidatura.py` |
| **3** | Integrações Google (Gmail, Sheets, Calendar) | `gmail_sender.py`, `sheets_dashboard.py`, `calendar_followup.py` |
| **4** | Analytics, notificações e enriquecimento | `analytics.py`, `notificador.py`, `recruiter_finder.py` |
| **5** | Fit Cultural, LinkedIn, dashboard completo | `linkedin_msg.py`, analytics no dashboard, GitHub Actions |

---

## 5. Arquivos Principais

### orchestrator.py

**O ponto de entrada CLI do projeto.** Coordena todos os agentes e expõe uma interface de linha de comando unificada.

Contém as seguintes funções de pipeline:

| Função | Descrição |
|--------|-----------|
| `pipeline_completo()` | Executa busca + geração de currículos + candidaturas em sequência |
| `pipeline_processar_pipeline()` | Gera currículos para vagas já buscadas sem repetir a busca |
| `pipeline_so_busca()` | Apenas busca novas vagas |
| `pipeline_so_curriculo(vaga_id)` | Gera currículo para uma vaga específica pelo ID |
| `pipeline_so_dashboard()` | Imprime o dashboard no terminal |
| `pipeline_listar_pipeline()` | Lista vagas com score ≥ 60 formatadas no terminal |
| `pipeline_enviar_candidaturas()` | Envia e-mails de candidatura via Gmail API |
| `pipeline_sincronizar_sheets()` | Sincroniza dados com Google Sheets |
| `pipeline_calendario()` | Cria eventos de follow-up no Google Calendar |
| `pipeline_enriquecer()` | Tenta encontrar e-mails de recrutadores |
| `pipeline_digest()` | Envia digest diário com top vagas e follow-ups |
| `pipeline_analytics()` | Exibe relatório de performance das candidaturas |

**Detalhe importante — geração paralela:**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = min(4, len(vagas_processar))  # máx 4 chamadas simultâneas
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futuros = {ex.submit(_processar, v): v for v in vagas_processar}
```

Vagas com currículo já gerado são puladas automaticamente (verifica `curriculo_path` no JSON).

---

### api_server.py

**Servidor HTTP local na porta 5001** que expõe endpoints para o dashboard controlar o backend Python sem abrir o terminal.

Usa apenas `http.server.ThreadingHTTPServer` da biblioteca padrão — sem Flask ou FastAPI — para manter zero dependências extras.

#### Endpoints disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/busca` | Inicia busca de vagas em background |
| `GET` | `/api/status` | Estado atual da busca (running, error, timestamps) |
| `GET` | `/api/busca-log?since=N` | Linhas do terminal de busca (polling a cada 2,5s) |
| `GET` | `/api/vagas` | Lista de vagas (Supabase ou JSON local) |
| `GET` | `/api/candidaturas` | Lista de candidaturas |
| `GET` | `/api/curriculo` | Dados do currículo base |
| `POST` | `/api/curriculo` | Salva currículo atualizado |
| `GET` | `/api/config` | Configurações do sistema |
| `POST` | `/api/config` | Salva configurações |
| `GET` | `/api/vaga-status` | Status por vaga (dict `{vaga_key: status}`) |
| `POST` | `/api/vaga-status` | Atualiza status de uma vaga |
| `GET` | `/api/output/pdf?f=arquivo` | Serve HTML do currículo gerado |
| `GET` | `/api/output/cover?f=arquivo` | Serve cover letter TXT |
| `POST` | `/api/gerar-curriculo` | Dispara geração de currículo para vaga |
| `GET` | `/api/gerar-curriculo/status?vaga_id=...` | Acompanha progresso da geração |
| `POST` | `/api/candidatura` | Registra ou atualiza candidatura |
| `GET` | `/api/analytics` | Métricas de performance (Fase 5) |
| `GET` | `/api/analytics/historico` | Histórico de uma métrica ao longo do tempo |
| `POST` | `/api/linkedin-msg` | Gera mensagem LinkedIn para uma vaga (Fase 5) |

**Log em tempo real:** A busca é disparada com `subprocess.Popen` com `stdout=PIPE`. Cada linha de saída do processo é acumulada em `_busca_log: list[str]`. O dashboard faz polling a cada 2,5 segundos em `/api/busca-log?since=N` para exibir o terminal verde em tempo real.

---

### scheduler.py

**Agendador de tarefas recorrentes** usando a biblioteca `schedule`. Deve ser iniciado separadamente com `py scheduler.py` e fica rodando em loop.

| Horário | Tarefa |
|---------|--------|
| **08:00** diário | Pipeline completo (busca + geração de currículos) |
| **09:00** diário | Follow-ups pendentes + Digest diário por e-mail |
| **09:05** diário | Snapshot de analytics salvo em `data/analytics_historico.json` |
| **Domingo 20:00** | Relatório semanal de performance |

Ao ser iniciado, o scheduler executa o pipeline completo imediatamente antes de entrar no loop de agendamento.

---

### index.html

**O dashboard completo em um único arquivo HTML/CSS/JS.** Roda 100% no browser, sem build step, e é hospedado no Vercel como página estática.

Utiliza o **Supabase JavaScript SDK** carregado via CDN para se conectar diretamente ao banco quando a API local está offline:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>
```

#### Páginas do dashboard

| Página | Rota interna | Descrição |
|--------|-------------|-----------|
| **Dashboard** | `navTo('dashboard')` | Visão geral: stats, top vagas, follow-ups urgentes |
| **Meu Currículo** | `navTo('curriculo')` | Editor completo do currículo base com abas |
| **Vagas** | `navTo('vagas')` | Pipeline de vagas com filtros, paginação e modal |
| **Candidaturas** | `navTo('candidaturas')` | Histórico com status, e-mail e currículo gerado |
| **Busca** | `navTo('busca')` | Terminal de busca em tempo real + stats por fonte |
| **Analytics** | `navTo('analytics')` | Gráficos de performance: resposta, status, plataforma, keywords |
| **LinkedIn** | `navTo('linkedin')` | Gerador de mensagem curta para recruiter |
| **Configurações** | `navTo('config')` | Termos de busca, fontes, Supabase, GitHub Actions |

#### Autenticação

O acesso ao dashboard é protegido por login via Supabase Auth:

```javascript
function initSupabase() {
  const url = localStorage.getItem('mv_sb_url') || 'https://...supabase.co';
  const key = localStorage.getItem('mv_sb_key') || 'sb_publishable_...';
  // ...
}
async function signInWithEmailPassword(email, password) {
  const { data, error } = await _sb.auth.signInWithPassword({ email, password });
}
```

Enquanto não autenticado, o `body` recebe a classe `auth-locked` que cobre toda a interface com a tela de login.

#### Paginação de vagas

A tabela de vagas é paginada com 25 itens por página por padrão (configurável):

```javascript
let _pgAtual = 1, _pgSize = 25;
function _renderPagina(total) { /* gera botões com reticências */ }
function irPagina(n)          { /* navega para a página n */     }
```

#### Filtros de vagas (AND logic)

Os filtros de tag funcionam com lógica AND — uma vaga precisa satisfazer **todos** os filtros selecionados simultaneamente:

```javascript
if (_filtros.tags.has('pcd')  && !isPcd)  return false;
if (_filtros.tags.has('ptbr') && !isPtbr) return false;
if (_filtros.tags.has('de')   && !isDe)   return false;
```

#### Modal de vaga

Ao clicar em uma vaga, abre um modal com:
- Visualização do currículo gerado (iframe via Blob URL, sem localhost)
- Cover letter (textarea editável, salva no Supabase)
- E-mail gerado (assunto + corpo + botão "Abrir cliente de e-mail")
- Botão "Gerar currículo agora" (via API local ou GitHub Actions como fallback)
- Botão "LinkedIn" — gera mensagem e navega para a página LinkedIn
- Botão "Marcar como Aplicada"

#### Currículo offline (Blob URL)

Para exibir o HTML do currículo no iframe sem precisar do servidor local:

```javascript
function _mostrarHtml(html) {
  const blob = new Blob([html], { type: 'text/html' });
  const url  = URL.createObjectURL(blob);
  iframe.src = url;
}
// Prioridade: v.curriculo_html → API → Supabase curriculo_html
```

#### Fallback GitHub Actions

Se a API local estiver offline na hora de gerar um currículo novo, o dashboard dispara um `workflow_dispatch` no GitHub Actions via API:

```javascript
await fetch('https://api.github.com/repos/.../actions/workflows/gerar_curriculo.yml/dispatches', {
  method: 'POST',
  headers: { Authorization: `Bearer ${ghToken}` },
  body: JSON.stringify({ ref: 'main', inputs: { vaga_id: vagaId } })
});
// Depois faz polling no Supabase a cada 10s esperando curriculo_html aparecer
```

---

## 6. Agentes

### agents/buscador.py

**Agente 1 — Busca e Score de Vagas**

Consulta múltiplas fontes de vagas de forma assíncrona (usando `httpx` e `asyncio`), normaliza os dados para um formato único e usa o Claude para calcular um score de 0 a 100 indicando o fit com o perfil da candidata.

#### Fontes de vagas

| Fonte | Método | Idioma | Notas |
|-------|--------|--------|-------|
| **Remotive** | API REST JSON | EN | Categorias: design, product, ai-ml |
| **RemoteOK** | API REST JSON | EN | Vagas tech/design remote-only |
| **Arbeitnow** | API REST JSON | EN/PT | Filtra apenas vagas remotas |
| **We Work Remotely** | RSS XML | EN | Categorias design + product |
| **LinkedIn** | Scraping HTTP | PT/EN | 60 vagas por requisição |
| **Adzuna Brasil** | API REST (chave gratuita) | PT | Vagas PT-BR |
| **Jooble Brasil** | API REST (chave gratuita) | PT | Vagas PT-BR |
| **Gupy** | Playwright (SPA) | PT | Vagas PCD + home office |
| **Catho** | Playwright | PT | Home office design/UX/UI |
| **PCD Online** | httpx + BeautifulSoup | PT | Exclusivo PCD |
| **Incluir PCD** | httpx + BeautifulSoup | PT | Exclusivo PCD |

#### Score calculado pelo Claude

Para cada vaga, o Claude analisa o fit com o currículo base e retorna um score de 0 a 100:

- **≥ 80**: Pipeline principal — currículo gerado automaticamente
- **60–79**: Pipeline secundário — listado, mas currículo não gerado automaticamente
- **< 60**: Ignorado

O prompt de scoring instrui o Claude a considerar: requisitos de idioma, exigência de presencialidade, tecnologias pedidas vs. skills da candidata, menção a PCD, nível de senioridade requerido.

#### Campos normalizados de cada vaga

```json
{
  "id": "remotive_1234",
  "titulo": "Product Designer",
  "empresa": "Acme Corp",
  "descricao": "...",
  "url": "https://...",
  "salario": "USD 80k-120k",
  "localidade": "Remote — Worldwide",
  "tags": ["figma", "ux", "design-systems"],
  "data_publicacao": "2026-04-10",
  "plataforma": "Remotive",
  "idioma_vaga": "en",
  "pcd_detectado": false,
  "score": 87,
  "status": "nova"
}
```

---

### agents/curriculo.py

**Agente 2 — Construtor de Currículo Inteligente**

O coração do sistema. Transforma o currículo base genérico em uma versão personalizada e otimizada para cada vaga específica, adaptada ao ATS e ao perfil cultural da empresa.

#### Fluxo interno

```
vaga + curriculo_base + regras_ats
         │
         ▼
  analisar_fit_cultural()     ← Fase 5: detecta perfil da empresa
         │
         ▼
  adaptar_curriculo_e_cover() ← 1 chamada ao Claude Haiku
         │
         ├── Parte 1: curriculo_adaptado (JSON com keywords injetadas)
         └── Parte 2: cover_letter (texto, tom adaptado ao fit cultural)
         │
         ▼
  salvar_curriculo_html()     ← output/pdfs/empresa_titulo_data.html
  salvar_cover_letter()       ← output/covers/empresa_titulo_data_cover.txt
```

#### Função `analisar_fit_cultural(empresa, url_vaga)` — Fase 5

Detecta o perfil cultural da empresa antes de gerar a cover letter, para adaptar o tom:

**Tipos detectados:**
- `startup` → tom: "dinâmico, com impacto e velocidade"
- `corporate` → tom: "formal e orientado a resultados"
- `product` → tom: "centrado no usuário e orientado a dados"
- `agency` → tom: "criativo e colaborativo"
- `unknown` → tom: "profissional e direto" (padrão)

**Método de detecção (em ordem):**
1. Heurística por nome da empresa (banco, governo, agência...)
2. Scraping da página `/sobre` ou similar com timeout de 5s
3. Contagem de keywords por categoria (startup_kw, corporate_kw, product_kw)

Falha silenciosamente — se não conseguir detectar, usa o tom padrão.

#### Prompt único (1 chamada = currículo + cover)

Para maximizar velocidade, uma única chamada ao **Claude Haiku** gera as duas saídas, separadas por `===COVER===`:

```
[JSON do currículo adaptado]
===COVER===
[Texto da cover letter]
```

O Haiku foi escolhido por ser ~10x mais rápido e ~15x mais barato que o Opus, com qualidade suficiente para esta tarefa.

#### Detecção de ATS

A URL da vaga identifica o sistema de recrutamento usado pela empresa:

```python
def detectar_ats(url_candidatura: str, ats_db: dict) -> dict:
    url_lower = url_candidatura.lower()
    for dominio, config in ats_db.get("ats_domains", {}).items():
        if dominio in url_lower:
            return config
    return ats_db.get("default", {})
```

O ATS detectado define regras como: aceitar colunas duplas, aceitar ícones/tabelas, tamanho de fonte recomendado.

---

### agents/gerador_pdf.py

**Agente 2.5 — Conversor HTML → PDF**

Converte os arquivos HTML de currículo em PDF. Tenta dois métodos na seguinte ordem:

1. **pdfkit + wkhtmltopdf**: Rápido, boa fidelidade. Requer instalação do `wkhtmltopdf` em `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`.
2. **Playwright (Chromium headless)**: Fallback sem instalação extra. Usa o Chromium já instalado para o scraping. Mais lento mas produz PDF idêntico ao que o Chrome geraria.

O PDF é salvo no mesmo diretório do HTML (`output/pdfs/`), com o mesmo nome e extensão `.pdf`.

---

### agents/candidatura.py

**Agente 3 — Registro e Acompanhamento de Candidaturas**

Responsável por formalizar a candidatura após o currículo ser gerado.

O que faz por candidatura:
- Cria registro estruturado em `data/candidaturas.json`
- Gera assunto e corpo do e-mail via Claude (em PT-BR ou EN conforme idioma da vaga)
- Define `data_followup` para 7 dias depois
- Sincroniza com Supabase (tabela `candidaturas`)

**Estrutura de uma candidatura:**

```json
{
  "id": "cand_remotive_1234_20260410",
  "vaga_id": "remotive_1234",
  "empresa": "Acme Corp",
  "status": "aplicada",
  "data_aplicacao": "2026-04-10T08:30:00",
  "data_followup": "2026-04-17",
  "curriculo_path": "output/pdfs/acme-corp_product-designer_2026-04-10.html",
  "cover_path": "output/covers/acme-corp_product-designer_2026-04-10_cover.txt",
  "email_gerado": {
    "para": "[recrutador@acmecorp.com]",
    "assunto": "Candidatura — Product Designer | Gianny Dornelas",
    "corpo": "Olá, ...",
    "anexos": ["acme-corp_product-designer_2026-04-10.html"]
  },
  "historico": [{ "data": "...", "evento": "candidatura_criada" }]
}
```

O campo `para` é preenchido com um placeholder. Para envio real, é necessário preencher o e-mail correto do recrutador (ou usar o `recruiter_finder.py`).

---

### agents/analytics.py

**Agente 4 — Analytics de Performance**

Calcula métricas de performance das candidaturas a partir do `data/candidaturas.json`.

#### Métricas calculadas

| Métrica | Descrição |
|---------|-----------|
| `total_candidaturas` | Total de candidaturas registradas |
| `taxa_resposta_pct` | % de candidaturas que receberam algum contato |
| `score_medio` | Score médio de todas as candidaturas |
| `score_medio_contato` | Score médio só das que receberam resposta |
| `por_status` | Contagem por status (aplicada, enviada, em_processo...) |
| `por_plataforma` | Total e taxa de contato por plataforma |
| `pcd` | Stats específicos de vagas PCD |
| `tempo_medio_contato_dias` | Dias médios entre envio e primeiro contato |
| `top_keywords_efetivas` | Keywords mais presentes nas candidaturas bem-sucedidas |
| `followups_vencidos` | Candidaturas com follow-up vencido |

**Status que contam como "contato recebido":** `em_processo`, `visualizada`, `entrevista`, `aprovada`.

Salva snapshots históricos diários em `data/analytics_historico.json` (últimos 90 dias).

---

### agents/notificador.py

**Agente 4 — Digest Diário por E-mail**

Envia um e-mail HTML estilizado para a própria candidata com:
- **Top 5 vagas novas do dia** (score ≥ 80, publicadas hoje)
- **Follow-ups pendentes ou vencidos**
- **Resumo de candidaturas** (total por status)

O envio só ocorre com `dry_run=False`. Por padrão simula o envio e imprime o que seria enviado.

Configuração necessária: `EMAIL_REMETENTE` no `.env` (mesmo endereço de e e para, pois é digest pessoal).

Conectado ao `scheduler.py` na tarefa `tarefa_followups()` que roda às 09:00 diariamente.

---

### agents/recruiter_finder.py

**Agente 4 — Enriquecimento de E-mails**

Tenta encontrar o e-mail do recrutador/RH da empresa para preencher o campo `para` das candidaturas.

**Estratégias em ordem de confiança:**
1. Procura e-mails na própria página da vaga
2. Testa páginas de carreiras da empresa (`/careers`, `/vagas`, `/trabalhe-conosco`...)
3. Filtra por prefixos de RH (`hr`, `rh`, `people`, `talent`, `recruit`...)
4. Retorna `None` se não encontrar — nunca chuta um e-mail

Uma blacklist filtra e-mails genéricos como `noreply`, `support`, `marketing`.

---

### agents/linkedin_msg.py

**Agente 5 — Gerador de Mensagem LinkedIn**

Gera uma mensagem curta (≤ 280 caracteres) para enviar ao recrutador no LinkedIn, usada quando a vaga não tem e-mail disponível ou como complemento à candidatura por e-mail.

```python
def gerar_mensagem_linkedin(vaga: dict, curriculo: dict | None = None) -> str:
    # 1 chamada ao Claude Haiku
    # Estrutura: saudação + quem sou + interesse + pedido de contato
    # Tom: direto, humano, sem bajulação
```

A mensagem gerada é salva no campo `linkedin_msg` da candidatura correspondente.

**Função `listar_sem_email()`:** Lista candidaturas que ainda não têm e-mail de recrutador preenchido — candidatos prioritários para a abordagem via LinkedIn.

---

### agents/gmail_sender.py

**Agente 3 — Envio de E-mails via Gmail API**

Envia candidaturas por e-mail usando a Gmail API do Google. Requer autenticação OAuth2.

- Monta e-mail `multipart` com corpo em texto + anexos (PDF do currículo e cover letter)
- Codifica em base64 para o formato da Gmail API
- Só envia com `dry_run=False` (segurança — sem envios acidentais)

---

### agents/sheets_dashboard.py

**Agente 3 — Google Sheets**

Sincroniza dados do projeto com uma planilha Google Sheets para tracking visual.

**Abas criadas:**
- `Candidaturas`: tabela completa com status, datas, URLs
- `Pipeline`: vagas top por score
- `Resumo`: métricas agregadas (taxa de resposta, por status)

Requer `GOOGLE_SHEET_ID` no `.env` com o ID da planilha.

---

### agents/calendar_followup.py

**Agente 3 — Google Calendar**

Cria eventos de lembrete no Google Calendar para follow-ups de candidaturas.

- Cada candidatura gera um evento 7 dias após a data de aplicação
- Horário: 09:00–09:30, fuso `America/Sao_Paulo`
- Inclui alerta por e-mail

---

### agents/google_auth.py

**Autenticação OAuth2 Google** compartilhada entre Gmail, Sheets e Calendar.

- Usa `google-auth-oauthlib` para o fluxo OAuth 2.0
- Credenciais em `config/google_credentials.json` (download do Google Cloud Console)
- Token salvo em `config/google_token.json` após primeiro login
- Token é renovado automaticamente quando expira

---

## 7. Scrapers

### agents/scrapers/gupy.py

Scraper do **Portal Gupy** — principal plataforma de vagas no Brasil, utilizada por centenas de grandes empresas.

- Usa **Playwright** (Chromium headless) porque o Gupy é uma SPA (Single Page Application) e não funciona com scraping HTTP simples
- Busca por 9 termos diferentes (design engineer, ux designer, product designer...)
- Extrai links de vagas via JavaScript injetado no browser
- Filtra vagas PCD diretamente

---

### agents/scrapers/catho.py

Scraper do **Catho** — plataforma popular de vagas no Brasil.

- Também usa **Playwright** (SPA)
- Foco em vagas home office de design/UX/UI
- 5 termos de busca diferentes

---

### agents/scrapers/pcd_online.py

Scraper do **PCD Online** (pcdonline.com.br) — plataforma exclusiva para vagas inclusivas no Brasil.

- Usa **httpx + BeautifulSoup** (sem Playwright — site server-side rendered)
- Todas as vagas são PCD por definição da plataforma
- Filtra por termos de design/UX dentro do portal

---

### agents/scrapers/incluir_pcd.py

Scraper do **Incluir PCD** (incluirpcd.com.br) — similar ao PCD Online.

- Também usa **httpx + BeautifulSoup**
- Focado em vagas inclusivas no Brasil
- Filtro por termos de design

---

## 8. Banco de Dados — Supabase

O Supabase é usado como banco de dados em nuvem (PostgreSQL gerenciado), permitindo que o dashboard no Vercel acesse dados sem precisar do servidor local rodando.

### db/client.py

**Cliente Python do Supabase.** Expõe funções de alto nível para todas as operações CRUD usadas pelos agentes.

#### Funções disponíveis

| Função | Tabela | Descrição |
|--------|--------|-----------|
| `get_client()` | — | Retorna instância lazy (singleton) do cliente Supabase |
| `upsert_vagas(vagas)` | `vagas` | Insere ou atualiza lista de vagas (lotes de 200) |
| `get_vagas()` | `vagas` | Retorna todas as vagas ordenadas por score desc |
| `marcar_curriculo_gerado(...)` | `vagas` | Atualiza paths + cover_text + curriculo_html de uma vaga |
| `upsert_candidatura(cand)` | `candidaturas` | Insere ou atualiza candidatura |
| `get_candidaturas()` | `candidaturas` | Retorna candidaturas ordenadas por data desc |
| `get_curriculo()` | `curriculo` | Retorna currículo base (id=1) |
| `save_curriculo(dados)` | `curriculo` | Salva currículo base |
| `get_config()` | `config` | Retorna configurações (id=1) |
| `save_config(dados)` | `config` | Salva configurações |
| `upsert_vaga_status(key, status)` | `vaga_status` | Atualiza status de uma vaga |
| `get_all_vaga_status()` | `vaga_status` | Retorna dict `{vaga_key: status}` |

O cliente usa a chave `service_role` (acesso total) para operações do backend Python. O frontend usa a chave `anon/publishable` (acesso limitado, seguro para expor).

### supabase_schema.sql

Script SQL para criar as 5 tabelas no Supabase. Deve ser executado uma vez no SQL Editor do Supabase.

#### Tabelas

**`vagas`** — Vagas coletadas e scoreadas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | text (PK) | ID único: `remotive_1234`, `gupy_abc`... |
| `titulo` | text | Título da vaga |
| `empresa` | text | Nome da empresa |
| `descricao` | text | Descrição completa |
| `url` | text | Link para candidatura |
| `score` | integer | Score de fit (0–100) |
| `plataforma` | text | Remotive, Gupy, Catho... |
| `idioma_vaga` | text | `pt`, `en`, `pt-BR` |
| `pcd_detectado` | boolean | Vaga menciona PCD |
| `curriculo_path` | text | Caminho do HTML gerado |
| `cover_path` | text | Caminho do TXT gerado |
| `cover_text` | text | Texto da cover letter (cache) |
| `curriculo_html` | text | HTML completo do currículo (cache) |
| `status` | text | `nova`, `aplicada`, `ignorada`... |

**`candidaturas`** — Histórico de candidaturas

Contém: id, vaga_id, empresa, status, data_aplicacao, data_followup, curriculo_path, cover_path, email_gerado (JSON), keywords (array), historico (array), linkedin_msg.

**`curriculo`** — Currículo base (1 registro, id=1)

Coluna `dados` (jsonb) — armazena todo o currículo base como JSON.

**`config`** — Configurações do sistema (1 registro, id=1)

Contém: score_minimo, cap_por_empresa, idioma_preferencial, termos_busca, fontes_ativas.

**`vaga_status`** — Status personalizado por vaga (complementa `vagas.status`)

Coluna `vaga_key` (PK) + `status` — permite marcar vagas como favoritas, ignoradas, etc. diretamente pelo dashboard sem alterar a tabela principal.

**RLS (Row Level Security):** Configurada com acesso total para `anon` em todas as tabelas, permitindo que o frontend se conecte sem autenticação de linha.

---

## 9. Dados e Configuração

### data/curriculo.json

**Fonte da verdade do currículo.** Todas as gerações de currículo partem deste arquivo. Estrutura:

```json
{
  "nome": "Gianny Dornelas",
  "localidade": "Vila Velha, ES — Remoto",
  "pcd": true,
  "tipo_pcd": "Deficiência Auditiva",
  "resumo_base": "...",
  "contato": {
    "email": "...", "linkedin": "...", "portfolio": "...", "github": "..."
  },
  "skills": [
    { "nome": "Figma", "nivel": "avancado", "anos": 6 }
  ],
  "experiencias": [
    {
      "empresa": "...", "cargo": "...", "periodo": "...",
      "descricao": ["..."], "resultados": ["..."]
    }
  ],
  "projetos": [
    { "nome": "...", "stack": ["..."], "descricao": "..." }
  ],
  "educacao": [
    { "curso": "...", "instituicao": "...", "ano": "..." }
  ],
  "certificacoes": ["..."]
}
```

Mudanças estruturais neste arquivo afetam todo o pipeline. O arquivo pode ser editado diretamente no dashboard na página "Meu Currículo".

### data/vagas.json

JSON array com todas as vagas coletadas e scoreadas. Atualizado a cada execução da busca. Sincronizado com o Supabase após cada busca.

### data/candidaturas.json

JSON array com o histórico completo de candidaturas. Sincronizado com o Supabase após cada registro.

### config/ats_database.json

Banco de dados de regras de formatação por sistema ATS (Applicant Tracking System). Contém perfis para:

- **Greenhouse** — PDF coluna única, sem ícones, keywords no topo
- **Lever** — PDF ou DOCX simples
- **Workday** — Texto puro ou PDF minimalista
- **Gupy** — PDF leve, PCD declarado no resumo
- **Ashby** — PDF com links clicáveis
- **SmartRecruiters** — PDF sem tabelas
- **Catho** — PDF com seções separadas
- **default** — Regras conservadoras para ATS desconhecido

---

## 10. GitHub Actions

### busca_diaria.yml

**Executa a busca de vagas automaticamente** todos os dias úteis às 08:00 BRT (11:00 UTC), sem precisar que o computador local esteja ligado.

```yaml
on:
  schedule:
    - cron: "0 11 * * 1-5"  # seg–sex, 11h UTC = 08h BRT
  workflow_dispatch:          # permite disparo manual
```

**Fluxo:**
1. Checkout do repositório
2. Instala Python 3.11 + dependências
3. Tenta instalar Playwright (opcional, não falha o workflow se der erro)
4. Executa `python orchestrator.py busca` com todas as variáveis de ambiente dos Secrets
5. O orchestrator sincroniza automaticamente com o Supabase ao final
6. Gera resumo no GitHub Step Summary com o total de vagas encontradas

**Secrets necessários no repositório GitHub:**
- `ANTHROPIC_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ADZUNA_APP_ID` (opcional)
- `ADZUNA_APP_KEY` (opcional)
- `JOOBLE_API_KEY` (opcional)

### gerar_curriculo.yml

**Geração de currículo sob demanda** quando a API local está offline. Disparado via `workflow_dispatch` com o parâmetro `vaga_id`.

**Fluxo:**
1. Checkout do repositório
2. Instala dependências + Playwright
3. **Baixa vagas.json do Supabase** (script Python inline)
4. Executa `python orchestrator.py curriculo <vaga_id>`
5. O orchestrator sincroniza `curriculo_html` e `cover_text` no Supabase
6. O dashboard detecta os novos dados via polling e exibe o resultado

O dashboard dispara este workflow via **GitHub API** usando o token pessoal configurado nas Configurações:

```javascript
await fetch('https://api.github.com/repos/gidornelas/multivagas/actions/workflows/gerar_curriculo.yml/dispatches', {
  method: 'POST',
  headers: { Authorization: `Bearer ${ghToken}` },
  body: JSON.stringify({ ref: 'main', inputs: { vaga_id: vagaId } })
});
```

---

## 11. Infraestrutura Web

### vercel.json

Configuração de deploy estático no Vercel. Define que apenas `index.html` e os arquivos em `assets/` são servidos — o restante do repositório (Python, JSONs de dados, config) não é exposto.

```json
{
  "builds": [
    { "src": "index.html", "use": "@vercel/static" },
    { "src": "assets/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/assets/(.*)", "dest": "/assets/$1" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

Headers de segurança adicionados: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.

### assets/

Contém arquivos estáticos do dashboard:
- `inclua_logo_4.png` — Logo da marca Inclua, exibida no sidebar do dashboard

---

## 12. Variáveis de Ambiente

Configure no arquivo `.env` na raiz do projeto:

```env
# ─── Obrigatório ─────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...        # Claude API — para scoring, currículo, cover letter

# ─── Supabase ────────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=sb_secret_...          # service_role key — para o backend Python

# ─── E-mail (Fase 4) ─────────────────────────────────
EMAIL_REMETENTE=seu@email.com       # Para receber o digest diário

# ─── Google (Fase 3 — opcional) ──────────────────────
GOOGLE_SHEET_ID=1BxiMVs0X...       # ID da planilha Google Sheets

# ─── Fontes externas (opcional) ──────────────────────
ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
JOOBLE_API_KEY=...
```

**Chave pública (frontend):**
```javascript
// Hardcoded no index.html como fallback — chave anon/publishable (segura para expor)
const key = localStorage.getItem('mv_sb_key') || 'sb_publishable_...';
```

---

## 13. Como Executar Localmente

### Pré-requisitos

- Python 3.11+
- Git
- (Opcional) wkhtmltopdf instalado em `C:\Program Files\wkhtmltopdf\bin\`

### Instalação

```powershell
# 1. Clone o repositório
git clone https://github.com/gidornelas/multivagas.git
cd multivagas

# 2. Instale as dependências Python
py -m pip install -r requirements.txt

# 3. Instale o Chromium para Playwright (scraping + PDF fallback)
py -m playwright install chromium

# 4. Configure o .env
copy .env.example .env
# Edite .env com suas chaves
```

### Executar o dashboard local

```powershell
# Inicia o servidor API local (porta 5001)
py api_server.py

# Abra index.html no browser
# OU acesse direto: https://incluavagas.vercel.app
```

### Executar o scheduler automático

```powershell
py scheduler.py
# Fica rodando em loop. Ctrl+C para parar.
```

---

## 14. Comandos do Orchestrator

```powershell
# ─── Básicos ─────────────────────────────────────────────────
py orchestrator.py busca                 # Busca novas vagas em todas as fontes
py orchestrator.py gerar                 # Gera currículos para vagas sem currículo (top 5)
py orchestrator.py completo              # busca + gerar + candidaturas
py orchestrator.py dashboard             # Imprime resumo no terminal
py orchestrator.py listar                # Lista vagas (score >= 60)

# ─── Currículo específico ─────────────────────────────────────
py orchestrator.py curriculo <vaga_id>   # Gera para vaga específica

# ─── Candidaturas ─────────────────────────────────────────────
py orchestrator.py enviar                # Simula envio de e-mails (dry run)
py orchestrator.py enviar --confirmar    # Envia de verdade

# ─── Google ──────────────────────────────────────────────────
py orchestrator.py sheets                # Simula sincronização com Sheets
py orchestrator.py sheets --confirmar    # Sincroniza de verdade
py orchestrator.py calendario            # Simula criação de eventos Calendar
py orchestrator.py calendario --confirmar # Cria eventos de verdade
py orchestrator.py setup-google          # Guia de configuração OAuth Google

# ─── Fase 4 ──────────────────────────────────────────────────
py orchestrator.py enriquecer            # Busca e-mails de recrutadores (dry run)
py orchestrator.py enriquecer --confirmar # Atualiza candidaturas.json com e-mails
py orchestrator.py digest                # Simula digest diário (dry run)
py orchestrator.py digest --confirmar    # Envia digest por e-mail
py orchestrator.py analytics             # Relatório de performance no terminal
py orchestrator.py analytics --salvar    # Relatório + snapshot em JSON

# ─── Fase 5 ──────────────────────────────────────────────────
py orchestrator.py linkedin              # Lista candidaturas sem e-mail
py orchestrator.py linkedin <vaga_id>    # Gera mensagem LinkedIn para a vaga
```

---

## 15. Dashboard — Páginas e Funcionalidades

### Dashboard (visão geral)

- Cards com total de vagas, candidaturas ativas, follow-ups urgentes, score médio
- Lista das top 5 vagas por score
- Candidaturas com follow-up vencido em destaque

### Meu Currículo

Editor completo com 6 abas: Dados Básicos, Skills, Experiência, Educação, Projetos, Certificações. Salva no arquivo local e sincroniza com o Supabase automaticamente.

### Vagas

- Tabela paginada (25 por página, configurável)
- Filtros: busca por texto, status, tags (PCD, PT-BR, Design Engineer — lógica AND)
- Ao clicar na vaga: abre modal completo com currículo, cover letter e e-mail
- Botão para gerar currículo direto pelo dashboard

### Candidaturas

- Tabela com todas as candidaturas registradas
- Filtro por status e busca por texto
- Importar/exportar JSON e CSV

### Busca

- Botão para disparar busca em background
- Terminal verde com log em tempo real (polling a cada 2,5s)
- Breakdown por fonte com contagem de vagas encontradas

### Analytics (Fase 5)

- Cards: total, taxa de resposta, score médio, follow-ups vencidos
- Gráfico de barras por status (CSS puro, sem bibliotecas)
- Tabela por plataforma com taxa de contato
- Nuvem de keywords efetivas (com opacidade proporcional à frequência)
- Stats de candidaturas PCD

### LinkedIn (Fase 5)

- Campo para colar ID de vaga e gerar mensagem
- Contador de caracteres em tempo real (limite 280)
- Botão copiar
- Lista de candidaturas sem e-mail de recrutador (candidatas a abordagem LinkedIn)
- Botão "Usar" preenche o ID automaticamente

### Configurações

- Gerenciamento de termos de busca
- Fontes ativas/inativas
- Credenciais Supabase (URL + chave anon)
- Configuração de GitHub Actions (token + repositório)
- Score mínimo e outras preferências

---

## 16. Decisões de Arquitetura

### Por que não usar Flask/FastAPI?

O `api_server.py` usa apenas `http.server.ThreadingHTTPServer` da biblioteca padrão. Isso mantém zero dependências extras para a API, simplifica o deploy local e não cria conflito de versões.

### Por que Supabase em vez de SQLite?

O dashboard precisa funcionar no Vercel (serverless, sem sistema de arquivos persistente). O Supabase permite que o frontend JavaScript se conecte diretamente ao banco sem servidor intermediário, viabilizando o modo offline-first.

### Por que Claude Haiku para currículo?

A geração de currículo precisa ser rápida (4 vagas em paralelo). O Haiku é ~10x mais rápido e ~15x mais barato que o Opus, produzindo resultados de qualidade suficiente para a tarefa. O Sonnet é reservado para o scoring de vagas, onde a qualidade da análise faz mais diferença.

### Por que uma chamada unificada (currículo + cover)?

Originalmente o sistema fazia 2 chamadas separadas por vaga (adaptar_curriculo + gerar_cover_letter). Unificando em uma chamada com `===COVER===` como separador, o tempo por vaga caiu de ~30-40s para ~5-8s — uma redução de ~80%.

### Por que Blob URL para o iframe?

O currículo HTML é exibido em um `<iframe>` dentro do modal. Em produção (Vercel), não há servidor local para servir o arquivo. A solução é:
1. Buscar o `curriculo_html` do Supabase
2. Criar um `Blob` com o HTML
3. Gerar uma URL temporária com `URL.createObjectURL(blob)`
4. Usar essa URL como `src` do iframe

Isso funciona completamente offline, sem depender de nenhum servidor.

### Por que GitHub Actions como fallback de geração?

Quando o computador está desligado (situação comum para freelancers), o GitHub Actions serve como "servidor na nuvem" para executar o Python e gerar currículos. O dashboard detecta se a API local está online antes de tentar — se não estiver, usa o GitHub Actions.

### Filtros AND vs OR

A primeira implementação dos filtros de tag usava lógica OR (mostrava vagas PCD OU PT-BR). A lógica correta para o caso de uso é AND: quando a usuária seleciona PCD + PT-BR, quer ver vagas que sejam **ao mesmo tempo** PCD e PT-BR.

---

## 17. Dependências

### Python (`requirements.txt`)

| Pacote | Versão | Uso |
|--------|--------|-----|
| `anthropic` | ≥0.92.0 | Claude API — scoring, currículo, cover letter, e-mail, LinkedIn |
| `httpx` | ≥0.28.0 | Requisições HTTP assíncronas para APIs de vagas |
| `beautifulsoup4` | ≥4.14.0 | Parse HTML para scrapers (PCD Online, Incluir PCD) |
| `python-docx` | ≥1.2.0 | Geração de .docx (não utilizado ativamente, disponível) |
| `schedule` | ≥1.2.0 | Agendamento de tarefas no scheduler.py |
| `python-dotenv` | ≥1.2.0 | Carregamento de variáveis do .env |
| `pdfkit` | ≥1.0.0 | Wrapper Python para wkhtmltopdf |
| `supabase` | ≥2.3.0 | Cliente Python do Supabase |
| `playwright` | ≥1.45.0 | Browser headless para scrapers (Gupy, Catho) e PDF fallback |
| `google-api-python-client` | ≥2.0.0 | Gmail, Sheets e Calendar APIs |
| `google-auth-httplib2` | ≥0.2.0 | Transport HTTP para autenticação Google |
| `google-auth-oauthlib` | ≥1.2.0 | Fluxo OAuth2 Google |

### Frontend (CDN, sem build step)

| Biblioteca | Uso |
|------------|-----|
| `@supabase/supabase-js@2` | Conexão direta ao banco de dados |
| `Inter` (Google Fonts) | Tipografia do dashboard |

### Ferramentas externas

| Ferramenta | Necessidade | Instalação |
|------------|-------------|------------|
| `wkhtmltopdf` | PDF (opcional) | [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html) |
| Chromium (Playwright) | Scraping + PDF fallback | `py -m playwright install chromium` |

---

*Documentação gerada em abril de 2026. Projeto em evolução contínua — fase 5 implementada.*
