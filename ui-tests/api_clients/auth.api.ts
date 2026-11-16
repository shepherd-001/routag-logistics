import type { APIRequestContext } from '@playwright/test';

export class AuthApi {
  constructor(private readonly request: APIRequestContext) {}

  login(email: string, password: string) {
    return this.request.post('/api/v1/auth/login', {
      data: { email, password },
    });
  }
}
