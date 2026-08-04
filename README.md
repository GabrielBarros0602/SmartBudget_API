# SmartBudget API

A personal finance REST API for tracking transactions, categorising spending,
and enforcing monthly budgets with threshold alerts.

Built with Python, FastAPI and PostgreSQL, using a layered architecture and
documented architectural decisions.

> **Status:** in development — S0 (scaffolding) complete. See [Roadmap](#roadmap).

---

## The problem

Instant payments changed how Brazilians spend money. In 2025, Pix moved
**R$ 35.36 trillion across 79.8 billion transactions** — a 33.6% jump over 2024
— and now regularly clears more than 300 million transfers in a single day.
Spending stopped being a handful of monthly card statements and became hundreds
of small, scattered, instant transfers.

Household finances did not keep up. The CNC's Peic survey put the share of
Brazilian families carrying debt at **80.4% in March 2026**, the highest in the
series since 2010, with **29.6%** holding overdue debt.

The tooling splits into two unsatisfying halves: manual spreadsheets, which are
accurate but abandoned within weeks, and closed consumer apps, which hold your
data and expose no programmable interface.

SmartBudget API is the missing middle: an open, well-tested back-end that owns
the hard part — categorisation, aggregation and budget rules — and leaves the
interface open to whatever consumes it.

## Features

| | Feature | Sprint |
|---|---|---|
| ☐ | Users and JWT authentication | S3 |
| ☐ | Transaction tracking (income / expense) | S2 |
| ☐ | Categories and categorisation rules | S2 |
| ☐ | Monthly report with per-category aggregation | S2 |
| ☐ | Budgets with alerts at 80% and 100% of a category limit | S3 |
| ☐ | Savings goals | stretch |

## Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy + Alembic |
| Auth | JWT |
| Tests | pytest |
| Lint / format | ruff |
| Containers | Docker + docker-compose |
| CI | GitHub Actions |

## Architecture

Four layers, one direction of dependency:

```
router  →  service  →  repository  →  PostgreSQL
(HTTP)     (rules)     (persistence)
```

Two rules keep the structure honest:

- **Business rules live only in the service layer.** Not in routers, not in repositories.
- **Repositories are injected via `Depends`,** never instantiated inside a service.

The reasoning, the alternatives that were rejected, and the conditions under
which this should be reconsidered are recorded in
[ADR-001](docs/adr/ADR-001-layered-architecture.md).

### Project structure

```
app/
├── api/            routers — HTTP in, HTTP out
│   ├── health.py   liveness probe (unversioned, on purpose)
│   └── v1/         versioned domain routers
├── services/       business rules — the only place they may live
├── repositories/   database access — no rules
├── models/         SQLAlchemy models (database shape)
├── schemas/        Pydantic schemas (API contract shape)
├── core/           settings and cross-cutting concerns
└── main.py         application factory
docs/adr/           architecture decision records
tests/
```

## Getting started

Requires Python 3.11+.

```powershell
git clone https://github.com/GabrielBarros0602/SmartBudget_API.git
cd SmartBudget_API

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
Copy-Item .env.example .env

uvicorn app.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`, with interactive docs at
`http://127.0.0.1:8000/docs`.

```powershell
# health check
curl http://127.0.0.1:8000/health

# tests and linting
pytest
ruff check .
ruff format .
```

## Roadmap

| Sprint | Scope | Status |
|---|---|---|
| S0 | Repo scaffolding, `GET /health`, ADR-001 | ✅ Done |
| S1 | Domain modelling, PostgreSQL via Docker, Alembic migrations | ⏳ Next |
| S2 | Transactions and categories: CRUD + business rules | ☐ |
| S3 | JWT auth, budgets and threshold alerts | ☐ |
| S4 | pytest suite, GitHub Actions CI, Dockerfile, demo script | ☐ |

## Contributing conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:` — imperative mood, small and frequent.
- Code, comments and commit messages are written in English.
- Every non-trivial architectural decision gets an ADR in `docs/adr/`.

## Sources

- Pix transaction volume, 2025 — Banco Central do Brasil, via
  [Agência Brasil](https://agenciabrasil.ebc.com.br/economia/noticia/2025-12/pix-bate-recorde-e-supera-313-milhoes-de-transacoes-em-um-dia)
  and [Gazeta do Povo](https://www.gazetadopovo.com.br/economia/pix-bate-recorde-historico-e-movimenta-r-35-trilhoes/)
- Household indebtedness — CNC, *Pesquisa de Endividamento e Inadimplência do
  Consumidor* (Peic), March 2026: [pesquisascnc.com.br](https://pesquisascnc.com.br/pesquisa-peic/),
  reported by [CNN Brasil](https://www.cnnbrasil.com.br/economia/macroeconomia/cnc-endividamento-das-familias-atinge-novo-recorde-e-chega-a-80-4/)

## License

MIT

---

# SmartBudget API (Português)

Uma API REST de finanças pessoais para registrar transações, categorizar gastos
e controlar orçamentos mensais com alertas de limite.

Construída com Python, FastAPI e PostgreSQL, em arquitetura em camadas e com
decisões arquiteturais documentadas.

## O problema

O pagamento instantâneo mudou a forma como o brasileiro gasta. Em 2025, o Pix
movimentou **R$ 35,36 trilhões em 79,8 bilhões de transações** — alta de 33,6%
sobre 2024 — e já ultrapassa 300 milhões de transferências em um único dia. O
gasto deixou de ser algumas faturas mensais e virou centenas de transferências
pequenas, instantâneas e dispersas.

O controle financeiro não acompanhou. A Peic/CNC registrou **80,4% das famílias
brasileiras endividadas em março de 2026**, o maior patamar da série histórica
iniciada em 2010, com **29,6%** com dívidas em atraso.

As ferramentas se dividem entre planilhas manuais — precisas, mas abandonadas em
poucas semanas — e aplicativos fechados, que retêm os dados do usuário e não
oferecem interface programável.

A SmartBudget API ocupa esse espaço: um back-end aberto e testado que resolve a
parte difícil (categorização, agregação e regras de orçamento) e deixa a
interface livre para quem for consumi-la.

## Arquitetura

Quatro camadas, uma única direção de dependência:

```
router  →  service  →  repository  →  PostgreSQL
(HTTP)     (regras)    (persistência)
```

Duas regras sustentam a estrutura:

- **Regras de negócio existem apenas na camada de serviço** — nunca em routers ou repositórios.
- **Repositórios são injetados via `Depends`**, nunca instanciados dentro do serviço.

O raciocínio completo, as alternativas descartadas e os critérios para
reavaliar a decisão estão em [ADR-001](docs/adr/ADR-001-layered-architecture.md).

## Como rodar

Requer Python 3.11+.

```powershell
git clone https://github.com/GabrielBarros0602/SmartBudget_API.git
cd SmartBudget_API

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
Copy-Item .env.example .env

uvicorn app.main:app --reload
```

Documentação interativa em `http://127.0.0.1:8000/docs`.

## Status

S0 (estrutura do repositório) concluído. Próximo: S1 — modelagem de domínio,
PostgreSQL via Docker e migrações com Alembic.
