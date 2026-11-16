import { expect, test } from '@playwright/test';
import { DeliveriesPage } from '../pages/deliveries.page';
import { LoginPage } from '../pages/login.page';
import { createDeliveryData } from './utils/dataFactory/delivery-data.factory';

const { BUSINESS_EMAIL, BUSINESS_PASSWORD,  COURIER_EMAIL, COURIER_PASSWORD } = process.env;
if (!BUSINESS_EMAIL || !BUSINESS_PASSWORD || !COURIER_EMAIL || !COURIER_PASSWORD) {
  throw new Error('Set all required environment variables in .env');
}

test.beforeEach(async ({ page }) => {
  await new LoginPage(page).login(BUSINESS_EMAIL, BUSINESS_PASSWORD);
  await expect(new DeliveriesPage(page).formHeading).toBeVisible();
});

async function createPublishedDelivery(deliveries: DeliveriesPage) {
  const data = createDeliveryData();
  await deliveries.fillDelivery(data);
  await deliveries.submit();

  await expect(deliveries.successMessage).toBeVisible();
  await expect(deliveries.successMessage).toHaveText(/^Delivery del_[a-z0-9]+ created\. Fee ₦/);
  const id = (await deliveries.successMessage.innerText()).split(' ')[1];
  const row = deliveries.rowForId(id);
  await expect(row.getByTestId('delivery-status')).toHaveText('pending');

  return { id, row, data };
}

test('a business creates and publishes a delivery', async ({ page }) => {
  const deliveries = new DeliveriesPage(page);
  const { id, row, data } = await createPublishedDelivery(deliveries);
  const amount = (1500 + 200 * data.weightKg).toLocaleString('en-NG', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const fee = `₦${amount}`;

  await expect(deliveries.successMessage).toHaveText(`Delivery ${id} created. Fee ${fee}`);
  await expect(row.getByRole('cell', { name: data.dropoff.address, exact: true })).toBeVisible();
  await expect(row.getByRole('cell', { name: fee, exact: true })).toBeVisible();
});

test('the dashboard shows assigned after a courier accepts the delivery', async ({ page, request }) => {
  const login = await request.post('/api/v1/auth/login', {
    data: { email: COURIER_EMAIL, password: COURIER_PASSWORD },
  });
  expect(login.ok(), `Courier login returned HTTP ${login.status()}`).toBe(true);
  const { token, user } = await login.json();
  expect(user.role).toBe('courier');

  const deliveries = new DeliveriesPage(page);
  const { id, row } = await createPublishedDelivery(deliveries);
  const headers = { Authorization: `Bearer ${token}` };
  const courierDelivery = `/api/v1/courier/deliveries/${id}`;
  const acceptance = await request.post(`${courierDelivery}/accept`, { headers });
  expect(acceptance.ok(), `Courier acceptance returned HTTP ${acceptance.status()}`).toBe(true);

  try {
    // The dashboard refreshes periodically. Wait for the status on this exact row.
    await expect(row.getByTestId('delivery-status')).toHaveText('assigned');
  } finally {
    const cancellation = await request.post(`${courierDelivery}/cancel`, { headers });
    expect(cancellation.ok(), `Test delivery cleanup returned HTTP ${cancellation.status()}`).toBe(true);
  }
});

test('an empty delivery shows a validation error for every required field', async ({ page }) => {
  const deliveries = new DeliveriesPage(page);

  await deliveries.submit();

  const errors = {
    'pickup-name': 'Pickup name is required',
    'pickup-phone': 'Pickup phone is required',
    'pickup-address': 'Pickup address is required',
    'dropoff-name': 'Drop-off name is required',
    'dropoff-phone': 'Drop-off phone is required',
    'dropoff-address': 'Drop-off address is required',
    'package-description': 'Package description is required',
    'package-weight': 'Weight is required',
  };

  for (const [field, message] of Object.entries(errors)) {
    await expect(deliveries.fieldError(field)).toBeVisible();
    await expect(deliveries.fieldError(field)).toHaveText(message);
  }

  await expect(deliveries.successMessage).toBeHidden();
});
