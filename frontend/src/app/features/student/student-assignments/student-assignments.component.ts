import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
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

@Component({
  selector: 'app-student-assignments',
  standalone: true,
  imports: [DatePipe, RouterLink, TableModule, TagModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Mis tareas" subtitle="Tareas publicadas para tu sede" />

    <div class="mc-card mc-table-card">
      <p-table
        [value]="assignments()"
        [lazy]="true"
        [paginator]="true"
        [rows]="pageSize"
        [totalRecords]="total()"
        [loading]="loading()"
        [rowsPerPageOptions]="[10, 25, 50]"
        (onLazyLoad)="loadPage($event)"
        styleClass="p-datatable-sm"
      >
        <ng-template #header>
          <tr>
            <th>Tarea</th>
            <th>Entrega</th>
            <th>Estado</th>
            <th class="w-24"></th>
          </tr>
        </ng-template>
        <ng-template #body let-a>
          <tr>
            <td>
              <p class="font-medium mc-text">{{ a.title }}</p>
              @if (a.description) {
                <p class="mt-1 text-sm mc-text-muted line-clamp-2">{{ a.description }}</p>
              }
            </td>
            <td class="whitespace-nowrap">
              {{ a.due_at ? (a.due_at | date: 'mediumDate') : 'Sin fecha' }}
            </td>
            <td>
              <p-tag
                [value]="a.submission_status ?? 'pendiente'"
                [severity]="a.submission_status === 'submitted' || a.submission_status === 'graded' ? 'success' : 'warn'"
              />
            </td>
            <td>
              <a
                [routerLink]="['/student/assignments', a.id]"
                class="text-sm font-medium mc-text-accent hover:underline"
              >
                Ver
              </a>
            </td>
          </tr>
        </ng-template>
        <ng-template #emptymessage>
          <tr>
            <td colspan="4" class="py-8 text-center mc-text-muted">Sin tareas publicadas</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class StudentAssignmentsComponent {
  private readonly http = inject(HttpClient);

  readonly assignments = signal<AssignmentRow[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageSize = 10;

  loadPage(event: TableLazyLoadEvent): void {
    const rows = event.rows ?? this.pageSize;
    const page = Math.floor((event.first ?? 0) / rows) + 1;
    this.loading.set(true);
    this.http
      .get<{ items: AssignmentRow[]; total: number }>(`${environment.apiUrl}/student/assignments`, {
        params: { page, limit: rows },
      })
      .subscribe({
        next: (res) => {
          this.assignments.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
