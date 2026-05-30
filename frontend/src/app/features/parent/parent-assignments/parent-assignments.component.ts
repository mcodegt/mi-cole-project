import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SelectModule } from 'primeng/select';
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
  imports: [DatePipe, FormsModule, TagModule, SelectModule, McPageHeaderComponent],
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

    @if (loading()) {
      <div class="mc-card py-8 text-center mc-text-muted">Cargando tareas…</div>
    } @else if (selectedStudentId) {
      <div class="grid gap-3">
        @for (a of assignments(); track a.id) {
          <article class="mc-card">
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <p class="font-medium mc-text">{{ a.title }}</p>
                @if (a.description) {
                  <p class="mt-1 text-sm mc-text-muted line-clamp-3">{{ a.description }}</p>
                }
              </div>
              <p-tag
                [value]="a.submission_status ?? 'pendiente'"
                [severity]="a.submission_status === 'submitted' ? 'success' : 'warn'"
              />
            </div>
            <p class="mt-3 text-xs mc-text-muted">
              Entrega: {{ a.due_at ? (a.due_at | date: 'mediumDate') : 'Sin fecha' }}
            </p>
          </article>
        } @empty {
          <div class="mc-card py-8 text-center mc-text-muted">Sin tareas publicadas</div>
        }
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
