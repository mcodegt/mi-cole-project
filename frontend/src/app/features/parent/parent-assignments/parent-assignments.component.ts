import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface ChildOption {
  id: string;
  full_name: string;
  code: string | null;
}

interface AssignmentRow {
  id: string;
  title: string;
  description: string | null;
  due_at: string | null;
  status: string;
  submission_status: string | null;
}

@Component({
  selector: 'app-parent-assignments',
  standalone: true,
  imports: [DatePipe, FormsModule, TableModule, TagModule, SelectModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Tareas" subtitle="Tareas publicadas por el colegio" />

    <div class="mc-card mb-4">
      <label class="mb-1 block text-xs font-medium mc-text-muted">Hijo</label>
      <p-select
        [options]="children()"
        [(ngModel)]="selectedStudentId"
        optionLabel="full_name"
        optionValue="id"
        placeholder="Seleccionar hijo"
        styleClass="w-full"
        (ngModelChange)="onStudentChange()"
      />
    </div>

    @if (selectedStudentId) {
      <div class="mc-card mc-table-card">
        <p-table
          [value]="assignments()"
          [paginator]="true"
          [rows]="pageSize"
          [loading]="loading()"
          [rowsPerPageOptions]="[5, 10, 25]"
          styleClass="p-datatable-sm"
        >
          <ng-template #header>
            <tr>
              <th>Tarea</th>
              <th>Entrega</th>
              <th>Estado entrega</th>
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
                  [severity]="a.submission_status === 'submitted' ? 'success' : 'warn'"
                />
              </td>
            </tr>
          </ng-template>
          <ng-template #emptymessage>
            <tr>
              <td colspan="3" class="py-8 text-center mc-text-muted">Sin tareas publicadas</td>
            </tr>
          </ng-template>
        </p-table>
      </div>
    }
  `,
})
export class ParentAssignmentsComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly children = signal<ChildOption[]>([]);
  readonly assignments = signal<AssignmentRow[]>([]);
  readonly loading = signal(false);
  readonly pageSize = 10;
  selectedStudentId: string | null = null;

  ngOnInit(): void {
    this.http.get<ChildOption[]>(`${environment.apiUrl}/parent/children`).subscribe({
      next: (res) => {
        this.children.set(res);
        const fromQuery = this.route.snapshot.queryParamMap.get('student_id');
        if (fromQuery && res.some((c) => c.id === fromQuery)) {
          this.selectedStudentId = fromQuery;
        } else if (res.length === 1) {
          this.selectedStudentId = res[0].id;
        }
        if (this.selectedStudentId) {
          this.loadAssignments();
        }
      },
    });
  }

  onStudentChange(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { student_id: this.selectedStudentId },
      queryParamsHandling: 'merge',
    });
    this.loadAssignments();
  }

  loadAssignments(): void {
    if (!this.selectedStudentId) {
      return;
    }
    this.loading.set(true);
    this.http
      .get<AssignmentRow[]>(`${environment.apiUrl}/parent/assignments`, {
        params: { student_id: this.selectedStudentId },
      })
      .subscribe({
        next: (res) => {
          this.assignments.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
