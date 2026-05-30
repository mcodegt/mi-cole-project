import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

let refreshInFlight = false;

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const session = auth.session();

  let headers = req.headers;
  if (session?.accessToken && !req.url.includes('/auth/login')) {
    headers = headers.set('Authorization', `Bearer ${session.accessToken}`);
  }
  if (session?.portal === 'staff') {
    headers = headers.set('X-Portal', 'staff');
    if (session.schoolId) {
      headers = headers.set('X-School-Id', session.schoolId);
    }
    if (session.campusId) {
      headers = headers.set('X-Campus-Id', session.campusId);
    }
  } else if (session?.portal === 'platform') {
    headers = headers.set('X-Portal', 'platform');
  } else if (session?.portal === 'parent') {
    headers = headers.set('X-Portal', 'parent');
    if (session.schoolId) {
      headers = headers.set('X-School-Id', session.schoolId);
    }
    if (session.campusId) {
      headers = headers.set('X-Campus-Id', session.campusId);
    }
  }

  const cloned = req.clone({ headers });

  return next(cloned).pipe(
    catchError((err: HttpErrorResponse) => {
      if (
        err.status !== 401 ||
        req.url.includes('/auth/login') ||
        req.url.includes('/auth/refresh') ||
        refreshInFlight
      ) {
        return throwError(() => err);
      }
      refreshInFlight = true;
      return auth.refreshToken().pipe(
        switchMap(() => {
          refreshInFlight = false;
          const updated = auth.session();
          let retryHeaders = req.headers;
          if (updated?.accessToken) {
            retryHeaders = retryHeaders.set('Authorization', `Bearer ${updated.accessToken}`);
          }
          if (updated?.portal === 'staff') {
            retryHeaders = retryHeaders.set('X-Portal', 'staff');
            if (updated.schoolId) {
              retryHeaders = retryHeaders.set('X-School-Id', updated.schoolId);
            }
            if (updated.campusId) {
              retryHeaders = retryHeaders.set('X-Campus-Id', updated.campusId);
            }
          } else if (updated?.portal === 'parent') {
            retryHeaders = retryHeaders.set('X-Portal', 'parent');
            if (updated.schoolId) {
              retryHeaders = retryHeaders.set('X-School-Id', updated.schoolId);
            }
            if (updated.campusId) {
              retryHeaders = retryHeaders.set('X-Campus-Id', updated.campusId);
            }
          }
          return next(req.clone({ headers: retryHeaders }));
        }),
        catchError((refreshErr) => {
          refreshInFlight = false;
          auth.clearSession();
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};
