import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

/** Rutas de administración del colegio (dueño). */
export const schoolOwnerGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isSchoolOwner()) {
    return true;
  }

  if (auth.isBillingRestricted()) {
    return router.createUrlTree(['/app/subscription']);
  }

  return router.createUrlTree(['/app']);
};
