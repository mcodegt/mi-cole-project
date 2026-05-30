import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TagModule } from 'primeng/tag';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface AssignmentRow {
  id: string;
  title: string;
  description: string | null;
  due_at: string | null;
  status: string;
  submission_status: string | null;
}

interface PaginatedAssignments {
  items: AssignmentRow[];
  total: number;
  page: number;
  limit: number;
}

@Component({
  selector: 'app-student-assignments',
  standalone: true,
  imports: [DatePipe, RouterLink, TagModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Mis tareas" subtitle="Tareas publicadas para tu sede" />

    <div class="grid gap-3">
      @for (a of assignments(); track a.id) {
        <a
          [routerLink]="['/student/assignments', a.id]"
          class="mc-touch-card block"
        >
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <p class="font-medium mc-text">{{ a.title }}</p>
              @if (a.description) {
                <p class="mt-1 text-sm mc-text-muted line-clamp-2">{{ a.description }}</p>
              }
            </div>
            <p-tag
              [value]="a.submission_status ?? 'pendiente'"
              [severity]="a.submission_status === 'submitted' || a.submission_status === 'graded' ? 'success' : 'warn'"
            />
          </div>
          <p class="mt-2 text-xs mc-text-muted">
            Entrega: {{ a.due_at ? (a.due_at | date: 'mediumDate') : 'Sin fecha' }}
          </p>
        </a>
      } @empty {
        <div class="mc-card py-8 text-center mc-text-muted">Sin tareas publicadas</div>
      }
    </div>
  `,
})
export class StudentAssignmentsComponent implements OnInit {
  private readonly http = inject(HttpClient);

  readonly assignments = signal<AssignmentRow[]>([]);

  ngOnInit(): void {
    this.http
      .get<PaginatedAssignments>(`${environment.apiUrl}/student/assignments`, {
        params: { page: 1, limit: 50 },
      })
      .subscribe({
        next: (res) => this.assignments.set(res.items),
      });
  }
}
