import { Routes } from '@angular/router';

import { LoginEntryPageComponent } from './features/auth/login-entry-page/login-entry-page.component';
import { authGuard } from './core/auth/auth.guard';
import { parentGuard } from './core/auth/parent.guard';
import { studentGuard } from './core/auth/student.guard';
import { platformGuard } from './core/auth/platform.guard';
import { staffContextGuard } from './core/auth/staff-context.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/ced-landing/ced-landing.component').then((m) => m.CedLandingComponent),
    data: { title: 'Centro Educativo Digital' },
  },
  {
    path: 'login/platform',
    loadComponent: () =>
      import('./features/auth/login-page/login-page.component').then((m) => m.LoginPageComponent),
    data: { portal: 'platform', portalTitle: 'Platform', title: 'Iniciar sesión' },
  },
  {
    path: 'login/ingresar',
    component: LoginEntryPageComponent,
    data: { title: 'Ingresar' },
  },
  {
    path: 'login/:portal/:schoolSlug/:campusSlug',
    loadComponent: () =>
      import('./features/auth/login-page/login-page.component').then((m) => m.LoginPageComponent),
    data: { title: 'Iniciar sesión' },
  },
  {
    path: 'change-password',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/auth/change-password-page/change-password-page.component').then(
        (m) => m.ChangePasswordPageComponent,
      ),
    data: { title: 'Cambiar contraseña' },
  },
  {
    path: 'platform',
    canActivate: [authGuard, platformGuard],
    data: { portalTitle: 'Platform' },
    loadComponent: () =>
      import('./layouts/platform-shell/platform-shell.component').then((m) => m.PlatformShellComponent),
    loadChildren: () =>
      import('./features/platform/platform.routes').then((m) => m.PLATFORM_ROUTES),
  },
  {
    path: 'app',
    canActivate: [authGuard, staffContextGuard],
    data: { portalTitle: 'Staff' },
    loadComponent: () =>
      import('./layouts/staff-shell/staff-shell.component').then((m) => m.StaffShellComponent),
    loadChildren: () => import('./features/staff/staff.routes').then((m) => m.STAFF_ROUTES),
  },
  {
    path: 'parent',
    canActivate: [authGuard, parentGuard],
    data: { portalTitle: 'Padres' },
    loadComponent: () =>
      import('./layouts/parent-shell/parent-shell.component').then((m) => m.ParentShellComponent),
    loadChildren: () => import('./features/parent/parent.routes').then((m) => m.PARENT_ROUTES),
  },
  {
    path: 'student',
    canActivate: [authGuard, studentGuard],
    data: { portalTitle: 'Estudiantes' },
    loadComponent: () =>
      import('./layouts/student-shell/student-shell.component').then((m) => m.StudentShellComponent),
    loadChildren: () => import('./features/student/student.routes').then((m) => m.STUDENT_ROUTES),
  },
  { path: '**', redirectTo: '' },
];
