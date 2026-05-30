import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const studentGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.session()?.portal === 'student' && auth.session()?.studentId) {
    return true;
  }
  const slug = auth.session()?.student?.school_slug ?? 'colegio-demo';
  return router.createUrlTree(['/login/student', slug, 'sede-norte']);
};
