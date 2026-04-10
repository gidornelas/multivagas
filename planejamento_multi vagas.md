# Multi-Agente de Vagas & Construtor de Currículo Inteligente

> Planejamento técnico e estrutural do projeto  
> Desenvolvido para busca assertiva de vagas PCD em Design Engineer / UX/UI / AI  
> **Abril 2026**

---

| | |
|---|---|
| **Repositório** | [github.com/seu-usuario/multivagas](https://github.com/seu-usuario/multivagas) |
| **Plataforma base** | Claude Code + VS Code |
| **Linguagem principal** | Python 3.11+ |
| **Agentes** | 3 (Buscador, Currículo, Candidatura) |
| **Foco de vaga** | Design Engineer · AI UX · UX/UI |
| **Perfil PCD** | Deficiente Auditiva — Home Office |
| **Status** | Em desenvolvimento ativo — Fase 1 implementada |

---

## Sumário

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Agente 1 — Buscador e Filtrador de Vagas](#3-agente-1--buscador-e-filtrador-de-vagas)
4. [Agente 2 — Construtor de Currículo Inteligente](#4-agente-2--construtor-de-currículo-inteligente)
5. [Agente 3 — Candidatura e Acompanhamento](#5-agente-3--candidatura-e-acompanhamento)
6. [Stack Técnica Completa](#6-stack-técnica-completa)
7. [Melhorias e Funcionalidades Avançadas](#7-melhorias-e-funcionalidades-avançadas)
8. [Estrutura de Arquivos do Projeto](#8-estrutura-de-arquivos-do-projeto)
9. [Configuração e Primeiros Passos](#9-configuração-e-primeiros-passos)
10. [Status de Implementação](#10-status-de-implementação)
11. [Como Executar](#11-como-executar)

---

## 1. Visão Geral do Projeto

Este documento detalha a arquitetura, componentes e implementação de um sistema multi-agente desenvolvido no Claude Code para automatizar e otimizar o processo completo de busca de vagas, adaptação de currículo e envio de candidaturas.

O sistema é projetado especificamente para o perfil de **Design Engineer / AI UX Designer** com foco em vagas PCD remotas, e combina inteligência artificial, scraping de plataformas, análise de ATS e geração automática de documentos personalizados.

### 1.1 Problema que resolve

- Busca manual em múltiplas plataformas consome horas por dia
- Currículos genéricos são rejeitados por sistemas ATS antes de chegar ao RH
- Cover letters padronizadas reduzem drasticamente a taxa de resposta
- Falta de rastreamento estruturado resulta em perda de oportunidades
- Vagas PCD são dispersas em plataformas distintas, sem centralização

### 1.2 O que o sistema entrega

- Varredura diária automatizada de vagas em 7+ plataformas
- Score de compatibilidade (0–100) calculado por IA para cada vaga
- Currículo adaptado automaticamente por vaga, com keywords da descrição injetadas
- Detecção do sistema ATS usado pela empresa e formatação correspondente
- Cover letter personalizada com análise de fit cultural
- Dashboard de acompanhamento com follow-up automático

---

## 2. Arquitetura do Sistema

O sistema é composto por um orquestrador central (Claude Code com MCP) que coordena três agentes especializados. Cada agente tem responsabilidade única e se comunica via arquivos JSON estruturados e chamadas à API da Anthropic.

```
┌──────────────────────────────────────────────┐
│              ORQUESTRADOR                     │
│          (Claude Code — MCP)                  │
└──────┬───────────────┬───────────────┬────────┘
       │               │               │
  [Agente 1]      [Agente 2]      [Agente 3]
  Buscador        Currículo       Candidatura
  de Vagas        Builder         Automática
```

| Componente | Responsabilidade | Tecnologias |
|---|---|---|
| **Orquestrador** | Coordena agentes, gerencia estado, processa filas de vagas | Claude Code MCP · Python · JSON |
| **Agente Buscador** | Scraping e filtragem de vagas em múltiplas plataformas | httpx · Playwright · Remotive API |
| **Agente Currículo** | Adapta currículo base com keywords da vaga e regras do ATS | Claude API · python-docx · WeasyPrint |
| **Agente Candidatura** | Envia candidatura, rastreia status e agenda follow-ups | Gmail API · Google Sheets · Calendar API |

O fluxo de dados segue uma direção linear: o Agente Buscador produz um JSON de vagas qualificadas, que é consumido pelo Agente Currículo para gerar os documentos, e por fim o Agente Candidatura executa o envio e registro.

---

## 3. Agente 1 — Buscador e Filtrador de Vagas

Responsável por varrer plataformas de emprego, coletar vagas relevantes, calcular o score de compatibilidade e identificar oportunidades PCD. Roda de forma agendada (diariamente) e alimenta o pipeline.

### 3.1 Plataformas e Métodos de Acesso

| Plataforma | Método | Custo | Prioridade |
|---|---|---|---|
| **Remotive.com** | API REST gratuita | Gratuito | Alta — vagas remotas |
| **Wellfound** | API disponível | Gratuito | Alta — startups tech |
| **LinkedIn Jobs** | API oficial | Aprovação necessária | Alta — maior volume |
| **Indeed Brasil** | Publisher API | Gratuito | Alta — vagas PCD BR |
| **Gupy** | Web scraping (Playwright) | Gratuito | Alta — cotas PCD BR |
| **Glassdoor** | Scraping controlado | Gratuito | Média |
| **Workana** | Scraping | Gratuito | Média — freela/CLT |
| **PCD Online** | Scraping | Gratuito | Alta — exclusivo PCD |
| **Incluir PCD** | Scraping | Gratuito | Alta — exclusivo PCD |

### 3.2 Sistema de Score de Compatibilidade

Cada vaga recebe um score de 0 a 100, calculado pela API do Claude com base em quatro dimensões ponderadas:

| Dimensão | Peso | Critérios avaliados |
|---|---|---|
| Skills técnicas | **35%** | Match entre skills listadas na vaga e no currículo base |
| Experiência relevante | **25%** | Anos de experiência, projetos similares, freelance conta |
| Keywords ATS | **25%** | Palavras-chave da descrição presentes no currículo |
| Fit cultural | **15%** | Análise da página da empresa, missão, stack e tom |

> **Regra de corte:** Vagas com score abaixo de 60 são descartadas automaticamente. Entre 60 e 79 ficam em fila de baixa prioridade. Acima de 80 entram no pipeline principal e o Agente Currículo é acionado.

### 3.3 Filtros Especializados

- **Filtro PCD:** detecta marcações explícitas de vaga PCD/cota inclusiva e prioriza
- **Filtro remoto:** exclui vagas presenciais ou híbridas sem opção remota
- **Filtro salarial:** remove vagas sem faixa salarial declarada *(opcional, configurável)*
- **Filtro de senioridade:** foca em Junior, Pleno e não-gerencial
- **Deduplicação:** evita processar a mesma vaga de plataformas diferentes

---

## 4. Agente 2 — Construtor de Currículo Inteligente

Transforma o currículo base (armazenado em JSON estruturado) em uma versão personalizada para cada vaga, otimizada para o ATS específico da empresa. Gera PDF e DOCX com formatação diferenciada por tipo de uso.

### 4.1 Currículo Base em JSON

O ponto de verdade do sistema é o arquivo `curriculo.json`. Toda geração parte dele. Estrutura:

```json
{
  "nome": "...",
  "contato": { "email": "...", "linkedin": "...", "portfolio": "..." },
  "localidade": "Vila Velha, ES — Remoto",
  "pcd": true,
  "tipo_pcd": "Deficiência Auditiva",
  "resumo_base": "Parágrafo de apresentação adaptável por vaga",
  "skills": [
    { "nome": "Figma", "nivel": "avançado" },
    { "nome": "React", "nivel": "intermediário" },
    { "nome": "Claude Code", "nivel": "intermediário" }
  ],
  "experiencias": [
    {
      "empresa": "Freelancer",
      "cargo": "Designer Gráfico & UX/UI",
      "periodo": "2018–presente",
      "descricao": ["..."],
      "resultados": ["..."]
    }
  ],
  "educacao": [
    { "instituicao": "UFES", "curso": "Design", "ano": "..." }
  ],
  "projetos": [
    { "nome": "...", "url": "...", "stack": ["..."], "descricao": "..." }
  ],
  "idiomas": [{ "lingua": "Inglês", "nivel": "intermediário" }]
}
```

### 4.2 Detector de ATS

Antes de gerar o currículo, o agente identifica qual sistema ATS a empresa usa, analisando o domínio da URL de candidatura. Cada ATS tem regras próprias de parsing:

| ATS | Regras críticas | Formato ideal |
|---|---|---|
| **Greenhouse** | Sem colunas duplas. Keywords no topo obrigatório. | PDF coluna única, Arial 11pt |
| **Lever** | Aceita DOCX e PDF. Keywords nas primeiras 3 linhas. | PDF ou DOCX simples |
| **Workday** | Muito sensível. Sem ícones, tabelas ou imagens. | Texto puro ou PDF minimalista |
| **Gupy** | Sistema BR. Aceita colunas leves. PCD no resumo. | PDF com layout leve, PCD declarado |
| **Ashby** | Moderno. Lê links. GitHub e portfólio têm peso. | PDF com links clicáveis |
| **iCIMS** | Conservador. Sem formatação especial. | PDF padrão sem elementos visuais |

### 4.3 Processo de Adaptação

O Claude API recebe a descrição completa da vaga e o `curriculo.json` e executa:

1. Extrai todas as keywords técnicas e comportamentais da descrição da vaga
2. Reordena e reescreve bullets de experiência para refletir as keywords mais relevantes
3. Ajusta o resumo profissional para mencionar a tecnologia ou metodologia destacada na vaga
4. Adiciona ou promove skills que aparecem na vaga e estão no currículo base
5. Insere menção a PCD de forma estratégica quando a vaga tem cota inclusiva
6. Aplica as regras do ATS detectado (layout, fontes, colunas, ícones)

### 4.4 Saídas Geradas

| Formato | Uso |
|---|---|
| **PDF ATS-safe** | Candidaturas via formulário online — coluna única, sem ícones |
| **PDF Design** | Envio direto a recrutadores — layout visual com branding pessoal |
| **DOCX padrão** | Sistemas corporativos que exigem Word |
| **Cover letter PDF** | 1 página, personalizada por vaga e empresa |

### 4.5 Regras Universais de ATS

Independentemente do ATS detectado, o currículo gerado sempre segue:

- Sem colunas duplas — leitura da esquerda para direita
- Sem cabeçalhos em imagem ou SVG
- Fontes: Arial, Calibri ou Georgia — nunca fontes decorativas
- Seções com títulos padrão: Summary, Experience, Skills, Education
- Keywords da vaga nas primeiras 150 palavras do documento
- Sem tabelas para estruturar layout — apenas para dados comparativos

---

## 5. Agente 3 — Candidatura e Acompanhamento

Responsável pela etapa final do pipeline: redigir e enviar a candidatura, registrar no dashboard e agendar follow-ups automáticos com base no status de cada processo.

### 5.1 Tipos de Candidatura Gerados

| Versão | Quando usar |
|---|---|
| **E-mail direto** | Quando há contato de recrutador visível ou a empresa aceita candidaturas por e-mail |
| **Cover letter formal** | Quando o formulário de candidatura tem campo de carta ou texto livre |
| **Mensagem LinkedIn** | Para abordagem direta a recrutadores ou founders de startups menores |

### 5.2 APIs e Integrações

| API | Função |
|---|---|
| **Gmail API** (OAuth 2.0) | Envio de e-mails com currículo e cover letter em anexo |
| **Google Sheets API** | Dashboard de candidaturas com status em tempo real |
| **Google Calendar API** | Criação automática de lembrete de follow-up (7 dias após envio) |
| **Anthropic API** | Geração do texto de candidatura personalizado por vaga |

### 5.3 Pipeline de Status

```
[Aplicada] → [Visualizada] → [Follow-up pendente] → [Em processo] → [Encerrada]
```

- **Aplicada** — e-mail ou formulário enviado, data registrada
- **Visualizada** — confirmação de leitura via pixel de rastreamento (quando possível)
- **Follow-up pendente** — 7 dias sem resposta, lembrete criado no Calendar
- **Em processo** — resposta recebida, agendamento de entrevista
- **Encerrada** — aprovada ou recusada, motivo registrado

### 5.4 Modo PCD na Candidatura

Quando a vaga é identificada como PCD ou tem cota inclusiva, o agente aplica:

- Menciona proativamente a condição de PCD (Deficiência Auditiva) no e-mail ou cover letter
- Destaca compatibilidade com trabalho remoto assíncrono como ponto positivo
- Adapta o tom para demonstrar autonomia e comunicação escrita clara
- Inclui menção a ferramentas de acessibilidade utilizadas no trabalho (ex: transcrição automática)

---

## 6. Stack Técnica Completa

### 6.1 Linguagens e Ambiente

| Tecnologia | Uso no projeto |
|---|---|
| **Python 3.11+** | Linguagem principal dos agentes, scraping, geração de arquivos |
| **JavaScript / Node.js** | Geração de DOCX com biblioteca docx-js |
| **Claude Code** | Ambiente de desenvolvimento com MCP integrado |
| **VS Code** | Editor com extensões de IA e Git integrado |
| **Git + GitHub** | Controle de versão, histórico de currículos gerados |

### 6.2 Bibliotecas Python

| Biblioteca | Instalação | Função |
|---|---|---|
| `httpx` | `pip install httpx` | Requisições HTTP assíncronas para APIs |
| `playwright` | `pip install playwright` | Scraping de SPAs (Gupy, LinkedIn, Workana) |
| `beautifulsoup4` | `pip install bs4` | Parsing de HTML estático |
| `python-docx` | `pip install python-docx` | Geração e edição de arquivos DOCX |
| `weasyprint` | `pip install weasyprint` | Geração de PDF a partir de HTML/CSS |
| `anthropic` | `pip install anthropic` | Chamadas à API do Claude |
| `google-api-python-client` | `pip install google-api-python-client` | Gmail, Sheets e Calendar APIs |
| `schedule` | `pip install schedule` | Agendamento de execução diária dos agentes |
| `python-dotenv` | `pip install python-dotenv` | Gerenciamento seguro de chaves de API |

### 6.3 MCP Servers no Claude Code

| MCP Server | Função |
|---|---|
| `filesystem` | Leitura e escrita de currículos, logs e JSONs de vagas |
| `fetch` | Busca de páginas de vagas e sites de empresas |
| `google-drive` | Armazenamento e versionamento de currículos gerados |
| `github` | Acesso ao repositório do projeto para atualizações |

---

## 7. Melhorias e Funcionalidades Avançadas

### 7.1 Score com Feedback de Gaps

Além do score numérico, o sistema gera um relatório de gaps por vaga — listando o que está faltando no currículo atual para aumentar a compatibilidade.

**Exemplo de saída:**

```
Vaga: Design Engineer — Vercel  |  Score: 87/100

✓ Skills presentes: React, Figma, Tailwind, Git, Design Systems
✓ Keywords detectadas: component library, design token, typescript

⚠ Gap 1: Storybook — não mencionado no currículo (peso: alto)
⚠ Gap 2: TypeScript avançado — mencionado mas sem projetos concretos

→ Recomendação: adicionar projeto de Storybook ao portfólio antes de aplicar
```

### 7.2 Detecção Automática de ATS

O agente analisa a URL do botão de candidatura e cruza com um banco de dados interno de domínios de ATS. Quando não reconhece, busca pistas no HTML da página (formulários, scripts carregados, meta tags). A detecção é registrada e melhora com uso.

### 7.3 Análise de Fit Cultural

Antes de gerar a cover letter, o agente busca e lê a página "About" e o blog da empresa, além do Glassdoor. O Claude sintetiza o tom cultural e ajusta o estilo da candidatura:

| Perfil da empresa | Tom recomendado |
|---|---|
| Produto-first e técnica | Direto, foco em código e portfólio deployado |
| Startup em crescimento | Energia, adaptabilidade, impacto rápido |
| Empresa madura / corporativa | Profissionalismo, processo, métricas |
| Empresa de IA / pesquisa | Curiosidade intelectual, experimentação |

### 7.4 Modo PCD Inteligente

O sistema tem comportamento diferenciado para três cenários:

1. **Vaga exclusiva PCD** — menção direta e proativa no início da candidatura
2. **Vaga aberta que aceita PCD** — menção estratégica no corpo do e-mail
3. **Vaga sem menção a PCD** — sem menção, foco total nas competências técnicas

### 7.5 Alerta de Novas Vagas Compatíveis

Ao rodar diariamente, o agente compara as vagas novas com as já processadas e envia um resumo por e-mail com as top 5 vagas do dia, score e link direto para aplicação.

### 7.6 Versionamento de Currículos

Cada currículo gerado é salvo com nome padronizado:

```
empresa_cargo_data.pdf
ex: vercel_design-engineer_2026-04-09.pdf
```

Mantido no Google Drive para análise de quais versões geraram mais respostas ao longo do tempo.

### 7.7 Análise de Performance (fase futura)

Com dados acumulados de candidaturas, o sistema poderá calcular:

- Taxa de resposta por plataforma de origem
- Score médio das vagas que retornaram contato
- Quais keywords no currículo geraram mais visualizações
- Tempo médio entre envio e primeira resposta por tipo de empresa

---

## 8. Estrutura de Arquivos do Projeto

```
job-agent/
├── agents/
│   ├── buscador.py          # Agente 1 — scraping e score
│   ├── curriculo.py         # Agente 2 — geração de currículo
│   └── candidatura.py       # Agente 3 — envio e tracking
│
├── data/
│   ├── curriculo.json       # Currículo base estruturado (fonte da verdade)
│   ├── vagas.json           # Vagas coletadas e pontuadas
│   └── candidaturas.json    # Histórico de candidaturas
│
├── output/
│   ├── pdfs/                # PDFs gerados por vaga
│   └── covers/              # Cover letters geradas
│
├── templates/
│   ├── curriculo_ats.html   # Template PDF ATS-safe
│   └── curriculo_design.html # Template PDF visual
│
├── config/
│   ├── .env                 # Chaves de API (nunca commitado)
│   └── ats_database.json    # Mapeamento ATS por domínio
│
├── orchestrator.py          # Orquestrador principal
├── scheduler.py             # Agendamento diário
└── README.md                # Documentação do projeto
```

---

## 9. Configuração e Primeiros Passos

### 9.1 Pré-requisitos

- Python 3.11 ou superior instalado
- Node.js 18+ (para geração de DOCX)
- Conta na Anthropic com chave de API ativa
- Projeto no Google Cloud com Gmail, Sheets e Calendar habilitados
- Claude Code instalado com MCP `filesystem` e `fetch` configurados

### 9.2 Variáveis de Ambiente (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_SHEET_ID=...         # ID da planilha de tracking
EMAIL_REMETENTE=seu@email.com
LINKEDIN_EMAIL=...          # Opcional, para scraping autenticado
```

> ⚠️ O arquivo `.env` **nunca deve ser commitado** no repositório. Adicione ao `.gitignore` antes do primeiro commit.

### 9.3 Primeiro Teste — Remotive API

A Remotive API é o ponto de entrada ideal por ser gratuita, sem autenticação e com JSON limpo. Teste direto no terminal:

```bash
# Buscar vagas de design remotas agora mesmo
curl 'https://remotive.com/api/remote-jobs?category=design&limit=10'

# Filtrar vagas que mencionam "engineer" ou "ux"
curl 'https://remotive.com/api/remote-jobs?search=design+engineer&limit=20'
```

### 9.4 Instalação do ambiente Python

> **Windows com Python Launcher:** use `py` e `py -m pip` (o comando `python`/`pip` pode não estar no PATH)

```bash
# Verificar versão do Python instalada
py --version

# Instalar dependências direto (sem venv)
py -m pip install -r requirements.txt

# Opcional: criar ambiente virtual isolado
py -m venv venv
venv\Scripts\activate      # Windows (PowerShell)
py -m pip install -r requirements.txt

# Fase 2 — instalar Playwright e browsers
py -m pip install playwright
py -m playwright install chromium
```

---

---

## 10. Status de Implementação

> Atualizado em 09 de Abril de 2026 — Fases 3 e 4 em andamento

| Arquivo | Descrição | Status |
|---|---|---|
| `agents/buscador.py` | Agente 1 — 11 fontes + score via Claude Haiku | ✅ Fase 1+4 |
| `agents/curriculo.py` | Agente 2 — adaptação de currículo + cover letter | ✅ Fase 1 |
| `agents/candidatura.py` | Agente 3 — registro, dashboard, e-mail gerado + Calendar | ✅ Fase 1+3 |
| `orchestrator.py` | Orquestrador — 12 modos de execução | ✅ Fase 1+4 |
| `scheduler.py` | Execução diária com digest, analytics e follow-ups | ✅ Fase 1+4 |
| `config/ats_database.json` | Banco de dados de ATS por domínio | ✅ Fase 1 |
| `requirements.txt` / `.env.example` | Configuração do ambiente | ✅ Fase 1 |
| `data/curriculo.json` | Currículo de Gianny (educação/projetos pendentes) | 🔄 Em andamento |
| `agents/scrapers/gupy.py` | Scraper Gupy via Playwright (61 vagas/rodada) | ✅ Fase 2 |
| `agents/scrapers/catho.py` | Scraper Catho via Playwright (anti-bot ativo) | ⚠️ Fase 2 |
| `agents/scrapers/pcd_online.py` | Scraper PCD Online — vagas 100% PCD PT-BR | ✅ Fase 4 |
| `agents/scrapers/incluir_pcd.py` | Scraper Incluir PCD — vagas 100% PCD PT-BR | ✅ Fase 4 |
| `agents/gerador_pdf.py` | PDF via pdfkit + Playwright fallback | ✅ Fase 2 |
| `agents/google_auth.py` | OAuth 2.0 — token salvo em config/ | ✅ Fase 3 |
| `agents/gmail_sender.py` | Envio de e-mail via Gmail API (dry_run por padrão) | ✅ Fase 3 |
| `agents/sheets_dashboard.py` | Sincronização com Google Sheets | ✅ Fase 3 |
| `agents/calendar_followup.py` | Follow-ups automáticos no Google Calendar | ✅ Fase 3 |
| `agents/recruiter_finder.py` | Busca e-mail do recrutador via web scraping | ✅ Fase 4 |
| `agents/notificador.py` | Digest diário por e-mail (HTML) com vagas e follow-ups | ✅ Fase 4 |
| `agents/analytics.py` | Métricas de performance + snapshots históricos | ✅ Fase 4 |
| `api_server.py` | Servidor HTTP local para o dashboard interativo | ✅ Dashboard |
| `dashboard.html` | Dashboard visual completo com modal de candidatura | ✅ Dashboard |

### Fontes de vagas ativas

| Fonte | Tipo | Vagas/rodada | Autenticação |
|---|---|---|---|
| **Remotive** | API JSON | ~0–50 | Sem auth |
| **RemoteOK** | API JSON | ~96 | Sem auth |
| **Arbeitnow** | API JSON | ~60 remotas | Sem auth |
| **We Work Remotely** | RSS XML | ~194 design | Sem auth |
| **LinkedIn Brasil** | HTML scraping | ~180 PT-BR | Sem auth |
| **Adzuna Brasil** | API JSON | ~240 PT-BR | Chave gratuita |
| **Jooble Brasil** | API JSON | variável PT-BR | Chave gratuita |
| **Gupy** | Playwright SPA | ~61 PT-BR | Sem auth |
| **Catho** | Playwright SPA | 0 (anti-bot) | Sem auth |

**Total por rodada:** ~833 brutas → ~510 relevantes → ~467 novas → **67 pipeline (≥80)**

### O que está funcionando agora

**Fase 1 — Core:**
- Busca em 9 fontes simultâneas com asyncio
- Score 0–100 por Claude Haiku com análise de gaps e keywords ATS
- Filtros: cargo relevante, inglês obrigatório, deduplicação por ID + (empresa, título)
- Cap de 3 vagas por empresa (evita spam de DataAnnotation e similares)
- Priorização PT-BR: vagas brasileiras processadas primeiro pela IA
- Currículo adaptado por vaga via Claude Sonnet com keywords injetadas
- Cover letter personalizada — tom PCD quando a vaga tem cota inclusiva
- Rascunho de e-mail gerado e salvo em `candidaturas.json`
- Dashboard no terminal com status por processo

**Fase 2 — Scraping SPA + PDF:**
- Gupy scraper via Playwright com injeção de JS (DOM real do React)
- Geração de PDF via pdfkit (wkhtmltopdf) com fallback Playwright Chromium
- HTMLs de currículo adaptados salvos em `output/pdfs/`

**Fase 3 — Google APIs:**
- OAuth 2.0 configurado — token salvo em `config/google_token.json`
- Gmail API pronta — envio com `dry_run=True` por padrão (seguro)
- Google Sheets sincronizado — 3 abas: Candidaturas, Pipeline, Resumo
- 10 candidaturas + 100 vagas top visíveis na planilha

### Próximos passos sugeridos

1. Preencher `data/curriculo.json` com educação, projetos e certificações reais
2. Substituir placeholders `[recrutador@empresa.com]` em `candidaturas.json` pelos e-mails reais e rodar `py orchestrator.py enviar --confirmar`
3. Investigar Catho anti-bot (tentar cookies/delay ou alternativa como InfoJobs)
4. Rodar `py orchestrator.py busca` diariamente — ou ativar `py scheduler.py`

---

## 11. Como Executar

### Configuração inicial

> **Windows:** Use `py` no lugar de `python` e `py -m pip` no lugar de `pip`

```bash
# 1. Clone o repositório
git clone https://github.com/gidornelas/multivagas.git
cd multivagas

# 2. Instale as dependências
py -m pip install -r requirements.txt
py -m playwright install chromium

# 3. Configure as variáveis de ambiente
copy .env.example .env
# Edite .env com: ANTHROPIC_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY,
#                 JOOBLE_API_KEY, EMAIL_REMETENTE, GOOGLE_SHEET_ID

# 4. Configure Google APIs (Fase 3)
py orchestrator.py setup-google   # exibe o guia passo a passo
# Depois de configurar config/google_credentials.json:
py -c "from agents.google_auth import testar_conexao; testar_conexao()"
py -c "from agents.sheets_dashboard import criar_estrutura_planilha; criar_estrutura_planilha()"
```

### Executar o pipeline

```bash
# Buscar e pontuar vagas (salva em data/vagas.json)
py orchestrator.py busca

# Gerar currículos e e-mails para top 5 vagas do pipeline
py orchestrator.py gerar

# Pipeline completo: busca + geração
py orchestrator.py completo

# Listar todas as vagas por score
py orchestrator.py listar

# Ver dashboard de candidaturas no terminal
py orchestrator.py dashboard

# Gerar currículo para uma vaga específica pelo ID
py orchestrator.py curriculo adzuna_5693737445

# Sincronizar com Google Sheets
py orchestrator.py sheets                  # simulação
py orchestrator.py sheets --confirmar      # sincroniza de verdade

# Enviar candidaturas por e-mail
py orchestrator.py enviar                  # simulação (dry run)
py orchestrator.py enviar --confirmar      # envia de verdade

# Execução diária agendada (08h00 todos os dias)
py scheduler.py
```

### Fluxo de uso diário recomendado

```
1. py orchestrator.py busca           → coleta vagas novas e pontua
2. py orchestrator.py listar          → revisa top vagas
3. py orchestrator.py gerar           → gera currículos e e-mails
4. Revisa output/pdfs/                → confere os HTMLs gerados
5. Preenche e-mail do recrutador      → edita data/candidaturas.json
6. py orchestrator.py enviar          → simula o envio (dry run)
7. py orchestrator.py enviar --confirmar → envia de verdade
8. py orchestrator.py sheets --confirmar → atualiza planilha
```

---

*Documento atualizado em 09 de Abril de 2026 · Fases 1, 2 e 3 implementadas*  
*Repositório: github.com/gidornelas/multivagas*