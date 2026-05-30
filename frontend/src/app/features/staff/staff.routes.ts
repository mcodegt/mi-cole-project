import { Routes } from '@angular/router';

import { billingAllowedGuard } from '../../core/auth/billing-restricted.guard';

export const STAFF_ROUTES: Routes = [
  {
    path: '',
    canActivate: [billingAllowedGuard],
    loadComponent: () =>
      import('./staff-home/staff-home.component').then((m) => m.StaffHomeComponent),
  },
  {
    path: 'campuses',
    canActivate: [billingAllowedGuard],
    loadComponent: () =>
      import('./campuses-list/campuses-list.component').then((m) => m.CampusesListComponent),
  },
  {
    path: 'students',
    canActivate: [billingAllowedGuard],
    loadComponent: () =>
      import('./students-list/students-list.component').then((m) => m.StudentsListComponent),
  },
  {
    path: 'parents',
    canActivate: [billingAllowedGuard],
    loadComponent: () =>
      import('./parents-list/parents-list.component').then((m) => m.ParentsListComponent),
  },
  {
    path: 'team',
    canActivate: [billingAllowedGuard],
    loadComponent: () => import('./team-list/team-list.component').then((m) => m.TeamListComponent),
  },
  {
    path: 'subscription',
    loadComponent: () =>
      import('./subscription-page/subscription-page.component').then((m) => m.SubscriptionPageComponent),
  },
];
