import { faker } from '@faker-js/faker';
import type { Delivery } from '../../../pages/deliveries.page';

export class DeliveryDataFactory {
  static createDeliveryData(): Delivery {
    const phone = () => `080${faker.string.numeric(8)}`;

    return {
      pickup: {
        name: faker.person.fullName(),
        phone: phone(),
        address: faker.location.streetAddress(),
      },
      dropoff: {
        name: faker.person.fullName(),
        phone: phone(),
        address: faker.location.streetAddress(),
      },
      description:  faker.commerce.productDescription(),
      weightKg: faker.number.int({ min: 1, max: 50 }),
    };
  }
}
