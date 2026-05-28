# Consulta Processos CNMP — MPPE

Script Python que acessa o sistema [ELO do CNMP](https://elo.cnmp.mp.br/pages/consulta.seam), busca processos do **Ministério Público do Estado de Pernambuco** e salva os números em um arquivo `.txt`.

## O que faz

- Acessa automaticamente o portal público de processos do CNMP
- Preenche o campo "Nome da parte" com `Ministério Público do Estado de Pernambuco`
- Percorre todas as páginas de resultado (paginação automática)
- Extrai os números de processo no formato `1.00000/AAAA-DD`
- Gera um arquivo `.txt` com um número por linha e timestamp no nome

## Pré-requisitos

- Python 3.9+
- Playwright instalado no ambiente

```bash
pip install playwright
python -m playwright install chromium
```

## Como usar

```bash
python3 consulta_cnmp.py
```

O script abre um navegador Chromium (visível), realiza a busca e salva o resultado na mesma pasta com o nome:

```
processos_mppe_YYYYMMDD_HHMMSS.txt
```

## Exemplo de saída

```
1.00230/2015-90
1.00322/2018-68
1.00271/2021-42
1.01141/2018-59
...
```

## Observações técnicas

- O site bloqueia navegadores headless — o script usa `headless=False` com anti-detecção (`--disable-blink-features=AutomationControlled`)
- O padrão regex usado para capturar números é `\d+\.\d+/\d{4}-\d{2}`
- Arquivos de debug (screenshots) são gerados automaticamente em caso de erro

## Estrutura

```
cnmp/
├── consulta_cnmp.py   # script principal
└── README.md
```
