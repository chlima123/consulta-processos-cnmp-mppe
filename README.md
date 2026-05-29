# consultas-cnmp

Ferramenta Python para consulta automática de processos no sistema **ELO do CNMP** (Conselho Nacional do Ministério Público).

## Funcionalidades

- Busca por **nome da parte** ou **número do processo**
- Filtro por processos **arquivados**
- Exportação em **TXT, CSV, JSON e Excel**
- Paginação automática (coleta todos os resultados)
- Execução agendada via **GitHub Actions** (toda segunda-feira)
- Suporte a **Browserbase** para execução em nuvem (CI/CD)

## Instalação

```bash
pip install -e .
python -m playwright install chromium
```

Com suporte a Browserbase (para CI):

```bash
pip install -e ".[browserbase]"
```

## Uso

### Busca padrão (MPPE)

```bash
consultas-cnmp
```

### Opções disponíveis

```
consultas-cnmp [OPÇÕES]

  -t, --termo TEXTO      Nome da parte (padrão: "Ministério Público do Estado de Pernambuco")
  -n, --numero NUMERO    Número do processo (ex: 1.00230/2015-90)
  -a, --arquivado        Buscar apenas processos arquivados
  -f, --formato FMT...   Formatos de saída: txt csv json excel (padrão: txt)
  -o, --saida DIR        Diretório de saída (padrão: resultados/)
      --browserbase      Usar Browserbase em vez do Chromium local
```

### Exemplos

```bash
# Busca padrão — exporta TXT
consultas-cnmp

# Exportar em todos os formatos
consultas-cnmp --formato txt csv json excel

# Buscar por número de processo
consultas-cnmp --numero 1.00230/2015-90 --formato json

# Buscar outro MP, apenas arquivados, salvar em pasta específica
consultas-cnmp --termo "Ministério Público do Estado da Bahia" \
               --arquivado \
               --formato csv excel \
               --saida /tmp/resultados
```

## Estrutura

```
consultas_cnmp/
├── src/
│   └── consultas_cnmp/
│       ├── __init__.py
│       ├── browser.py      # contexto Playwright (local ou Browserbase)
│       ├── scraper.py      # extração e paginação
│       ├── exporters.py    # TXT, CSV, JSON, Excel
│       └── cli.py          # entrada de linha de comando
├── resultados/             # saída gerada (ignorada pelo git)
├── .github/
│   └── workflows/
│       └── consulta_agendada.yml   # execução automática semanal
├── consulta_cnmp.py        # script legado (mantido por compatibilidade)
├── pyproject.toml
└── README.md
```

## GitHub Actions

O workflow `consulta_agendada.yml` executa toda **segunda-feira às 03h (Brasília)** e faz commit dos resultados no repositório.

### Configurar secrets

No repositório GitHub, acesse **Settings → Secrets → Actions** e adicione:

| Secret | Valor |
|---|---|
| `BROWSERBASE_API_KEY` | sua chave do Browserbase |
| `BROWSERBASE_PROJECT_ID` | seu project ID do Browserbase |

### Execução manual

Na aba **Actions** do repositório, selecione **Consulta CNMP Agendada** → **Run workflow**.

## Observações técnicas

- O site bloqueia Chromium headless padrão — o modo local usa `headless=False` com anti-detecção
- Para CI/CD, use `--browserbase` (suporta headless com stealth nativo)
- O padrão regex dos números: `\d+\.\d+/\d{4}-\d{2}` (ex: `1.00230/2015-90`)
