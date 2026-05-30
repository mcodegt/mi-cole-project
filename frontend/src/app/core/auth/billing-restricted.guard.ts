import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

/** En modo restringido solo se permite /app/subscription y hijos. */
export const billingAllowedGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isBillingRestricted()) {
    return true;
  }
  return router.createUrlTree(['/app/subscription']);
};

export const billingRestrictedOnlyGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  if (auth.isBillingRestricted()) {
    return true;
  }
  return inject(Router).createUrlTree(['/app']);
};
