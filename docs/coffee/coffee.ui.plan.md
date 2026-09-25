# Coffee UI implementation plan

Status: Implemented

## Summary

Build the approved New Recipe form at `/coffee/new` and a recent-recipes page at `/coffee`.

## Implementation

- Add Material UI, Emotion, and declarative React Router. Establish a shared light theme: forest green `#284e3b` primary, clay `#a65d42` secondary, paper `#f5f1e8` background, sage `#dce5d8` highlights, ink `#203027` text, and `#dcd7cb` borders. Use Newsreader headings and DM Sans body text; apply the theme to the existing home page.
- Build the form to match the approved wireframe, including the **New Recipe** heading and **Lighter ↔ Darker** roast guide. Default only the date to today. Use free-text autocomplete for roaster, product, and grinder; toggle controls for roast level and recipe type; and a five-star rating control.
- Add the pending suggestions endpoint from [coffee.spec.md](coffee.spec.md). Scope product suggestions to the entered roaster, debounce requests, and keep new names valid even when no suggestion matches.
- Validate the form, convert `m:ss` to API seconds, and POST to `/api/coffee/recipes`. Preserve entered values on errors. On success, navigate to `/coffee` and show confirmation; Cancel also returns to `/coffee`.
- Show the latest 20 recipes on `/coffee`, sorted by date descending, with a **New Recipe** action and empty, loading, and error states.

## Verification

- Test form validation, suggestions, time conversion, save success and failure, navigation, and recent-recipes states.
- Test suggestion endpoint scoping and filtering against the dedicated backend test database.
- Run frontend build and lint, backend tests and lint, and check desktop and narrow layouts plus keyboard access.

## Assumptions

- Values in the wireframe are examples, not defaults.
- Editing, deletion, detail pages, and advanced list controls are outside this first UI release.
- The existing create and list API contracts stay unchanged; suggestions are the only added endpoint.
