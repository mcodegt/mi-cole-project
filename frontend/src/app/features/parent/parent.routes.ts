import { Routes } from '@angular/router';

export const PARENT_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./parent-home/parent-home.component').then((m) => m.ParentHomeComponent),
  },
  {
    path: 'assignments',
    loadComponent: () =>
      import('./parent-assignments/parent-assignments.component').then(
        (m) => m.ParentAssignmentsComponent,
      ),
  },
];
