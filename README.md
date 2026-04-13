# Angulus (Pygame)

## Regras

- **Tabuleiro:** 9 colunas × 8 linhas.
- **Objetivo:** capturar o rei adversário.
- **Cada turno:** mover uma peça.

| Peça | Movimento | Captura |
|------|-----------|---------|
| **Peão** | Exatamente 1 casa em qualquer direção | Só na diagonal (1 casa) |
| **Peça** | 1 a 2 casas em qualquer direção | 1 a 2 casas em qualquer direção |
| **Rei** | 1 a 3 casas em qualquer direção | 1 a 3 casas em qualquer direção |

> Peças deslizantes (peça/rei) não podem saltar por cima de outras peças.

---

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

### Modo IA vs IA

```bash
python main.py --ai-vs-ai WHITE_AI BLACK_AI N
# ou com profundidade explícita
python main.py --ai-vs-ai WHITE_AI WHITE_DEPTH BLACK_AI BLACK_DEPTH N
```

Valores para `WHITE_AI` / `BLACK_AI`: `random`, `minimax`, `mcst`.

**Flags opcionais:**

- `--seed <int>` — torna execuções aleatórias reprodutíveis.
- `--max-plies <int>` — limita o número de turnos antes de declarar empate.

---

## Controlos (modo jogador)

1. Clica numa das tuas peças para a selecionar.
2. Clica numa casa destacada para mover ou capturar.

---

## Análise de Dados e Benchmark

Para visualizar o relatório técnico e os gráficos de performance:

```bash
pip install streamlit pandas plotly
```

---

## Posições Iniciais

Em `main.py`, edita a constante `INITIAL_LAYOUT`:

- 8 strings (linhas), cada uma com 9 caracteres (colunas).

| Símbolo | Peça |
|---------|------|
| `P` | Peão branco |
| `A` | Peça branca |
| `K` | Rei branco |
| `p` | Peão preto |
| `a` | Peça preta |
| `k` | Rei preto |
| `.` | Casa vazia |