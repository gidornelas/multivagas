# CLAUDE.md

## Visao geral

Este repositorio automatiza um funil de vagas com tres etapas principais:

1. Buscar e filtrar vagas de design/UX/UI remotas.
2. Adaptar curriculo e gerar cover letter por vaga.
3. Registrar candidatura, preparar e-mail e acompanhar follow-up.

O ponto de entrada principal e `orchestrator.py`. O agendamento diario fica em `scheduler.py`.

## Fluxo do sistema

1. `agents/buscador.py`
   - consulta APIs publicas e fontes HTML/RSS
   - normaliza vagas em `data/vagas.json`
   - calcula score e alimenta o pipeline principal
2. `agents/curriculo.py`
   - le `data/curriculo.json`
   - detecta regras de ATS via `config/ats_database.json`
   - usa a API da Anthropic para adaptar curriculo e gerar cover letter
   - salva HTML em `output/pdfs/` e texto em `output/covers/`
3. `agents/gerador_pdf.py`
   - converte HTML para PDF com `wkhtmltopdf`
   - usa Playwright como fallback quando necessario
4. `agents/candidatura.py`
   - registra candidatura em `data/candidaturas.json`
   - gera assunto/corpo de e-mail
   - nao envia automaticamente por padrao

## Arquivos e diretorios importantes

- `orchestrator.py`: CLI principal do projeto.
- `scheduler.py`: agenda execucao diaria as 08:00 e revisao de dashboard as 09:00.
- `dashboard.html`: painel visual local.
- `data/curriculo.json`: curriculo base, fonte de verdade para personalizacao.
- `data/vagas.json`: base de vagas coletadas e scoreadas.
- `data/candidaturas.json`: historico e status das candidaturas.
- `config/ats_database.json`: regras por ATS.
- `config/google_credentials.json`: OAuth Google.
- `config/google_token.json`: token local gerado apos autenticacao.
- `output/pdfs/`: HTMLs e PDFs gerados por vaga.
- `output/covers/`: cover letters geradas.

## Como executar

### Ambiente

- Python 3.11+ recomendado.
- Instalar dependencias:

```powershell
py -m pip install -r requirements.txt
```

- Instalar navegador do Playwright:

```powershell
py -m playwright install chromium
```

### Variaveis e servicos esperados

- `ANTHROPIC_API_KEY` obrigatoria para adaptacao de curriculo, cover letter e e-mail.
- Chaves de busca opcionais podem ser lidas de `.env` para fontes externas.
- Google APIs sao opcionais e usadas apenas em `enviar`, `sheets` e autenticacao.

### Comandos principais

```powershell
py orchestrator.py busca
py orchestrator.py gerar
py orchestrator.py completo
py orchestrator.py dashboard
py orchestrator.py listar
py orchestrator.py curriculo <vaga_id>
py orchestrator.py enviar
py orchestrator.py enviar --confirmar
py orchestrator.py sheets
py orchestrator.py sheets --confirmar
py orchestrator.py setup-google
```

### Scheduler

```powershell
py scheduler.py
```

Comportamento atual:

- roda o pipeline ao iniciar
- agenda pipeline diario as `08:00`
- imprime dashboard/follow-ups as `09:00`

## Regras operacionais do projeto

- O pipeline principal considera vagas com `score >= 80`.
- O modo `listar` mostra pipeline a partir de `score >= 60`.
- Candidaturas sao registradas como `aplicada` e recebem `data_followup` para `+7 dias`.
- O envio real por Gmail so acontece com `--confirmar`.
- Se `wkhtmltopdf` nao estiver instalado em `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`, o gerador tenta Playwright.

## Dependencias externas relevantes

- Anthropic API
- httpx
- beautifulsoup4
- schedule
- pdfkit
- Playwright
- Google Gmail/Sheets APIs

## Observacoes importantes

- O repositorio contem arquivos sensiveis em `config/`. Nao exponha credenciais ou tokens.
- O projeto assume escrita local em JSON; nao ha banco relacional.
- A geracao de curriculo depende do formato de `data/curriculo.json`. Mudancas estruturais nesse arquivo afetam o pipeline inteiro.
- A conversao HTML -> PDF depende de instalacao local ou do runtime do Playwright.

## Proximo ponto de leitura para manutencao

Se for mexer no fluxo principal, comece por:

1. `orchestrator.py`
2. `agents/buscador.py`
3. `agents/curriculo.py`
4. `agents/candidatura.py`
5. `agents/gerador_pdf.py`