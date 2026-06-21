# B&P House — Partners Backend

Placeholder for the partners platform backend. **No code yet** — this will be
built in a later stage to receive and store the onboarding submissions
(the section-built payload from `partners-frontend`) and to power the
classification and partner-portal work.

## Context
- The front end lives in the sibling directory `../partners-frontend` and is a
  fully independent Vite + React app (its own dependencies and assets).
- Until the backend exists, the front end stores submissions locally
  (`localStorage` + `window.__bnpLastSubmission`) and logs the payload.

## Intended scope (to be defined later)
- An endpoint to accept the onboarding payload.
- Persistence + the internal classification step.
- Auth for a future partner portal.
