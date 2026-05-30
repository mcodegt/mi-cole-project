import { Routes } from '@angular/router';

export const PARENT_ROUTES: Routes = [
  {
    path: '',
    data: { title: 'Inicio' },
    loadComponent: () =>
      import('./parent-home/parent-home.component').then((m) => m.ParentHomeComponent),
  },
  {
    path: 'assignments',
    data: { title: 'Tareas' },
    loadComponent: () =>
      import('./parent-assignments/parent-assignments.component').then(
        (m) => m.ParentAssignmentsComponent,
      ),
  },
];
