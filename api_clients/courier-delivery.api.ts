import type { APIRequestContext } from '@playwright/test';

export class CourierDeliveryApi {
  constructor(private readonly request: APIRequestContext) {}

  acceptDelivery(id: string, token: string) {
    return this.request.post(`/api/v1/courier/deliveries/${id}/accept`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  }
}
