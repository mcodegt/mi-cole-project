import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const platformGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const session = auth.session();
  if (session?.portal === 'platform' && (session.platform?.is_superadmin || auth.hasPermission('platform.schools.manage'))) {
    return true;
  }
  return router.createUrlTree(['/login/platform']);
};
