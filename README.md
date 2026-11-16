# Routag QA Assessment

This submission covers the Routag delivery journey, business wallet behavior, and dashboard validation using the supplied assessment sandbox.

| Task | Deliverable |
| --- | --- |
| A | [Manual test cases](Task%20A%20-%20test-cases.xlsx) |
| B | [API automation with Python and pytest](Task%20B%20-%20api-tests/README.md) |
| C | [Dashboard automation with Playwright and TypeScript](Task%20C%20-%20ui-tests/README.md) |
| E | [QA reasoning answers](Task%20E%20-%20answers.md) |

## Quick start

Run these commands in PowerShell. You’ll need Docker or the supplied sandbox source, Python 3.14 for the API suite, and Node.js 22 or later for the UI suite. First-time image, dependency, and browser downloads may take longer than five minutes.

### Start the sandbox

In a separate terminal, run the command below and leave the sandbox running while you test.

```powershell
docker run --rm -p 4000:4000 ghcr.io/vastrack-tech/qa-sandbox:1.0
```

If using the supplied sandbox source, run `npm install` and `npm start` from its `sandbox/` directory. The dashboard is at [localhost:4000](http://localhost:4000), and the API docs are at [localhost:4000/docs](http://localhost:4000/docs).

### Run the API tests

From the submission root:

```powershell
Set-Location 'Task B - api-tests'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env.qa
```

In `.env.qa`, set `BASE_URL=http://localhost:4000/api/v1` and replace the email and password placeholders for `BUSINESS1`, `BUSINESS2`, `COURIER1`, and `COURIER2` with the four seeded accounts from the assessment. Run:

```powershell
$env:ENV = 'qa'
.\.venv\Scripts\python.exe -m pytest
```

The suite covers quotes, delivery status and tracking, wallet holds and settlement, cancellation, repeated actions, cross-account access, and webhook event logging.

### Run the UI tests

From the submission root in another terminal:

```powershell
Set-Location 'Task C - ui-tests'
npm.cmd ci
npx.cmd playwright install chromium
Copy-Item .env.example .env
```

In `.env`, set `BASE_URL=http://localhost:4000` and fill in `BUSINESS_EMAIL`, `BUSINESS_PASSWORD`, `COURIER_EMAIL`, and `COURIER_PASSWORD` using one seeded business and one seeded courier account. Run:

```powershell
npm.cmd test -- --project=chromium
```

For all configured browsers, run `npx.cmd playwright install` followed by `npm.cmd test`.

The UI suite checks successful delivery creation and publication, all eight required-field messages, and the dashboard transition from `pending` to `assigned` after a courier accepts the delivery through the API. Page objects handle dashboard interactions, and Faker generates the delivery data.

Keep populated `.env.qa` and `.env` files local. The committed example files list the required variables.

## Assumptions

- Start with clean sandbox data and run the suites one at a time. The API suite compares wallet balances before and after delivery actions, and the UI suite creates deliveries on the seeded accounts. Restart the sandbox to restore seeded data.
- The UI bonus test leaves the delivery assigned and its fee held. The selected business needs up to ₦11,500 available to cover the generated delivery fee.
- The API webhook check verifies the sandbox event log. Verifying receipt and payloads requires a webhook receiver.

## With more time

- Send concurrent acceptance and completion requests and reconcile the wallet transactions to confirm that each delivery produces one hold, one charge, and one courier payout.
- Use a local webhook receiver to verify the event payload and observe what happens when the receiver is temporarily unavailable.

## AI assistance and verification

AI helped draft the documentation.
