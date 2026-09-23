# Career Quest

Career Quest is an employee-development navigator for HackAlem AI, Case 1. The Halyk visual frontend is connected to FastAPI: it loads the starter kit, projects current skills, calculates next-grade gaps, shows a development map, records completions, provides HR aggregates/import and persists a demonstration rewards ledger.

**Full LLM context and validated recommendation orchestration are implemented; a live provider is not configured.** The default recommendation endpoint returns HTTP 501 when eligible candidates require a model. With no candidates it returns `no_candidates`. See [the LLM context contract](docs/llm-context.md) for provider integration and the authorized context endpoint.

## Наше решение — Halyk Career Quest

**Трек: Halyk Bank. Кейс №1: Career Quest — AI-навигатор развития сотрудника.**
Команда IFlow создаёт персональную карту карьерного развития: сотрудник выбирает
ориентир из требований следующего грейда и заданной в профиле цели, видит ближайшие
полезные шаги и понимает, как каждый из них развивает навыки.
В одной истории соединяются обучение, практика, менторство и приятные награды.

### Какую задачу решаем

Каталог курсов сам по себе не объясняет сотруднику, с чего начать и что поможет
приблизиться к следующему грейду. HR нужны данные о дефицитах навыков и о том,
каким сотрудникам пока не удаётся предложить подходящее развитие.

Наш подход — связать профиль сотрудника, требования роли и доступные мероприятия
в понятный маршрут из **1–3 ближайших шагов**. Для каждого шага показываем,
почему он подходит, сколько времени займёт и какой навык поможет развить.

### Карта развития как главное пространство

Главный экран — игровая карта в зелёно-золотой стилистике Halyk с собственной
SVG-иллюстрацией ландшафта, узлами событий и анимациями. Названия районов и
показатели навыков берутся из реального профиля сотрудника. На карте отображается
до пяти событий; полный каталог доступен в разделе «События».

- **Карьерный ориентир:** следующий грейд или уже заданная в профиле цель.
  Переключение меняет представление маршрута; редактирование профиля API пока
  не поддерживает.
- **Развилки:** доступные обучение, практика и менторство из исходного каталога.
- **Доступные и будущие этапы:** сервер проверяет роль, грейд, навыки, историю и
  расписание. Карточка объясняет ограничения недоступного события.
- **Свой темп:** 1, 3 или 5 часов в неделю. Самостоятельные задания можно
  распределять по неделям, живые встречи должны помещаться в доступное время.
  Это локальный фильтр ближайших шагов; выбранный темп не отправляется LLM.
- **Прогресс:** подтверждение завершения отправляется на сервер. После записи
  интерфейс загружает обновлённые навыки, историю, маршрут и баланс наград.

Игровой путь и обмен внутренних монет на полезные предложения вдохновлены
механикой Astana Hub. Мы адаптируем их под карьерные цели сотрудников Halyk
и зелёно-золотую визуальную стилистику банка.

### Где нужен ИИ

AI-навигатор должен помогать подобрать маршрут и объяснить его человеческим
языком. В интерфейсе уже есть запрос рекомендаций через backend и отображение
ответов, факторов выбора, гипотез и уточняющих вопросов. Сценарий
**«Хочу стать Senior, но на обучение есть только час в неделю»** пока разделён
на серверные требования к цели и локальный фильтр нагрузки на карте.

Рекомендации должны учитывать несколько факторов одновременно:

1. Дефицит и критичность навыков для следующего грейда или карьерной цели.
2. Текущую роль, грейд и предварительные требования мероприятия.
3. Историю участия: завершения, отказы, пропуски и обратную связь.
4. Формат, продолжительность и расписание. Выбранный в интерфейсе темп сейчас
   меняет только оценку длительности; в LLM он пока не передаётся.

Сначала backend определяет допустимых кандидатов и рассчитывает прогресс.
Затем в LLM передаётся полный профиль, вся история с карточками мероприятий,
каталог и требования текущего/следующего грейда и явно заданной цели. Инструкция
требует объяснения минимум по трём факторам. Результат проходит проверку: рекомендовать можно только реальные
мероприятия из каталога, соответствующие ограничениям. Уровни навыков и
начисления рассчитываются по правилам данных, а не генерируются моделью.

**Сейчас внешний провайдер LLM не подключён:** при наличии кандидатов endpoint
рекомендаций по умолчанию возвращает HTTP 501. Подготовка контекста, инструкции,
адаптер JSON-ответов и проверки уже работают; [контракт подключения](docs/llm-context.md).
Карта показывает только сохранённую AI-подборку: один основной шаг и до двух
дополнительных при высокой уверенности и отдельном обосновании пользы.
При сомнении в дополнительных вариантах остаётся один шаг. Без провайдера
карта показывает статус недоступности AI; полный каталог и профиль доступны.
Темп обучения меняет оценку длительности, но не состав и порядок рекомендаций.

### Halyk Market — награды за развитие

За каждое новое добровольное завершение через API сотрудник получает
**80 внутренних монет** и выбирает награды: книги, мерч или билеты на
профессиональные мероприятия. Начальный баланс — **0**. Исходная и
импортированная история завершений монет не начисляет. На карте видно, сколько
ещё монет нужно до ближайшей награды.

Монеты не повышают уровни навыков и не влияют на решение о повышении.
Обучение и менторство остаются бесплатными. За обязательные процессы награды
не начисляются. Каталог, баланс и обмены загружаются через API; списание монет и
квитанции обмена сохраняются в серверном состоянии. Сервер проверяет баланс,
повтор запроса и повторный обмен одной награды. Market остаётся демонстрацией:
реальные покупки, доставка и интеграция с коммерческим Halyk Market не подключены.

### Пример пользовательского пути

**Вход сотрудником → выбор доступного карьерного ориентира → темп → ближайшие
события → подтверждение пройденной активности → обновление навыков и маршрута →
награда в Market.**

Покрытие требований к навыкам показывает продвижение к цели, но не является
гарантией повышения. Сотрудник может переключить отображаемый ориентир и темп;
новую карьерную цель пока нельзя сохранить через интерфейс.

### Что получает HR

Общую картину дефицитов навыков, участия в мероприятиях и доступности подходящих
шагов. Это помогает планировать обучение и расширять каталог там, где
возможностей не хватает. Данные сотрудника защищены разграничением доступа;
публичный рейтинг эффективности сотрудников не предусмотрен.

Для проверки кейса сохраняется поддержка исходного JSON/CSV-формата и импорта
дополнительных профилей и истории жюри. В текущем API отсутствие допустимых
кандидатов уже рассчитывается; показатель отсутствия AI-рекомендаций появится
после реализации рекомендателя.

### Текущий статус

| Часть решения | Статус |
| --- | --- |
| Данные стартового набора, расчёт навыков и траектории, допустимые мероприятия | Реализованы; интерфейс использует ответы backend |
| FastAPI, разграничение employee/HR, импорт, завершения и HR-агрегаты | Подключены к основному интерфейсу |
| Игровая карта, обзор, каталог событий и адаптивный интерфейс Halyk | Основной frontend проекта; локальные фильтры работают поверх серверных данных |
| Halyk Market | Серверный каталог, баланс и сохраняемые обмены; демонстрационные награды |
| Полный контекст LLM, инструкции, адаптер JSON и проверка фактов | Реализованы; UI поддерживает ответы и ошибки, внешний провайдер ещё не настроен |
| Предложения и почтовые уведомления | Сохраняемая очередь, SMTP HR, расписание, паузы, реакции сотрудников и журнал; требуется настройка отправителя и LLM |
| Docker Compose и native-запуск | Один origin для браузера через Next.js-прокси `/backend` |

Следующие шаги: подключить LLM-провайдера, оценить качество рекомендаций и
добавить API редактирования цели и интеграцию записи с организатором. Запись на предложенный курс уже сохраняется в системе уведомлений. Подробности текущей
связи интерфейса с сервером: [frontend integration](docs/frontend-integration.md).

## Launch

Prerequisites: Docker Desktop with Linux containers. From the repository root:

```sh
docker compose up --build
```

Open [Career Quest](http://localhost:3000), [API documentation](http://localhost:8000/docs), or [health](http://localhost:8000/health). No API keys are needed. The original files already live in data/raw; if distributing without restricted data, copy the four source files and README translations from case_1/career_quest_dataset in the supplied archive before starting.

Enter one of the **public local-demo tokens**:

| Token | Identity | Access |
| --- | --- | --- |
| demo-employee | E0001 | Own development information |
| demo-active | E0004 | Own development, including an unfinished assignment |
| demo-hr | HR | Employee inspection, aggregates and jury imports |

On the login screen, choose **Сотрудник** (`demo-active`, E0004) or **HR-команда** (`demo-hr`), or enter another configured token. The frontend obtains the role from `/api/session`; it does not infer permissions from the token text. Tokens stay in page memory, so reloading requires login again.

For an immediate demo, open the employee's events and confirm a completed self-paced activity or an existing assignment. The server updates skills and trajectory; new voluntary completions earn Market coins. Switch to HR for aggregates and imports. HR can inspect employee routes and the reward catalog, but cannot complete activities or redeem rewards on an employee's behalf.

The browser calls `/backend/api/...` on the frontend origin. Next.js forwards requests to `http://backend:8000` inside Compose; the browser does not need to resolve the Docker service name.

Production authentication is outside this MVP. Backend authorization is enforced on every protected endpoint; entering a role header cannot grant access. Demo tokens are deliberately public and unsuitable for deployment. Replace core/auth.py identity verification before exposing this app to untrusted users. Compose binds host ports to loopback.

## Architecture and technology

Next.js App Router + TypeScript + custom CSS/SVG -> same-origin Next.js proxy -> FastAPI + Pydantic -> deterministic services -> repositories -> immutable JSON/CSV and one mutable JSON overlay. One Uvicorn worker, one mutation lock, one atomic state replacement. No database, queue, cache service or LLM framework.

```text
frontend/
  src/app/                 visual app, employee/[id], hr, responsive styles
  src/components/          connected shell, map, HR, illustrations
  src/lib/                 API client, public types and local route planner
  public/                  Halyk logo
  next.config.ts           /backend rewrite
  Dockerfile
backend/
  app/api/                 HTTP routes and authorization dependencies
  app/schemas/             source, public, state and evidence models
  app/repositories/        file access and repository views
  app/services/            projection, gaps, eligibility, mutations, aggregates
  app/ai/                  full context contract, prompts, JSON adapter and output validator
  app/core/                config, identity and errors
  tests/
  Dockerfile
data/raw/                  original starter kit, read-only
data/fixtures/             original SHA-256 manifest
data/state/                ignored native-runtime state
docs/                      architecture, data model, plan and handoff
docker-compose.yml
```

See [architecture](docs/architecture.md), [data model](docs/data-model.md), and [implementation plan](docs/superpowers/plans/2026-09-23-career-quest-foundation.md).

## Configuration

Copy .env.example to .env only if changing Compose defaults. Compose reads .env; native Python reads the process environment (it does not automatically load .env).

| Variable | Purpose |
| --- | --- |
| DEV_IDENTITIES_JSON | Server-only token-to-principal mapping, employee or hr |
| NEXT_PUBLIC_API_URL | Browser API prefix, default `/backend`; embedded during frontend build |
| BACKEND_INTERNAL_URL | Next.js proxy destination: native default `http://127.0.0.1:8000`, Compose build `http://backend:8000` |
| FRONTEND_ORIGIN | Allowed frontend CORS origin when using a direct browser API URL |
| DATA_RAW_DIR | Native backend raw directory override |
| STATE_PATH | Native backend state file override |
| APPLICATION_DATE | Demo clock override, never before the 2026-10-01 snapshot |
| AI_PROVIDER, OPENAI_API_KEY, NVIDIA_API_KEY | Reserved, currently unused; keys must never be public variables |
| MAIL_ENCRYPTION_KEY | Server-only Fernet key for saved SMTP credentials; preserve across restarts |
| PUBLIC_APP_URL | Employee-facing cabinet URL used in emails |
| NOTIFICATION_WORKER_ENABLED, NOTIFICATION_POLL_SECONDS | Background preparation/delivery worker; default true / 2 seconds |

The default clock is the dataset snapshot, not the host date. Future scheduled sessions cannot be completed. Move APPLICATION_DATE forward to demonstrate later sessions, rebuild/restart the backend, and never move it backwards over recorded completions. Self-paced and existing assignments work immediately.

Keep provider keys and the identity mapping on the server. Do not put them in `NEXT_PUBLIC_*`, frontend source or committed environment files. The default proxy removes the need for a public backend URL; an explicit direct URL requires matching CORS configuration. Rebuild the production frontend after changing its URL configuration.

## Local development

Python 3.12+ and Node.js 22+:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

In another terminal, from the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open [the native frontend](http://127.0.0.1:3000). The default Next.js proxy reaches `http://127.0.0.1:8000`; no frontend environment file is required. Native default tokens are demo-employee, demo-active and demo-hr. To add imported employee identities, set DEV_IDENTITIES_JSON as shown in .env.example before starting Python. Application logic is independent of known employee IDs. Next.js reads frontend/.env.local when a URL override is needed.

## API

Email setup, workflow, recovery guarantees and notification endpoints: [notifications](docs/notifications.md). Delivery starts disabled. HR must connect a mailbox, configure employee addresses and enable it; automatic recommendations also require a configured AI client. Test emails are explicit HR actions.

All /api endpoints require Authorization: Bearer TOKEN.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | /health | Public readiness |
| GET | /api/session | Server-resolved role and employee ID for the current token |
| GET | /api/employees | Own summary for employees; all for HR |
| GET | /api/employees/{id} | Profile, projected skills and effective history |
| GET | /api/employees/{id}/trajectory | Next grade, goal, gaps and eligible candidates |
| GET | /api/employees/{id}/recommendations/context | Full linked context; own employee or HR access |
| POST | /api/employees/{id}/recommendations | Validated injected AI result; no_candidates without a model; 501 if provider missing |
| POST | /api/employees/{id}/activities/{event_id}/complete | Own activity only; HR cannot complete |
| GET | /api/hr/dashboard | HR-only gap, candidate-coverage and participation aggregates |
| POST | /api/dataset/import | HR-only multipart employees/history |
| GET | /api/market | Reward catalog; own ledger for employees, catalog-only access for HR |
| POST | /api/market/redeem | Employee-only persisted reward redemption with balance and retry checks |

Completion body:

```json
{"command_id":"00000000-0000-4000-8000-000000000001","source_record_id":null,"session_date":null}
```

Generate a UUID per intentional action and reuse the exact body after an uncertain response. The persisted receipt returns the original result on retry. Reusing a command ID with different content is 409. Completing the same non-recurring activity under another UUID is also rejected. Use source_record_id for an existing in_progress/overdue assignment; use session_date for a scheduled session.

Market redemption body:

```json
{"command_id":"00000000-0000-4000-8000-000000000002","reward_id":"book"}
```

Market applies the same retry principle. Each employee can redeem each reward once; insufficient balance and duplicate rewards return 409. Completion and redemption receipts persist in the same mutable overlay. The frontend retains operation IDs for retries during the current page session.

Errors use {error: {code, message, details}}. Statuses include 401, 403, 404, 409, 413, 422, 501 and 503. Private API responses are not cacheable. Import details include sanitized file/row/field locations (CSV header is row 1; employee array indices are zero-based), without echoing uploaded values.

## Dataset and imports

The starter kit contains 200 employees, 40 activities, 60 skills, 32 role/grade profiles and 2,743 history rows. Its synthetic data must remain within the hackathon; do not publish it elsewhere.

Import employees.json using the original meta/employees envelope and/or activity_history.csv with all original columns. In HR view select one or both files. API multipart field names are employees and history. Maximum total request size is 10 MiB including multipart overhead. Catalog replacement, ZIP uploads and filesystem-path imports are unsupported.

The whole prospective dataset is validated before a write. New IDs append; identical existing rows are no-ops; conflicting IDs or semantic duplicate participations reject the whole request. Imports and completions share one lock. Raw data is never edited.

The dataset README's no-repeat rule conflicts with real repeated annual mandatory compliance history. Original history is preserved. Distinct existing mandatory compliance assignments can be completed, and imported distinct zero-gain compliance participations are accepted. Voluntary events remain non-repeatable except EV_036 (the documented club).

## State, restart and reset

Native state lives in data/state/state.json. Compose state lives in its named career_quest_state volume. Normal docker compose down preserves it. Startup validates state and its raw-data fingerprint; invalid/mismatched state fails visibly rather than resetting.

For an intentional **disposable demo reset**, first stop the backend and back up the state file or Docker volume. Then remove only that demo state file (native), or explicitly remove this project's named state volume. This deletes imports, completions and Market redemptions, not data/raw. Do not use volume deletion for normal restarts. Multiple backend workers/processes sharing the file are unsupported.

## Tests and checks

Notification integration verification: all 175 backend tests passed, including fake SMTP, authorization, restart recovery and disk failure after mail acceptance. Frontend verification uses `npm run typecheck` and `npm run build`. Browser interaction and real mailbox delivery have not been verified. Commands are listed below.

```sh
# From repository root, with .venv activated:
python -m pytest backend/tests -q
cd frontend
npm run typecheck
npm run build
cd ..
docker compose config --quiet
```

Tests cover real loading and original hashes, gaps, assessment replay, caps/no-regression, eligibility/evidence, authorization, completion retries/restarts, atomic rollback, imports and HR counts. Mutation tests use temporary state; raw data remains untouched. The HR real-dataset calculation has a two-second regression budget; overloaded hosts can affect timing. Latest installed Starlette emits an httpx test-client deprecation warning, documented separately from failures.

## Current status and next work

Implemented: the deterministic foundation, authorized session/API, connected Halyk map and employee/HR UI, import/completion persistence, server-backed demonstration Market, same-origin Docker/native topology, complete linked LLM context, provider-independent prompt/JSON adapter and validated recommendation orchestration. The UI handles recommendation responses, evidence, hypotheses, questions and missing-provider errors.

Next: configure a live provider with the ten-second request budget, evaluate recommendation quality, and populate HR recommendation coverage. Current employees_without_recommendation is null; employees_without_candidate is a separate deterministic measure. The provider integration must set transport timeouts; the injected synchronous callable has no deadline enforcement by itself. Weekly pace is a local route filter and is not sent to the LLM. Offer enrollment and email preferences now have persisted write endpoints; external LMS registration, profile/goal editing and answers to AI clarification questions remain unimplemented. See [notification workflow and API handoff](docs/notifications.md).

Foundation handoff: [docs/handoff.md](docs/handoff.md). Current frontend/API mapping and integration limits: [docs/frontend-integration.md](docs/frontend-integration.md).

## Выбранный трек и кейс

- Трек: Halyk Bank
- Case 1: Career Quest — AI-навигатор развития сотрудника

## Authors

- [Zhassyn Zhalynuly](https://github.com/zzhassyn)
- [Danial Amangeldi](https://github.com/danial41-design)
- Nurislam Aldabergenuly
