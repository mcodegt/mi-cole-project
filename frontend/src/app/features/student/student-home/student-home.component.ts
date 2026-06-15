import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TagModule } from 'primeng/tag';

import { McKpiCardComponent } from '../../../shared/mc-kpi-card.component';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface DashboardData {
  student_name: string;
  student_code: string | null;
  school_name: string;
  pending_assignments_count: number;
  submitted_assignments_count: number;
}

@Component({
  selector: 'app-student-home',
  standalone: true,
  imports: [RouterLink, TagModule, McPageHeaderComponent, McKpiCardComponent],
  template: `
    <mc-page-header
      title="Bienvenido"
      [subtitle]="dashboard()?.student_name ?? ''"
      [showBack]="false"
    />

    @if (dashboard(); as d) {
      <div class="mb-6 grid gap-4 sm:grid-cols-2">
        <mc-kpi-card label="Tareas pendientes" [value]="d.pending_assignments_count" />
        <mc-kpi-card label="Entregas enviadas" [value]="d.submitted_assignments_count" />
      </div>

      <div class="mc-card">
        <h2 class="mb-4 text-base font-semibold mc-text">Acceso rápido</h2>
        <a routerLink="/student/assignments" class="mc-touch-card inline-flex w-full items-center gap-3 sm:w-auto">
          <i class="pi pi-book text-indigo-500"></i>
          <span class="text-sm font-medium mc-text">Ver mis tareas</span>
        </a>
      </div>
    }
  `,
})
export class StudentHomeComponent implements OnInit {
  private readonly http = inject(HttpClient);

  readonly dashboard = signal<DashboardData | null>(null);

  ngOnInit(): void {
    this.http.get<DashboardData>(`${environment.apiUrl}/student/dashboard`).subscribe({
      next: (res) => this.dashboard.set(res),
    });
  }
}
