import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';

import { AuthService } from '../../../core/auth/auth.service';
import { McKpiCardComponent } from '../../../shared/mc-kpi-card.component';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-staff-home',
  standalone: true,
  imports: [McPageHeaderComponent, McKpiCardComponent],
  template: `
    <mc-page-header
      title="Dashboard"
      [subtitle]="'Bienvenido, ' + (auth.session()?.user?.full_name ?? '')"
    />

    @if (dashboard(); as d) {
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <mc-kpi-card
          label="Estudiantes"
          [value]="d.usage['students'].current"
          [hint]="'Límite: ' + (d.usage['students'].max ?? '∞')"
        />
        <mc-kpi-card label="Plan" [value]="d.plan?.name ?? 'Sin plan'" />
        <mc-kpi-card label="Acceso" [value]="d.billing.billing_access_mode" />
        <mc-kpi-card
          label="Padres"
          [value]="d.usage['parents'].current"
          [hint]="'Límite: ' + (d.usage['parents'].max ?? '∞')"
        />
      </div>
    }
  `,
})
export class StaffHomeComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);

  readonly dashboard = signal<{
    plan?: { name: string };
    billing: { billing_access_mode: string };
    usage: Record<string, { current: number; max?: number }>;
  } | null>(null);

  ngOnInit(): void {
    this.http.get(`${environment.apiUrl}/subscription/dashboard`).subscribe({
      next: (res) => this.dashboard.set(res as never),
    });
  }
}
