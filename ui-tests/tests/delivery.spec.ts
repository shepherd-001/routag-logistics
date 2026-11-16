import { expect, test } from '@playwright/test';
import { CourierDeliveryApi } from '../api_clients/courier-delivery.api';
import { AuthApi } from '../api_clients/auth.api';
import { DeliveryPage } from '../pages/delivery.page';
import { LoginPage } from '../pages/login.page';
import { DeliveryDataFactory } from '../utils/dataFactory/delivery-data.factory';

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value?.trim()) {
    throw new Error('Missing environment variable ' + name + '. Set it in .env.');
  }
  return value;
}

test.beforeEach(async ({ page }) => {
  await new LoginPage(page).login(requiredEnv('BUSINESS_EMAIL'), requiredEnv('BUSINESS_PASSWORD'));
  await expect(new DeliveryPage(page).formHeading).toBeVisible();
});


test('a business creates and publishes a delivery', async ({ page }) => {
  const deliveryPage = new DeliveryPage(page);
  const delivery_data = DeliveryDataFactory.createDeliveryData();
  await deliveryPage.createDelivery(delivery_data);

  const id = await deliveryPage.readCreatedDeliveryId();
  const row = deliveryPage.rowForId(id);
  await expect(deliveryPage.statusOf(id)).toHaveText('pending');

  const amount = (1500 + 200 * delivery_data.weightKg).toLocaleString('en-NG', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2, 
  });
  const fee = `₦${amount}`;

  await expect(deliveryPage.successMessage).toHaveText(`Delivery ${id} created. Fee ${fee}`);
  await expect(row.getByRole('cell', { name: delivery_data.dropoff.address, exact: true })).toBeVisible();
  await expect(row.getByRole('cell', { name: fee, exact: true })).toBeVisible();
});


test('an empty delivery shows a validation error for every required field', async ({ page }) => {
  const deliveryPage = new DeliveryPage(page);

  await deliveryPage.submit();

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
    await expect(deliveryPage.fieldError(field)).toBeVisible();
    await expect(deliveryPage.fieldError(field)).toHaveText(message);
  }

  await expect(deliveryPage.successMessage).toBeHidden();
});

test('the dashboard shows assigned after a courier accepts the delivery', async ({ page, request }) => {
  const courierApi = new CourierDeliveryApi(request);
  const auth = new AuthApi(request);
  const login = await auth.login(requiredEnv('COURIER_EMAIL'), requiredEnv('COURIER_PASSWORD'));
  expect(login.ok(), `Courier login returned HTTP ${login.status()}`).toBe(true);
  const { token, user } = await login.json();
  expect(user.role).toBe('courier');

  const deliveryPage = new DeliveryPage(page);
  await deliveryPage.createDelivery(DeliveryDataFactory.createDeliveryData());
  const id = await deliveryPage.readCreatedDeliveryId();
  const status = deliveryPage.statusOf(id);
  await expect(status).toHaveText('pending');

  const acceptance = await courierApi.acceptDelivery(id, token);
  expect(acceptance.ok(), `Courier acceptance returned HTTP ${acceptance.status()}`).toBe(true);
  await expect(status).toHaveText('assigned');
});
