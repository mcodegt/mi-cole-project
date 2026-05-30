import { Routes } from '@angular/router';

import { billingAllowedGuard } from '../../core/auth/billing-restricted.guard';

export const STAFF_ROUTES: Routes = [
  {
    path: '',
    canActivate: [billingAllowedGuard],
    data: { title: 'Dashboard' },
    loadComponent: () =>
      import('./staff-home/staff-home.component').then((m) => m.StaffHomeComponent),
  },
  {
    path: 'campuses',
    canActivate: [billingAllowedGuard],
    data: { title: 'Sedes' },
    loadComponent: () =>
      import('./campuses-list/campuses-list.component').then((m) => m.CampusesListComponent),
  },
  {
    path: 'students',
    canActivate: [billingAllowedGuard],
    data: { title: 'Estudiantes' },
    loadComponent: () =>
      import('./students-list/students-list.component').then((m) => m.StudentsListComponent),
  },
  {
    path: 'parents',
    canActivate: [billingAllowedGuard],
    data: { title: 'Padres' },
    loadComponent: () =>
      import('./parents-list/parents-list.component').then((m) => m.ParentsListComponent),
  },
  {
    path: 'team',
    canActivate: [billingAllowedGuard],
    data: { title: 'Equipo' },
    loadComponent: () => import('./team-list/team-list.component').then((m) => m.TeamListComponent),
  },
  {
    path: 'subscription',
    data: { title: 'Suscripción' },
    loadComponent: () =>
      import('./subscription-page/subscription-page.component').then((m) => m.SubscriptionPageComponent),
  },
];
