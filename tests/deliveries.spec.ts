import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';
import { DeliveriesPage } from '../pages/deliveries.page';
import { LoginPage } from '../pages/login.page';

test.beforeEach(async ({ page }) => {
  const { BUSINESS_EMAIL, BUSINESS_PASSWORD } = process.env;
  if (!BUSINESS_EMAIL || !BUSINESS_PASSWORD) {
    throw new Error('Set BUSINESS_EMAIL and BUSINESS_PASSWORD in .env or in the environment.');
  }

  await new LoginPage(page).signIn(BUSINESS_EMAIL, BUSINESS_PASSWORD);
  await expect(new DeliveriesPage(page).formHeading).toBeVisible();
});

test('a business creates and publishes a delivery', async ({ page }) => {
  const deliveries = new DeliveriesPage(page);
  const address = `12 Herbert Macaulay Way, Yaba, Lagos (E2E ${randomUUID()})`;

  await deliveries.fillDelivery({
    pickup: { name: 'Ada Okafor', phone: '08012345678', address: '8 Allen Avenue, Ikeja, Lagos' },
    dropoff: { name: 'Tunde Bello', phone: '08087654321', address },
    description: 'Box of books',
    weightKg: 2,
  });
  await deliveries.submit();

  await expect(deliveries.successMessage).toBeVisible();
  await expect(deliveries.successMessage).toHaveText(/^Delivery del_[a-z0-9]+ created\. Fee ₦1,900\.00$/);
  const deliveryId = (await deliveries.successMessage.innerText()).split(' ')[1];
  const row = deliveries.rowForAddress(address);

  await expect(row.getByRole('cell', { name: deliveryId, exact: true })).toBeVisible();
  await expect(row.getByRole('cell', { name: '₦1,900.00', exact: true })).toBeVisible();
  await expect(row.getByTestId('delivery-status')).toHaveText('pending');
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
