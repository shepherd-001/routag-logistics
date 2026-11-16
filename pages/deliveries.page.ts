import type { Page } from '@playwright/test';

export type Delivery = {
  pickup: { name: string; phone: string; address: string };
  dropoff: { name: string; phone: string; address: string };
  description: string;
  weightKg: number;
};

export class DeliveriesPage {
  constructor(private readonly page: Page) {}

  get formHeading() {
    return this.page.getByRole('heading', { name: 'Create delivery' });
  }

  get successMessage() {
    return this.page.getByTestId('delivery-success');
  }

  get rows() {
    return this.page.getByTestId('delivery-row');
  }

  fieldError(field: string) {
    return this.page.getByTestId(`${field}-error`);
  }

  rowForId(id: string) {
    return this.rows.filter({
      has: this.page.getByRole('cell', { name: id, exact: true }),
    });
  }

  async fillDelivery(delivery: Delivery) {
    await this.page.getByTestId('pickup-name').fill(delivery.pickup.name);
    await this.page.getByTestId('pickup-phone').fill(delivery.pickup.phone);
    await this.page.getByTestId('pickup-address').fill(delivery.pickup.address);
    await this.page.getByTestId('dropoff-name').fill(delivery.dropoff.name);
    await this.page.getByTestId('dropoff-phone').fill(delivery.dropoff.phone);
    await this.page.getByTestId('dropoff-address').fill(delivery.dropoff.address);
    await this.page.getByTestId('package-description').fill(delivery.description);
    await this.page.getByTestId('package-weight').fill(String(delivery.weightKg));
  }

  async submit() {
    await this.page.getByRole('button', { name: 'Create and publish delivery' }).click();
  }

  async createDelivery(delivery: Delivery) {
    await this.fillDelivery(delivery);
    await this.submit();
  }
}
