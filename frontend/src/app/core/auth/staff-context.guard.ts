import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const staffContextGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const session = auth.session();
  if (session?.portal === 'staff' && session.schoolId && session.membershipId && session.campusId) {
    return true;
  }
  if (session?.portal === 'staff') {
    return router.createUrlTree(['/login/staff', session.staff?.school_slug ?? 'colegio-demo', 'sede-norte']);
  }
  return router.createUrlTree(['/login/staff/colegio-demo/sede-norte']);
};
