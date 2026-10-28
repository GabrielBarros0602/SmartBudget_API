# SmartBudget API — checklist de desenvolvimento

Documento de trabalho. Governa a ordem do desenvolvimento e o que conta como pronto.

Regras:

- Item que começa com **Decidir:** só está pronto quando o ADR está escrito e commitado — não
  quando o código funciona.
- **Um item só é marcado quando está no `origin`.** Escrito no disco não conta. O checkbox vira
  no mesmo commit que fecha o item, então este arquivo é sempre verdadeiro e
  `git log -p docs/ROADMAP.md` mostra exatamente quando cada coisa fechou.
- Sprint fecha com commit próprio, atualizando o status no cabeçalho: `docs(roadmap): close S1`.

Convenções de commit em [`../CONTRIBUTING.md`](../CONTRIBUTING.md). Decisões em
[`adr/`](adr/README.md).

**Repositório:** https://github.com/GabrielBarros0602/SmartBudget_API

---

## S0 — Estrutura do repositório · ✅ Concluído

- [x] Repositório criado e conectado ao remote
- [x] `requirements.txt` e `requirements-dev.txt`
- [x] Endpoint `GET /health`
- [x] README com definição do problema
- [x] ADR-001 → [ADR-001](adr/ADR-001-layered-architecture.md)
- [x] Histórico de commits limpo e atômico
- [x] `git push` para o origin

---

## S0.5 — Processo e qualidade · 🔄 Em andamento

Adotado do SyncaAI em outubro de 2026, com o S1 já em andamento. Vem antes do bloco 3 do S1
de propósito: o código de domínio nasce dentro do processo, em vez de ser trazido para ele
depois.

- [x] `CONTRIBUTING.md`: tipos de commit ampliados, escopos de serviço único, rodapé
      `Refs: ADR-00X`, anti-patterns, branches e pull requests
- [ ] `docs/ROADMAP.md` como checklist governante, no lugar da tabela estática do README e do
      checklist do diário local, que não é versionado
- [ ] Tabela de pendências abertas neste arquivo, com a coluna "onde resolver"
- [ ] CI no GitHub Actions, em push na `main` e em pull request: `ruff check`,
      `ruff format --check` e `pytest`, com `DATABASE_URL` definida no ambiente
- [ ] mypy strict, no CI e antes de cada commit
- [ ] `main` protegida: pull request obrigatório com o check `API checks` verde, merge só por
      rebase, sem exigir aprovação
- [ ] `GET /health/ready` com `SELECT 1` no banco, separado do liveness `GET /health`
- [ ] `requirements.in` e `requirements-dev.in` compilados com
      `uv pip compile --universal --python-version 3.11`; o CI regenera e falha se algum
      arquivo mudar

**Por que `ruff format --check` e não `ruff format`:** código mal formatado deve falhar o
build, não ser corrigido em silêncio.

**Por que dois endpoints de saúde:** o orquestrador *reinicia* o container quando liveness
falha, e apenas *para de rotear tráfego* quando readiness falha. Um endpoint único que consulta
o banco faz uma oscilação de rede no PostgreSQL reiniciar a aplicação sem motivo.

**Por que `uv` em modo universal:** o desenvolvimento é em Windows e o runtime é Linux. Um
lockfile resolvido só para uma plataforma produz ambiente diferente no container — exatamente
a divergência que lockfile existe para evitar.

---

## S1 — Modelagem de domínio e banco de dados · 🔄 Em andamento

### Bloco 1 — Decisões · ✅

- [x] **Decidido:** dinheiro é `NUMERIC(12, 2)`, tratado como `Decimal`, nunca `float`
      → [ADR-002](adr/ADR-002-data-modelling-foundations.md)
- [x] **Decidido:** data da transação é `DATE`; carimbos de auditoria são `TIMESTAMPTZ` em UTC
      → [ADR-002](adr/ADR-002-data-modelling-foundations.md)
- [x] **Decidido:** chave primária `BIGINT` gerada como identity
      → [ADR-002](adr/ADR-002-data-modelling-foundations.md)

### Bloco 2 — Banco local e conexão · ✅

- [x] `docker-compose.yml` com PostgreSQL 18, volume nomeado e healthcheck
- [x] SQLAlchemy, Alembic e psycopg 3 nas dependências; variáveis do banco no `.env.example`
- [x] `Base`, engine e gerenciamento de sessão do SQLAlchemy
- [x] Sessão do banco como dependência do FastAPI (`get_db`) — mesmo padrão de injeção do
      `get_settings`

### Bloco 3 — Modelos e restrições

- [ ] Modelar o domínio: `User`, `Category`, `Transaction`, `Budget`
- [ ] Restrições no schema, não só no Python, até onde o domínio pedir: foreign keys,
      `NOT NULL`, `CHECK` em valores, unicidade composta (nome de categoria único por usuário),
      `ON DELETE CASCADE` explícito onde o filho não existe sem o pai, e índice funcional onde a
      unicidade recai sobre valor normalizado (`lower(email)`). Validação no Python vale para um
      caminho de código; constraint vale para todos, incluindo o `INSERT` manual e a importação
      de extrato do stretch
- [ ] Índices nas colunas que o relatório mensal vai filtrar

### Bloco 4 — Migrations

- [ ] **Decidir: quando as migrations rodam.** A direção é não aplicá-las no start do container
      e rodá-las explicitamente, para que um deploy nunca mute o schema como efeito colateral de
      um restart — e um restart pedido pelo liveness do S0.5 nunca vire migration. Fecha antes
      da primeira migration, porque é ela que fixa como o `Dockerfile` e o README do S4 sobem o
      banco
- [ ] Alembic inicializado, primeira migration gerada e aplicada
- [ ] Migration verificada nos dois sentidos pelo CI: `upgrade`, `downgrade`, `upgrade`. Um
      `downgrade` que nunca rodou só se revela quebrado no dia em que é preciso; no CI a
      verificação deixa de ser passo manual e vira permanente

---

## S2 — Transações e categorias

- [ ] Schemas Pydantic: `Create` / `Update` / `Read` por entidade
- [ ] Repositórios: implementações SQLAlchemy, injetadas via `Depends`
- [ ] Serviços com as regras de verdade
- [ ] Routers conectados ao `api/v1/router.py`
- [ ] Endpoint de relatório mensal — agregação por categoria
- [ ] Erros de domínio mapeados para status HTTP num lugar só; nenhum serviço importa
      `HTTPException`. Serviço que conhece HTTP não pode ser chamado fora de uma requisição —
      por teste unitário ou por script — sem arrastar o FastAPI junto, e o mapeamento espalhado
      diverge: o mesmo erro vira `400` num endpoint e `422` no outro
- [ ] Testes de integração contra PostgreSQL real, marcados como `integration` para poderem ser
      desmarcados com `pytest -m "not integration"`. Sessão falsa não pega o que importa aqui —
      constraint violada, `NUMERIC` arredondando, agregação mensal sobre `DATE` —, e o marcador
      mantém a suíte rápida rodando sem Docker
- [ ] Paginação nos endpoints de listagem
- [ ] Regras de negócio a definir: categoria com transações pode ser apagada? Transação pode ter
      data futura? Valor zero é válido?

---

## S3 — Autenticação, orçamentos e alertas

- [ ] **Decidir: parâmetros do hash de senha com argon2id** (`m`, `t`, `p`), registrados em ADR.
      Nunca um SHA puro: hashes de uso geral são rápidos, e rápido é exatamente o errado aqui.
      Entre os lentos, argon2id é memory-hard, o que encarece ataque com GPU. O SyncaAI já
      decidiu e documentou os parâmetros dele — ponto de partida, não resposta pronta
- [ ] Emissão e verificação de JWT
- [ ] Dependência `get_current_user`
- [ ] **Classe base de repositório com escopo por dono, sem nenhum acessor sem escopo** — a
      query sem filtro de `user_id` não é expressável. Ataca a falha de segurança mais provável
      deste projeto: o usuário A ler `/transactions/42`, que pertence ao usuário B. Um filtro
      lembrado por cada serviço falha na primeira vez que alguém esquece; uma base que não
      oferece o caminho sem filtro não depende de memória. O ADR-002 já depende disso: as chaves
      sequenciais só são seguras com a checagem de dono
- [ ] Entidade `Budget`: limite por categoria por mês
- [ ] **Decidir: como os alertas são produzidos.** Calculados na leitura, ou persistidos como
      eventos quando o limiar é cruzado? Muda o que a API pode oferecer (histórico?
      idempotência? notificações?) → merece ADR próprio
- [ ] Lógica dos limiares de 80% e 100%, testada nos valores de fronteira

---

## S4 — Testes, CI, Docker, acabamento

- [ ] Pirâmide de testes: unitários para serviços (repositórios falsos), integração para
      repositórios (PostgreSQL real, existentes desde o S2), uma camada fina de ponta a ponta
- [ ] Cobertura medida e reportada — escolher uma meta e justificá-la
- ~~GitHub Actions: ruff + pytest a cada push~~ → antecipado para o S0.5
- [ ] `Dockerfile` multi-stage (build vs runtime), usuário não-root
- [ ] `docker-compose up` sobe API + banco num comando só
- [ ] README: badges, roteiro de demo de 5 minutos, screenshot ou passo a passo com `curl`
- [ ] Auditoria final: sem placeholder, sem código morto, sem bloco comentado

---

## Stretch — primeiro a cortar se o prazo apertar

- [ ] Metas de economia
- [ ] Categorização automática por descrição
- [ ] Importação de extrato CSV / OFX
