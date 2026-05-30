import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const parentGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.session()?.portal === 'parent' && auth.session()?.parentId) {
    return true;
  }
  const slug = auth.session()?.parent?.school_slug ?? 'colegio-demo';
  return router.createUrlTree(['/login/parent', slug, 'sede-norte']);
};
