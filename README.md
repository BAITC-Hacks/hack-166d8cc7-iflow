# Career Quest

Career Quest is an employee-development navigator for HackAlem AI, Case 1. This foundation loads the real starter kit, projects current skills, calculates next-grade gaps, lists eligible development activities, records completions and provides HR aggregates/import.

**AI recommendations are not implemented.** The recommendation endpoint returns HTTP 501. Candidates and structured evidence are ready for the next milestone; this is not yet a complete hackathon submission.

## Наше решение — Halyk Career Quest

**Трек: Halyk Bank. Кейс №1: Career Quest — AI-навигатор развития сотрудника.**
Команда IFlow создаёт персональную карту карьерного развития: сотрудник выбирает
цель, видит ближайшие полезные шаги и понимает, как каждый из них развивает навыки.
В одной истории соединяются обучение, практика, менторство и приятные награды.

### Какую задачу решаем

Каталог курсов сам по себе не объясняет сотруднику, с чего начать и что поможет
приблизиться к следующему грейду. HR нужны данные о дефицитах навыков и о том,
каким сотрудникам пока не удаётся предложить подходящее развитие.

Наш подход — связать профиль сотрудника, требования роли и доступные мероприятия
в понятный маршрут из **1–3 ближайших шагов**. Для каждого шага показываем,
почему он подходит, сколько времени займёт и какой навык поможет развить.

### Карта развития как главное пространство

Главный экран — игровая карта с районами навыков, которую исследует сотрудник. В локальном прототипе есть четыре района: **Холмы архитектуры, Долина
кода, Площадь диалога и Сад лидерства**. Для других ролей состав районов должен
формироваться по их профилю навыков.

- **Карьерная цель:** ориентир следующего грейда или выбранной роли.
- **Развилки:** выбор между обучением, практикой и встречами с менторами.
- **Доступные и будущие этапы:** например, практика проектирования сервиса
  открывается после архитектурного воркшопа.
- **Свой темп:** 1, 3 или 5 часов в неделю. Самостоятельные задания можно
  распределять по неделям, живые встречи должны помещаться в доступное время.
- **Прогресс:** завершённые активности меняют уровни навыков и дальнейший маршрут.

Игровой путь и обмен внутренних монет на полезные предложения вдохновлены
механикой Astana Hub. Мы адаптируем их под карьерные цели сотрудников Halyk
и зелёно-золотую визуальную стилистику банка.

### Где нужен ИИ

Планируем AI-навигатор, который помогает подобрать маршрут и объяснить его
человеческим языком. Сценарий: **«Хочу стать Senior, но на обучение есть только
час в неделю»** — система предлагает посильные шаги и объясняет компромиссы.

Рекомендации должны учитывать несколько факторов одновременно:

1. Дефицит и критичность навыков для следующего грейда или карьерной цели.
2. Текущую роль, грейд и предварительные требования мероприятия.
3. Историю участия: завершения, отказы, пропуски и обратную связь.
4. Формат, продолжительность, расписание и доступное время сотрудника.

Сначала backend определяет допустимых кандидатов и рассчитывает прогресс.
Затем планируем ранжирование и LLM-уточнение с объяснением минимум по трём
факторам. Результат проходит проверку: рекомендовать можно только реальные
мероприятия из каталога, соответствующие ограничениям. Уровни навыков и
начисления рассчитываются по правилам данных, а не генерируются моделью.

**Сейчас вызовы LLM не подключены:** опубликованный endpoint рекомендаций
возвращает HTTP 501. В отдельном локальном прототипе маршрут подбирается
правилами по цели, навыкам и времени; объяснения формируются по шаблонам.

### Halyk Market — награды за развитие

За добровольные активности сотрудник получает внутренние монеты и выбирает
награды: книги, мерч или билеты на профессиональные мероприятия. На карте видно,
сколько ещё монет нужно до следующей награды.

Монеты не повышают уровни навыков и не влияют на решение о повышении.
Обучение и менторство остаются бесплатными. За обязательные процессы награды
не начисляются. В прототипе Market — демонстрационный каталог; реальные
покупки, доставка и интеграция с коммерческим Halyk Market не подключены.

### Пример пользовательского пути

**Middle Backend Engineer → цель Senior → выбор темпа → ближайшие события →
завершение воркшопа → обновление навыка → открытие практики → награда в Market.**

Покрытие требований к навыкам показывает продвижение к цели, но не является
гарантией повышения. Сотрудник может изменить цель или темп и пересобрать
ближайший маршрут.

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
| Данные стартового набора, расчёт навыков и траектории, допустимые мероприятия | Опубликованы в текущей технической основе |
| FastAPI, разграничение employee/HR, импорт и сохранение завершений, HR-агрегаты | Опубликованы; подробнее в технических разделах ниже |
| Минимальный интерфейс сотрудника и HR, запуск через Docker Compose | Опубликованы |
| Новая игровая карта, темп обучения, анимации и Halyk Market | Отдельный локальный frontend-прототип на демо-данных; в этот push не включён и с backend ещё не интегрирован |
| AI-рекомендации с LLM и проверенными объяснениями | Следующий этап разработки |

Следующие шаги: объединить новый интерфейс с API и исходным каталогом,
подключить рекомендатель, затем проверить полный сценарий сотрудника и HR.
Инструкции ниже относятся к **уже опубликованной технической основе**.

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

For an immediate demo, use demo-active, open the employee, and complete Applied Statistics for Analysts or an existing assignment. Watch the skills and trajectory update. Switch to demo-hr and open HR view for aggregates/import.

Production authentication is outside this MVP. Backend authorization is enforced on every protected endpoint; entering a role header cannot grant access. Demo tokens are deliberately public and unsuitable for deployment. Replace core/auth.py identity verification before exposing this app to untrusted users. Compose binds host ports to loopback.

## Architecture and technology

Next.js App Router + TypeScript + Tailwind -> FastAPI + Pydantic -> deterministic services -> repositories -> immutable JSON/CSV and one mutable JSON overlay. One Uvicorn worker, one mutation lock, one atomic state replacement. No database, queue, cache service or LLM framework.

```text
frontend/
  src/app/                 home, employee/[id], hr
  src/components/          session, employee, HR and status UI
  src/lib/                 API client and public types
  Dockerfile
backend/
  app/api/                 HTTP routes and authorization dependencies
  app/schemas/             source, public, state and evidence models
  app/repositories/        file access and repository views
  app/services/            projection, gaps, eligibility, mutations, aggregates
  app/ai/                  disabled provider boundary and output validator
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
| NEXT_PUBLIC_API_URL | Browser-facing backend URL; embedded during frontend build |
| FRONTEND_ORIGIN | Allowed frontend CORS origin |
| DATA_RAW_DIR | Native backend raw directory override |
| STATE_PATH | Native backend state file override |
| APPLICATION_DATE | Demo clock override, never before the 2026-10-01 snapshot |
| AI_PROVIDER, OPENAI_API_KEY, NVIDIA_API_KEY | Reserved, currently unused; keys must never be public variables |

The default clock is the dataset snapshot, not the host date. Future scheduled sessions cannot be completed. Move APPLICATION_DATE forward to demonstrate later sessions, rebuild/restart the backend, and never move it backwards over recorded completions. Self-paced and existing assignments work immediately.

## Local development

Python 3.12+ and Node.js 22+:

```sh
python -m venv .venv
# Activate .venv using your shell.
python -m pip install -r backend/requirements-dev.txt
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Native default tokens are demo-employee and demo-hr. To use demo-active or imported identities, set DEV_IDENTITIES_JSON as shown in .env.example before starting Python. Configure any imported employee ID there; application logic is independent of known IDs. Next.js reads frontend/.env.local if a browser API URL override is needed.

## API

All /api endpoints require Authorization: Bearer TOKEN.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | /health | Public readiness |
| GET | /api/employees | Own summary for employees; all for HR |
| GET | /api/employees/{id} | Profile, projected skills and effective history |
| GET | /api/employees/{id}/trajectory | Next grade, goal, gaps and eligible candidates |
| POST | /api/employees/{id}/recommendations | Explicit 501, no fake AI result |
| POST | /api/employees/{id}/activities/{event_id}/complete | Own activity only; HR cannot complete |
| GET | /api/hr/dashboard | HR-only gap, candidate-coverage and participation aggregates |
| POST | /api/dataset/import | HR-only multipart employees/history |

Completion body:

```json
{"command_id":"00000000-0000-4000-8000-000000000001","source_record_id":null,"session_date":null}
```

Generate a UUID per intentional action and reuse the exact body after an uncertain response. The persisted receipt returns the original result on retry. Reusing a command ID with different content is 409. Completing the same non-recurring activity under another UUID is also rejected. Use source_record_id for an existing in_progress/overdue assignment; use session_date for a scheduled session.

Errors use {error: {code, message, details}}. Statuses include 401, 403, 404, 409, 413, 422, 501 and 503. Private API responses are not cacheable. Import details include sanitized file/row/field locations (CSV header is row 1; employee array indices are zero-based), without echoing uploaded values.

## Dataset and imports

The starter kit contains 200 employees, 40 activities, 60 skills, 32 role/grade profiles and 2,743 history rows. Its synthetic data must remain within the hackathon; do not publish it elsewhere.

Import employees.json using the original meta/employees envelope and/or activity_history.csv with all original columns. In HR view select one or both files. API multipart field names are employees and history. Maximum total request size is 10 MiB including multipart overhead. Catalog replacement, ZIP uploads and filesystem-path imports are unsupported.

The whole prospective dataset is validated before a write. New IDs append; identical existing rows are no-ops; conflicting IDs or semantic duplicate participations reject the whole request. Imports and completions share one lock. Raw data is never edited.

The dataset README's no-repeat rule conflicts with real repeated annual mandatory compliance history. Original history is preserved. Distinct existing mandatory compliance assignments can be completed, and imported distinct zero-gain compliance participations are accepted. Voluntary events remain non-repeatable except EV_036 (the documented club).

## State, restart and reset

Native state lives in data/state/state.json. Compose state lives in its named career_quest_state volume. Normal docker compose down preserves it. Startup validates state and its raw-data fingerprint; invalid/mismatched state fails visibly rather than resetting.

For an intentional **disposable demo reset**, first stop the backend and back up the state file or Docker volume. Then remove only that demo state file (native), or explicitly remove this project's named state volume. This deletes imports/completions, not data/raw. Do not use volume deletion for normal restarts. Multiple backend workers/processes sharing the file are unsupported.

## Tests and checks

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

Implemented: the deterministic foundation, authorized API, minimal employee/HR UI, import/completion persistence and Docker topology. No provider calls, scoring, fabricated explanations or optional gamification.

Next: multi-factor scoring -> LLM refinement -> validated 1–3 recommendations with evidence-backed explanations; then populate HR recommendation coverage. Current employees_without_recommendation is null, not a misleading zero; employees_without_candidate is a separate deterministic measure. Enforce the ten-second recommendation budget in that next milestone.

Verification results, known limits, final tree and next-agent instructions: [docs/handoff.md](docs/handoff.md).

## Выбранный трек и кейс
- Трек: Halyk Bank
- Case 1: Career Quest — AI-навигатор развития сотрудника

## Authors

- [Zhassyn Zhalynuly](https://github.com/zzhassyn)
- [Danial Amangeldi](https://github.com/danial41-design) (Backend/ML Developer)
- Nurislam Aldabergenuly
