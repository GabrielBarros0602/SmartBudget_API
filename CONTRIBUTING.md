# Contributing to SmartBudget API

Solo project, but the conventions are enforced as if it were not. The commit
history is part of the deliverable: it should be possible to read it end to end
and understand both what the API does and why it was built that way.

Code, comments and commit messages are written in English.

## Commit convention

[Conventional Commits](https://www.conventionalcommits.org/), with the type set
below.

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Use for |
|---|---|
| `feat` | new behaviour visible to an API consumer |
| `fix` | corrects broken behaviour |
| `refactor` | changes structure without changing behaviour |
| `perf` | changes behaviour only in how fast or cheap it is |
| `test` | adds or changes tests, nothing else |
| `docs` | documentation, including ADRs and the roadmap |
| `build` | Dockerfile, dependency manifests, build configuration |
| `ci` | GitHub Actions workflows |
| `style` | formatting only, zero logic change |
| `chore` | anything that fits none of the above — repository plumbing |
| `revert` | reverts a previous commit |

`build`, `ci`, `perf`, `style` and `revert` extend the original six. The
distinction that matters most in practice is `build` versus `ci`: `build` is how
the artifact is produced, `ci` is what verifies it.

### Scopes

The scope is the area of this single-service repository that a change touches.
Required whenever a single area is touched.

| Scope | Area |
|---|---|
| `api` | the FastAPI service in general — routers, services, schemas, settings |
| `db` | models, migrations, repositories and queries |
| `auth` | authentication, authorization, ownership isolation |
| `deps` | dependency manifests |
| `adr` | architecture decision records |
| `roadmap` | sprint checklist |

Omit the scope only when a change genuinely spans the repository.

### Subject line

- Imperative mood: `add`, not `added` or `adds`
- Lowercase after the colon
- No trailing period
- 72 characters maximum
- English

### Body

Optional. Use it to say **why**, not what — the diff already says what. Wrap at
80 columns.

### Footer

Reference the architecture decision a commit implements:

```
Refs: ADR-002
```

This is the mechanism that keeps the code connected to its reasoning. Any commit
implementing a recorded decision carries the reference, so
`git log --grep "ADR-002"` shows every change that decision produced.

Breaking changes use `!` after the scope and a footer:

```
feat(api)!: rename the transaction field date to occurred_on

BREAKING CHANGE: clients sending "date" must send "occurred_on" instead.
```

### Examples

```
feat(db): add transaction model with amount as NUMERIC(12, 2)

Money stays exact end to end: the column is NUMERIC and the Python type is
Decimal, so the monthly aggregation cannot drift by cents.

Refs: ADR-002
```

```
build(deps): lock dependencies with uv pip compile
test(db): add transaction repository tests against real postgres
ci: run ruff, mypy and pytest on push and pull request
docs(adr): record how budget alerts are produced
fix(auth): filter transactions by owner in the repository layer
```

### Anti-patterns

- `wip`, `update files`, `changes`, `fix stuff` — say what changed
- One commit mixing a refactor with a feature — split it; the refactor goes first
- A commit that leaves the test suite red
- A single commit containing a whole sprint

## Architecture decisions

Every non-trivial architectural decision gets an ADR in
[`docs/adr/`](docs/adr/README.md).

## Branches and pull requests

`main` changes only through a pull request with a green `API checks` check.
Nothing is committed to `main` directly, and branch protection enforces it so
the rule does not depend on memory.

Branch names use the commit types as prefixes:

```
feat/transaction-model
fix/env-file-discovery
docs/adr-003-budget-alerts
build/uv-lockfiles
```

The pull request title follows the commit convention, so the merged history
reads the same as the log:
`feat(db): add domain models for user, category, transaction and budget`.

**Merge with rebase, never squash.** Squashing collapses a branch into one
commit, which destroys the atomic history this project treats as a deliverable —
a four-commit branch becomes one opaque change. Rebase keeps each commit and
keeps the history linear. Enable *Allow rebase merging* and disable both
*Allow squash merging* and *Allow merge commits* in the repository settings, so
the wrong button is not there to press.

Do not enable *Require approvals* on a solo repository: GitHub refuses to let an
author approve their own pull request, so it would make every merge impossible
or force an admin bypass, which turns the rule into theatre.

## Sprint discipline

Development is governed by [`docs/ROADMAP.md`](docs/ROADMAP.md), and its header
holds the rules: a `Decidir:` item closes only when its ADR is committed, a
checkbox is ticked in the same commit that completes the item and only once the
work is on `origin`, and a sprint closes with its own commit —
`docs(roadmap): close S1`.

One checklist item is roughly one to three commits. If an item needs ten, it was
two items.

## Before every commit

The same checks CI runs, one per line so a failure says which one it was:

```
ruff format .
ruff check .
pytest
```

CI runs `ruff format --check`, so unformatted code fails the build rather than
being fixed silently.

---

## Português

**Convenção de commits:** Conventional Commits com o conjunto de tipos acima. A
base original (`feat`, `fix`, `chore`, `docs`, `test`, `refactor`) foi ampliada
com `build`, `ci`, `perf`, `style` e `revert`. A distinção que mais importa na
prática é `build` contra `ci`: `build` é como o artefato é produzido, `ci` é o
que o verifica.

**Escopos** dizem qual área deste repositório de serviço único a mudança toca —
`api`, `db`, `auth`, `deps`, `adr`, `roadmap`. Sem escopo só quando a mudança
atravessa o repositório todo.

**Rodapé `Refs: ADR-002`** em todo commit que implementa uma decisão registrada.
É o mecanismo que mantém o código ligado ao raciocínio:
`git log --grep "ADR-002"` mostra tudo que aquela decisão produziu.

**Anti-patterns:** mensagem que não diz o que mudou, refactor misturado com
feature, commit que deixa a suíte vermelha, sprint inteiro num commit só.

**Branches e pull requests:** a `main` só muda por PR com o check `API checks`
verde, e a proteção da branch garante isso. Nome de branch usa os tipos de
commit como prefixo — `feat/transaction-model`, `docs/adr-003-budget-alerts`.
Título do PR segue a convenção de commit.

**Merge com rebase, nunca squash.** Squash colapsa a branch num commit só e
destrói o histórico atômico que este projeto trata como entregável. Desabilite
*Allow squash merging* e *Allow merge commits* nas configurações para o botão
errado não existir.

Não habilite *Require approvals* em repositório solo: o GitHub não deixa o autor
aprovar o próprio PR, então todo merge ficaria impossível ou dependeria de
bypass de admin.

**Disciplina de sprint:** o [`docs/ROADMAP.md`](docs/ROADMAP.md) governa o
desenvolvimento, e as regras estão no cabeçalho dele. Um item de checklist são um
a três commits; se precisar de dez, eram dois itens.

**Antes de cada commit:** `ruff format .`, `ruff check .` e `pytest`. O CI roda
`ruff format --check`, então código mal formatado falha o build em vez de ser
corrigido em silêncio.

Código, comentários e mensagens de commit em inglês; o roadmap em português,
porque é instrumento de trabalho.
