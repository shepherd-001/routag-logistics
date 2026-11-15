# Routag dashboard UI tests

Playwright and TypeScript tests for Task C of the Vastrack QA assessment. Page objects in `pages/` handle login and the delivery form. Tests and assertions live in `tests/`.

## Run locally

Use Node.js 22 or newer and start the assessment sandbox. Its dashboard defaults to http://localhost:4000.

```powershell
npm ci
npx playwright install chromium
Copy-Item .env.example .env
```

Set `BUSINESS_EMAIL` and `BUSINESS_PASSWORD` in `.env` using a seeded business account from the assessment. Set `BASE_URL` if the sandbox runs at a different address. You can also set these variables in your shell.

```powershell
npm test
```

Use `npm run test:headed` to watch the browser. Failure screenshots and traces are saved in `test-results/`. Traces can contain sandbox login and session data, so review them before sharing.

## Coverage and assumptions

- A valid submission shows a success message and lists the same delivery ID and drop-off address with a fee of ₦1,900.00 for 2 kg and a `pending` status. The sandbox's submit button creates and publishes the delivery.
- An empty submission shows the eight field-level validation messages and shows no success confirmation.
- Each test logs in through the UI in a fresh browser context. The successful test uses a unique address and leaves its delivery in the sandbox.
- With more time I would add a courier acceptance test and verify that the dashboard updates to `assigned`.

## AI assistance

Codex helped author this project. Both scenarios were run in Chromium against the local assessment sandbox and passed.
