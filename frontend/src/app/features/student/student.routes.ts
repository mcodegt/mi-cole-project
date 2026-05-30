import { Routes } from '@angular/router';

export const STUDENT_ROUTES: Routes = [
  {
    path: '',
    data: { title: 'Inicio' },
    loadComponent: () =>
      import('./student-home/student-home.component').then((m) => m.StudentHomeComponent),
  },
  {
    path: 'assignments',
    data: { title: 'Tareas' },
    loadComponent: () =>
      import('./student-assignments/student-assignments.component').then(
        (m) => m.StudentAssignmentsComponent,
      ),
  },
  {
    path: 'assignments/:id',
    data: { title: 'Detalle de tarea' },
    loadComponent: () =>
      import('./student-assignment-detail/student-assignment-detail.component').then(
        (m) => m.StudentAssignmentDetailComponent,
      ),
  },
];
