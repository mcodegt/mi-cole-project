import { Routes } from '@angular/router';

export const STUDENT_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./student-home/student-home.component').then((m) => m.StudentHomeComponent),
  },
  {
    path: 'assignments',
    loadComponent: () =>
      import('./student-assignments/student-assignments.component').then(
        (m) => m.StudentAssignmentsComponent,
      ),
  },
  {
    path: 'assignments/:id',
    loadComponent: () =>
      import('./student-assignment-detail/student-assignment-detail.component').then(
        (m) => m.StudentAssignmentDetailComponent,
      ),
  },
];
