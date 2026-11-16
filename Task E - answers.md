# Task E — QA Reasoning

## 1. A release is two days away and you have one day of testing time. How do you decide what to test?

I’d review what changed with the developers and product owner, then prioritize by customer impact and likelihood of failure. For Routag, I’d start with a smoke test of the full delivery journey, from quote and creation through courier acceptance, pickup, and delivery. In my sandbox testing, a courier could mark an accepted package as delivered before recording pickup. I’d retest that sequence because it can trigger a payout while the package is still awaiting pickup. I’d spend most of the remaining time on wallet holds, payout, and cancellation because mistakes there can cost businesses or couriers money. I’d also check that one business cannot access another’s deliveries.

I’d run existing automation early and use the results to guide focused manual testing. I’d reserve time to retest fixes and give the release owner a clear summary of what passed, which defects remain open, and which areas I couldn’t cover.

## 2. How would you test the wallet so a business is never debited twice for one delivery?

I’d start with a known wallet balance and record the available balance, held amount, and transaction entries for one delivery. On acceptance, I’d verify that exactly one fee moves from available funds to held funds. On completion, I’d verify that the hold clears, the business’s total funds decrease by exactly one fee, and the courier receives one payout.

I’d repeat the acceptance and completion requests, and simulate a client timeout after the server processes a request so I can test what happens when the client retries. After each attempt, I’d reconcile the balances and transaction entries against the delivery ID. A response code alone can miss an extra debit. I’d also test cancellation after acceptance and verify that it releases the hold exactly once, even if the cancellation request is retried.

## 3. How would you put your automated tests into a CI/CD pipeline?

I’d run the automated tests against a fresh sandbox in CI. The pipeline would install dependencies from the lockfile, start the sandbox, wait for it to respond, and supply the base URL and test credentials through environment variables. I’d give each CI job its own sandbox so parallel runs can’t interfere with one another’s wallet balances or deliveries.

On pull requests, I’d run the API suite and Playwright tests in Chromium and require them to pass before merging. I’d run Firefox and WebKit nightly and before releases. When a test fails, I’d publish the test report and retain screenshots or traces with restricted access, since traces can contain session data. I’d investigate flaky failures before making the affected test a release gate.