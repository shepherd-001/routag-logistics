# Routag API tests

This repository contains the Python/pytest API suite for the Routag delivery and wallet journey.

## Run the tests locally

Use Python 3.14 and a running assessment sandbox. The commands below use PowerShell. Initial image and dependency
downloads may take longer than five minutes.

### 1. Start the assessment sandbox

Run this in a separate terminal and leave it running while the tests execute.

```powershell
docker run --rm -p 4000:4000 ghcr.io/vastrack-tech/qa-sandbox:1.0
```

If you have the assessment source, you can also use Node.js 18 or later and run `npm install` and `npm start` from its
`sandbox/` directory.

### 2. Run the API tests

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env.qa
```

In `.env.qa`, set `BASE_URL` to `http://localhost:4000/api/v1`. Fill the email and password fields for `BUSINESS1`,
`BUSINESS2`, `COURIER1`, and `COURIER2` with the four seeded accounts from the assessment. Then run:

```powershell
$env:ENV = 'qa'
.\.venv\Scripts\python.exe -m pytest
```

The API suite covers quote validation, delivery status and tracking, wallet holds and settlement, cancellation, repeated
actions, cross-account access, and webhook event logging.

Keep the populated `.env.qa` file local.

## Assumptions

- Run the suite against the supplied sandbox. Start with clean sandbox data and avoid concurrent activity on the seeded
  accounts because the tests compare wallet balances before and after delivery actions. Restarting the sandbox restores
  the seeded data.
- The API webhook test checks the sandbox's event log. A separate receiver would be needed to verify delivery to an
  external endpoint.

## With more time

- Study the requirement more and perform more exploratory test
- Send concurrent completion requests and verify the wallet ledger records exactly one business charge and one courier
  credit.
- Point the sandbox webhook at a local receiver and verify the event payload and delivery behavior.

## AI assistance and verification

AI generated the layout and ideas for this README.
