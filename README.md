# Routag dashboard UI tests

Playwright and TypeScript tests for Task C of the Vastrack QA assessment. Page objects in `pages/` handle login and the delivery form. Tests and assertions live in `tests/`.

## Run locally

Use Node.js 22 or newer and start the assessment sandbox. Its dashboard defaults to http://localhost:4000.

```powershell
npm ci
npx playwright install
Copy-Item .env.example .env
```

Set `BUSINESS_EMAIL` and `BUSINESS_PASSWORD` in `.env` using a seeded business account from the assessment. Set `COURIER_EMAIL` and `COURIER_PASSWORD` using a seeded courier account for the bonus test. The bonus test needs sufficient available business wallet funds for a fee of up to ₦2,500. Set `BASE_URL` if the sandbox runs at a different address. You can also set these variables in your shell.

```powershell
npm test
```

Use `npm run test:headed` to watch the browser. Failure screenshots and traces are saved in `test-results/`. Traces can contain sandbox login and session data, so review them before sharing.

## Coverage and assumptions

- A valid submission shows a success message and lists the same delivery ID and drop-off address with the expected fee for the generated weight and a `pending` status. The sandbox's submit button creates and publishes the delivery.
- An empty submission shows the eight field-level validation messages and shows no success confirmation.
- Each test logs in through the UI in a fresh browser context. Faker generates contacts, addresses, and package details for each valid delivery. The creation test leaves its delivery in the sandbox.
- The bonus test creates its own delivery, accepts it through the courier API, and verifies that the same dashboard row changes from `pending` to `assigned`. It then cancels the delivery to release the wallet hold.

## AI assistance

AI helped structure this README and implement the Faker data generator and courier acceptance test.

Verification against the local sandbox passed for all three scenarios in Chromium, Firefox, and WebKit (9 tests total).
