import { Routes } from '@angular/router';

export const PLATFORM_ROUTES: Routes = [
  { path: '', redirectTo: 'schools', pathMatch: 'full' },
  {
    path: 'schools',
    loadComponent: () =>
      import('./schools-list/schools-list.component').then((m) => m.SchoolsListComponent),
  },
  {
    path: 'billing',
    loadComponent: () =>
      import('./billing-queue/billing-queue.component').then((m) => m.BillingQueueComponent),
  },
];
