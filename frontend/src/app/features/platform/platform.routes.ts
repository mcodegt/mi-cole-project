import { Routes } from '@angular/router';

export const PLATFORM_ROUTES: Routes = [
  { path: '', redirectTo: 'schools', pathMatch: 'full' },
  {
    path: 'schools',
    data: { title: 'Colegios' },
    loadComponent: () =>
      import('./schools-list/schools-list.component').then((m) => m.SchoolsListComponent),
  },
  {
    path: 'billing',
    data: { title: 'Facturación' },
    loadComponent: () =>
      import('./billing-queue/billing-queue.component').then((m) => m.BillingQueueComponent),
  },
];
