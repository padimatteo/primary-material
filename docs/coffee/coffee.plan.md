# Coffee backend implementation plan

Status: Steps 1–5 complete; step 6 pending

Source of truth: [coffee.spec.md](coffee.spec.md)  
Scope: Database, FastAPI endpoints, backend tests, and setup documentation. The Coffee page UI is a later phase with its own specification.

## Current progress

Database foundations, models and schemas, transactional lookup resolution, the five recipe endpoints, and typeahead suggestions are complete. The remaining backend integration tests and developer instructions in step 6 are pending. The existing `/api/hello` and `/api/health` endpoints must keep working.

## Implementation sequence

### 1. Add database foundations and migration tooling

- [x] Add Alembic to `backend/pyproject.toml` and update `backend/uv.lock`.
- [x] Define a shared SQLAlchemy declarative base and a request-scoped `Session` dependency in `backend/app/database.py`. Keep the current engine and health check compatible.
- [x] Configure Alembic in `backend/alembic.ini` and `backend/alembic/` to use `DATABASE_URL` and the model metadata. Do not create tables from the application startup path.
- [x] Add an initial migration for `roasters`, `products`, `grinders`, and `coffee_entries`, including UUID primary keys, foreign keys, numeric and enum/check constraints, timestamps, and the indexes in the spec.
- [x] Use case-insensitive unique indexes on `lower(name)` for roasters and grinders, and on `(roaster_id, lower(name))` for products. Store trimmed names so the index and API matching use the same normalization rule.
- [x] Store `product_id` and `grinder_id` on `coffee_entries`. Derive the roaster through `products.roaster_id`; do not add `coffee_entries.roaster_id`.

**Checkpoint:** The migration upgrades an empty PostgreSQL database and downgrades cleanly. Inspect the resulting constraints and indexes, including the product-to-roaster relationship.

### 2. Define models and API schemas

- [x] Add SQLAlchemy models for the four tables, with relationships that load `entry.product.roaster` and `entry.grinder` for responses and list queries.
- [x] Add Pydantic create, partial update, response, list, and suggestions schemas under a coffee backend module such as `backend/app/coffee/`.
- [x] Enforce the spec's required fields, enum choices, scales, positive values, decimal precision and finite values, 255-character trimmed lookup names, and 10,000-character notes limit. Reject unknown request fields and server-owned fields.
- [x] Keep `brew_time_seconds` as a positive integer. Serialize lookup **names** and numeric values in the public response; lookup IDs remain internal.
- [x] Give the partial update schema a validator that rejects an empty object while distinguishing an omitted field from `notes: null`.

**Checkpoint:** Schema-level tests cover accepted boundary values and rejected invalid values before route logic is added.

### 3. Implement transactional lookup resolution and entry writes

- [x] Add one service or repository path that trims and resolves a roaster, its product, and a grinder by case-insensitive name, creating a row when absent.
- [x] Resolve product names within their roaster. Reuse canonical stored spelling on case-only matches. Use PostgreSQL uniqueness plus conflict-safe insertion/reselection so concurrent requests for a new name converge on one row.
- [x] Make lookup resolution and entry creation or update one transaction. Roll back the entire write on validation or database failure; never leave lookup rows from a failed entry write.
- [x] On update, handle `product` under the current roaster, `roaster` plus `product` together, and `roaster` alone by resolving the existing product name under the new roaster. Handle grinder changes independently.
- [x] Preserve `created_at` and update `updated_at` on successful updates. Delete only the entry; retain lookup rows for reuse.

**Checkpoint:** Service tests show that repeated names share lookup rows, the same product name under different roasters remains distinct, and a roaster-only update selects or creates the correct product pair.

### 4. Add the five recipe endpoints

- [x] Add a coffee router and include it under `/api/coffee/recipes` in `backend/app/main.py`, leaving general routes intact. Tag it `coffee` in OpenAPI.
- [x] Implement `POST /` with `201`, a complete response, and a `Location` header; `GET /{id}` with `200` or `404`; partial `PUT /{id}` with `200` or `404`; and `DELETE /{id}` with `204` or `404`.
- [x] Use UUID path parameters so malformed IDs produce `422`. Return `422` for invalid bodies and query parameters.
- [x] Implement `GET /` with the specified `items`, `total`, `limit`, and `offset` envelope. Join product, roaster, and grinder where needed. Apply filters together, count before pagination, and sort through a fixed field allowlist with `id` as the final tie breaker.
- [x] Treat `q` as a literal case-insensitive substring across roaster, product, grinder, and notes; escape SQL wildcard characters. Use case-insensitive exact matching for the three name filters.

**Checkpoint:** Every CRUD endpoint and the combined list query match the status codes and response shapes in the spec.

### 5. Add typeahead suggestions

- [x] Register `GET /suggestions` before `GET /{id}`.
- [x] Support `field=roaster|product|grinder`, optional prefix `q`, and the specified limit. Require `roaster` for product suggestions and reject it for the other fields.
- [x] Query only lookup rows referenced by at least one current entry. Return canonical names, case-insensitively sorted, in `{ "values": [...] }`.
- [x] Ensure deleted entries no longer cause otherwise unreferenced names to appear; an unknown roaster returns an empty product list.

**Checkpoint:** Suggestions are useful for existing names but do not restrict entry creation to suggested values.

### 6. Add integration tests and developer instructions

- [ ] Add tests under `backend/tests/` that run against a dedicated PostgreSQL test database migrated from scratch. Never point destructive test setup at the normal `homebase` database. Provide a clear test database configuration and cleanup fixture.
- [ ] Cover the full create → get → list → partial update → delete flow; validation and `404`/`422` behavior; lookup deduplication; product scoping; suggestions; combined search/filter/sort/pagination; stable ties; and `total` before pagination.
- [ ] Add a concurrent-create test using independent database sessions or clients to verify the unique-name race is handled without duplicate rows or a failed request.
- [ ] Update `backend/README.md` or the root `README.md` with migration and backend test commands, including how to create/configure the test database.
- [ ] Run `uv run alembic upgrade head`, `uv run pytest`, and `uv run ruff check .` from `backend/`. Re-run the existing hello and health checks. Record any environment prerequisite that prevents a check.

## Completion criteria

The backend is done when all acceptance criteria in [coffee.spec.md](coffee.spec.md) pass against a migrated PostgreSQL database, the existing endpoints still pass, and the API's OpenAPI schema accurately describes the coffee routes. Stop before building the frontend; use the verified API contract to write its separate spec.
