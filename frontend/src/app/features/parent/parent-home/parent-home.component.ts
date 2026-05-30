import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TagModule } from 'primeng/tag';

import { McKpiCardComponent } from '../../../shared/mc-kpi-card.component';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface ChildRow {
  id: string;
  full_name: string;
  code: string | null;
  status: string;
}

interface DashboardData {
  parent_name: string;
  school_name: string;
  children_count: number;
  pending_assignments_count: number;
  children: ChildRow[];
}

@Component({
  selector: 'app-parent-home',
  standalone: true,
  imports: [RouterLink, TagModule, McPageHeaderComponent, McKpiCardComponent],
  template: `
    <mc-page-header
      title="Bienvenido"
      [subtitle]="dashboard()?.parent_name ?? ''"
    />

    @if (dashboard(); as d) {
      <div class="mb-6 grid gap-4 sm:grid-cols-2">
        <mc-kpi-card label="Hijos en el colegio" [value]="d.children_count" />
        <mc-kpi-card
          label="Tareas pendientes"
          [value]="d.pending_assignments_count"
          hint="Entre todos tus hijos"
        />
      </div>

      <div class="mc-card">
        <h2 class="mb-4 text-base font-semibold text-slate-900">Mis hijos</h2>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (child of d.children; track child.id) {
            <a
              [routerLink]="['/parent/assignments']"
              [queryParams]="{ student_id: child.id }"
              class="rounded-lg border border-slate-200 p-4 transition hover:border-primary hover:shadow-sm"
            >
              <p class="font-medium text-slate-900">{{ child.full_name }}</p>
              <p class="text-sm text-slate-500">{{ child.code || 'Sin código' }}</p>
              <p-tag
                class="mt-2"
                [value]="child.status"
                [severity]="child.status === 'active' ? 'success' : 'secondary'"
              />
            </a>
          }
        </div>
      </div>
    }
  `,
})
export class ParentHomeComponent implements OnInit {
  private readonly http = inject(HttpClient);

  readonly dashboard = signal<DashboardData | null>(null);

  ngOnInit(): void {
    this.http.get<DashboardData>(`${environment.apiUrl}/parent/dashboard`).subscribe({
      next: (res) => this.dashboard.set(res),
    });
  }
}
