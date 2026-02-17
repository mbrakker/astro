# Reuse Extraction Audit and Standalone Service Plan

## Current state (evidence)

The project already has a partial separation between generators (`gen_*`), services (`service_*`), and orchestration (`script_pipeline.py`), but responsibilities are still mixed in multiple places:

- Orchestration logic, retries, publication state updates, and content-type branching are centralized in one large pipeline script.
- Generators still perform direct external I/O in several cases (for example HTTP requests and RSS fetching in generator modules).
- Service modules contain business-domain behavior (prompt decisions, retries, content heuristics) instead of remaining pure I/O adapters.
- Most services are tightly coupled to absolute paths under `/opt/astro_bot/*`, reducing portability.

## High-value extraction candidates (reusable library modules)

### 1) `llm_text_service` library module
**Extract from:**
- `src/service_text.py`
- `src/service_openai_logger.py`
- `src/service_prompt_loader.py`

**Why reusable:**
- Prompt loading, prompt rendering, model invocation, and usage logging are cross-project concerns.

**Current extraction scope:**
- Keep OpenAI access consolidated in one service module.
- Keep prompt loading/rendering/version logging behind the existing prompt service entrypoint.
- Keep usage accounting in the same OpenAI service module via internal helper functions.

### 2) `image_generation_service` library module
**Extract from:**
- `src/service_image.py`

**Why reusable:**
- Prompt-to-image generation, caching, and downloading assets are generic for many projects.

**Current extraction scope:**
- Keep provider access consolidated in one image service module.
- Move prompt selection out of the service and into generator/prompt service layers.
- Keep storage integration behind one service contract.

### 3) `topic_repository_service` / `content_repository_service`
**Extract from:**
- `src/service_topic_loader.py`
- `src/service_history_logger.py`
- `src/service_duplicate_topic_check.py`
- `src/core/content_service.py`

**Why reusable:**
- CRUD for scheduled content, publication ledger, and duplicate checks are reusable in any publishing workflow.

**Current extraction scope:**
- Keep repository access consolidated per storage system.
- Ensure repository methods return typed contracts only.
- Remove CLI parsing from service modules.

### 4) `messaging_delivery_service` library module
**Extract from:**
- `src/service_telegram_sender.py`
- `src/service_notifier.py`
- `src/service_channels.py`

**Why reusable:**
- Channel resolution + bot send + owner alerting is a common integration pattern.

**Current extraction scope:**
- Keep Telegram provider access consolidated in one service module.
- Keep channel resolution and notifications as explicit service contracts without role mixing.

### 5) `news_ingestion_service` library module
**Extract from (currently inside generator):**
- `src/gen_mystic.py`

**Why reusable:**
- RSS parsing, keyword filtering, html cleaning, image harvesting can serve any news pipeline.

**Current extraction scope:**
- Move all network/feed parsing out of generators and into one ingestion service module.
- Keep generator responsibility limited to domain transformation and validation.

### 6) `astronomy_snapshot_service` library module
**Extract from:**
- `src/service_stellarium.py`

**Why reusable:**
- Browser-driven astronomy snapshots can be reused in educational/media apps.

**Current extraction scope:**
- Keep browser-driven external I/O in one astronomy snapshot service module.
- Keep deterministic URL composition in utilities.
- Keep output storage behind one service contract.

## Modules that should remain domain-specific (not primary extraction targets)

- `src/service_tarot.py`, `src/service_day_context.py`, `src/service_zodiac_archetype.py`, `src/service_energy_personalization.py`: useful but astrology-domain specific and less universal.
- `src/gen_*` modules for specific content types should remain project generators, but should consume extracted reusable services.

## Mandatory changes to make services universal and standalone

1. **Introduce strict contracts package (`src/contracts/`)**
   - Every service input/output must be a versioned dataclass.
   - Add validation on inbound/outbound data.

2. **Remove hardcoded absolute paths**
   - Replace `/opt/astro_bot/...` constants with configuration object + env overrides.
   - Inject all paths and credentials from config provider.

3. **Refactor by role boundaries**
   - Services: external I/O only.
   - Generators: business logic only.
   - Orchestrator: run order/retries/status transitions only.

4. **Create provider interfaces for portability**
   - `LLMProvider`, `ImageProvider`, `MessagingProvider`, `TopicRepository`, `ArtifactStore`.
   - Default implementations for current stack; alternative adapters per project.
   - Preserve one-service-per-external-system module boundaries.

5. **Adopt typed error taxonomy**
   - Base `AppError` with `code`, `retryable`, `severity`, `context`.
   - Retries only in orchestrator based on error type.

6. **Add structured event logging**
   - JSON logs with `run_id`, `task_id`, `span_id`, `module`, `role`.
   - Sanitize secrets/PII in all events.

7. **Decouple prompts from monolithic YAML usage**
   - Keep per-use-case prompt namespaces in files.
   - Add prompt hash/version to every LLM call log.

8. **Package extracted modules as installable library**
   - Build `astro_services_lib/` with semantic versioning.
   - Keep current project as composition layer consuming the library.

9. **Testing required for library readiness**
   - contracts: serialization + schema snapshots
   - services: integration tests with sandbox fixtures
   - generators: unit tests with mocked services
   - orchestrator: pipeline idempotency + retry tests

## Recommended migration sequence

1. Extract `llm_text_service` + prompt service first (largest cross-cutting dependency).
2. Extract `topic_repository_service` and remove DB access from generators/scripts.
3. Extract messaging + notification services.
4. Extract image generation service.
5. Move RSS ingestion from generator to dedicated service.
6. Finalize by introducing interfaces and packaging as shared library.
