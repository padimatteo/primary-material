# Coffee backend specification

Status: Draft for review  
Scope: Coffee recipe entry persistence and HTTP API. Frontend behavior and layout belong in a separate specification.

## Purpose and model

A **coffee entry** records one prepared coffee: the coffee and equipment used, the recipe settings, the date, and the resulting rating and notes. Repeated brews of the same coffee are separate entries. Roasters, products, and grinders are shared lookup records so differently cased or repeated input resolves to the same stored value. A product belongs to a roaster. All entries belong to the single Homebase installation. Authentication and sharing are outside this version.

The API lives under `/api/coffee/recipes`. The word `recipes` in the URL refers to these saved entries; there is no separate reusable recipe template in this version.

## Entry data

| Field | API type | Rules | Database representation |
| --- | --- | --- | --- |
| `id` | UUID string | Server generated; immutable | UUID primary key |
| `date` | ISO date, `YYYY-MM-DD` | Required; calendar date of the brew | `DATE` |
| `roaster` | string | Required; trim surrounding whitespace; 1–255 characters after trimming | Resolved through the entry's product to `roasters.name` |
| `product` | string | Required; trim surrounding whitespace; 1–255 characters after trimming | `coffee_entries.product_id` references `products.id` |
| `roast_level` | integer | Required; 1 through 5 | `SMALLINT` with check constraint |
| `recipe_type` | string enum | Required; `espresso`, `pour_over`, `drip`, or `french_press` | constrained text or database enum |
| `coffee_weight_g` | decimal number | Required; greater than 0; at most two decimal places | `NUMERIC(8,2)` with positive check |
| `brew_time_seconds` | integer | Required; greater than 0; measured duration | positive `INTEGER` |
| `total_yield_g` | decimal number | Required; greater than 0; at most two decimal places | `NUMERIC(8,2)` with positive check |
| `grind_setting` | decimal number | Required; at most two decimal places; may be zero or negative for grinder scales that use them | `NUMERIC(8,2)` |
| `grinder` | string | Required; trim surrounding whitespace; 1–255 characters after trimming | `coffee_entries.grinder_id` references `grinders.id` |
| `rating` | integer | Required; 1 through 5 | `SMALLINT` with check constraint |
| `notes` | string or `null` | Optional; at most 10,000 characters; empty string is stored as `null` | nullable `TEXT` |
| `created_at` | ISO timestamp | Server generated; UTC; read only | timestamp with time zone |
| `updated_at` | ISO timestamp | Server generated; UTC; changes on update; read only | timestamp with time zone |

Weights and grind settings are JSON numbers, but the backend must parse and validate them as decimal values, not binary floats. It must reject non-finite values and values that do not fit the database precision. No uniqueness constraint applies to coffee entries.

`brew_time_seconds` is the canonical API and storage value so duration sorting is numeric. The frontend will accept and display minutes:seconds, for example `2:30`, and convert that to `150` seconds. Seconds in the displayed value must be `00`–`59`; durations may exceed 59 minutes.

## Lookup tables and name resolution

| Table | Columns and constraints |
| --- | --- |
| `roasters` | `id` UUID primary key; `name` `VARCHAR(255)` not null; unique case-insensitive name |
| `products` | `id` UUID primary key; `roaster_id` UUID foreign key to `roasters.id` not null; `name` `VARCHAR(255)` not null; unique case-insensitive name **within one roaster** |
| `grinders` | `id` UUID primary key; `name` `VARCHAR(255)` not null; unique case-insensitive name |
| `coffee_entries` | `product_id` UUID foreign key to `products.id` not null; `grinder_id` UUID foreign key to `grinders.id` not null; remaining entry fields from the table above |

All three lookup names are 1–255 characters after trimming. The entry stores no separate `roaster_id`: its product determines the roaster, avoiding inconsistent roaster/product pairs. The API continues to accept and return the three names as strings; lookup UUIDs are internal to this version.

For each write, trim submitted names and match existing lookup rows without regard to case. Reuse a match and return its stored spelling. Otherwise create a new row using the submitted spelling. Resolve products by **both** roaster and product name, so two roasters may each have a product named `House Blend`. Perform lookup resolution and entry creation or update in one transaction. Database uniqueness constraints must also handle concurrent requests that submit the same new name; a race must resolve to the existing row rather than create duplicates or fail the request.

On an update, a supplied `product` is resolved under the entry's current roaster unless `roaster` is also supplied. If only `roaster` changes, resolve the entry's existing product name under the new roaster, creating that roaster/product pair if needed. A supplied `grinder` is resolved independently. Deleting an entry does not cascade to its lookup rows. Unreferenced lookup rows may be retained for later reuse, but are excluded from typeahead suggestions.

## Endpoints

All endpoints return JSON except a successful delete. Use the existing FastAPI `/api` prefix and tag these routes `coffee` in OpenAPI.

### `GET /api/coffee/recipes/{id}`

Returns one entry as the response shape below with status `200`. An unknown valid UUID returns `404`. A malformed UUID returns FastAPI's validation response, `422`.

### `GET /api/coffee/recipes`

Returns `200` with:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

`total` counts all records matching the filters before pagination. `limit` defaults to 20 and must be 1–100; `offset` defaults to 0 and must be nonnegative. An empty result is successful, including an offset beyond the last result.

Optional query parameters:

| Parameter | Behavior |
| --- | --- |
| `q` | Trimmed, case-insensitive substring search across `roaster`, `product`, `grinder`, and `notes`. Blank is equivalent to omitted. |
| `roaster`, `product`, `grinder` | Case-insensitive exact match, individually or together. |
| `recipe_type` | Exact enum match. |
| `roast_level`, `rating` | Exact integer match, 1–5. |
| `date_from`, `date_to` | Inclusive ISO date bounds; either may be supplied alone. `date_from` after `date_to` is invalid. |
| `sort_by` | One of `date`, `roaster`, `product`, `roast_level`, `recipe_type`, `coffee_weight_g`, `brew_time_seconds`, `total_yield_g`, `grind_setting`, `grinder`, `rating`, `created_at`. Default `date`. |
| `sort_dir` | `asc` or `desc`; default `desc`. |

Combine different filters with AND. Search text is treated literally, including `%` and `_`. Sorting always adds `id` as a final tie breaker so pagination is deterministic for unchanged data. Invalid query values return `422`.

### `GET /api/coffee/recipes/suggestions`

Supplies values for the three typeahead fields. Query parameters:

- `field` is required and must be `roaster`, `product`, or `grinder`.
- `q` is optional; trim it and match case-insensitive prefixes. Blank returns the first matching values.
- `limit` defaults to 10 and must be 1–20.
- `roaster` is required when `field=product` and invalid with the other fields. It scopes product suggestions to one case-insensitively matched roaster. An unknown roaster returns an empty list.

Return `200` with `{ "values": ["Example"] }`. Values come from lookup rows referenced by at least one current entry, using their canonical stored spelling, and are sorted alphabetically without regard to case. Suggestions are guidance only: users may submit a new roaster, product, or grinder. Invalid parameters return `422`. Register this route before `/{id}`.

### `POST /api/coffee/recipes`

Accepts all required editable fields and optional `notes`; rejects unknown fields and server-managed fields. Resolve or create the roaster, product under that roaster, and grinder as specified above. Returns `201`, the created entry, and a `Location` header pointing to `/api/coffee/recipes/{id}`. Invalid input returns `422` and creates nothing.

Example request:

```json
{
  "date": "2026-09-22",
  "roaster": "Example Roaster",
  "product": "House Blend",
  "roast_level": 3,
  "recipe_type": "pour_over",
  "coffee_weight_g": 18,
  "brew_time_seconds": 150,
  "total_yield_g": 300,
  "grind_setting": 18.5,
  "grinder": "Example Grinder",
  "rating": 4,
  "notes": "Balanced and sweet"
}
```

Example response body (also used by the single-entry endpoint and for items in a list):

```json
{
  "id": "6cd54c03-866c-4112-954b-27c37a428793",
  "date": "2026-09-22",
  "roaster": "Example Roaster",
  "product": "House Blend",
  "roast_level": 3,
  "recipe_type": "pour_over",
  "coffee_weight_g": 18,
  "brew_time_seconds": 150,
  "total_yield_g": 300,
  "grind_setting": 18.5,
  "grinder": "Example Grinder",
  "rating": 4,
  "notes": "Balanced and sweet",
  "created_at": "2026-09-22T14:00:00Z",
  "updated_at": "2026-09-22T14:00:00Z"
}
```

### `PUT /api/coffee/recipes/{id}`

Accepts **one or more editable fields** and updates only those supplied. This partial-update behavior is deliberate to support changing a rating or one recipe setting through the requested `PUT` endpoint. Omitted fields retain their values; `notes: null` clears notes. Resolve changed lookup names using the current or supplied roaster as described above. The request cannot modify `id`, `created_at`, or `updated_at`, and unknown fields are rejected. Apply the same field validation as creation. Return `200` with the complete updated entry; update `updated_at` only when an update succeeds. An empty object or invalid input returns `422`; an unknown valid UUID returns `404`.

### `DELETE /api/coffee/recipes/{id}`

Permanently deletes the entry and returns `204` with no body. An unknown valid UUID returns `404`; a malformed UUID returns `422`.

## Persistence and implementation constraints

- Add a schema migration for `roasters`, `products`, `grinders`, and `coffee_entries` rather than creating tables implicitly at application startup. Introduce migration tooling if needed; the scaffold has none yet.
- Validate at the API boundary and enforce important numeric bounds and enum values in the database. Use parameterized SQLAlchemy queries for filtering, suggestions, and sort fields chosen from a fixed allowlist.
- Enforce case-insensitive uniqueness with database indexes on normalized lookup names: roaster name, grinder name, and the combination of roaster ID and product name. Index entry foreign keys, default date ordering, and common exact filters (`recipe_type`, `rating`).
- Keep database sessions scoped to a request and roll back failed writes.

## Acceptance criteria

1. A valid entry can be created, fetched by ID, found in the list, partially updated, and deleted. After deletion, fetching it returns `404`.
2. Duplicate brews are allowed. Free-text typeahead fields accept values not yet present in the database and create the needed lookup rows. Case and surrounding whitespace variants reuse existing rows; identical product names at different roasters remain distinct.
3. List search, filters, sort direction, pagination, and total count work together; equal sort values have deterministic order.
4. Suggestions return canonical names referenced by current entries, require a roaster for product suggestions, and never prevent free-text submission. Deleting an entry does not leave an unreferenced name in suggestions.
5. Boundary and invalid cases return the specified errors: missing or blank required fields, lookup names over 255 characters, invalid enum values, out-of-range scales, nonpositive weights or duration, excessive decimal precision, invalid dates, unknown fields, and malformed IDs.
6. The migration applies to a new PostgreSQL database; API tests cover writes and reads against the migrated schema, including concurrent creation of the same lookup name.

## Decisions to confirm during review

- An entry represents one brew, with its recipe and rating together; reusable recipe templates are deferred.
- All listed fields except `notes` are required, including a rating at creation.
- The API uses seconds for time and partial-update semantics for `PUT`, as described above.
- Roaster, product, and grinder names are normalized through lookup tables while the public API continues to use strings. Products are unique within a roaster, and the product foreign key determines an entry's roaster.
