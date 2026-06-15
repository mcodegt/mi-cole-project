import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface TeamMemberRow {
  id: string;
  user_full_name: string;
  user_email: string;
  role_code: string;
  role_name: string;
  status: string;
}

@Component({
  selector: 'app-team-list',
  standalone: true,
  imports: [TableModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Equipo" subtitle="Membresías staff del colegio" backRoute="/app/settings" />

    <div class="mc-card mc-table-card">
      <p-table
        [value]="members()"
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
            <th>Nombre</th>
            <th>Correo</th>
            <th>Rol</th>
            <th>Estado</th>
          </tr>
        </ng-template>
        <ng-template #body let-m>
          <tr>
            <td class="font-medium">{{ m.user_full_name }}</td>
            <td class="mc-text-muted">{{ m.user_email }}</td>
            <td>{{ m.role_name }}</td>
            <td>{{ m.status }}</td>
          </tr>
        </ng-template>
        <ng-template #emptymessage>
          <tr>
            <td colspan="4" class="py-8 text-center mc-text-muted">Sin miembros en el equipo</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class TeamListComponent {
  private readonly http = inject(HttpClient);

  readonly members = signal<TeamMemberRow[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageSize = 25;

  loadPage(event: TableLazyLoadEvent): void {
    const rows = event.rows ?? this.pageSize;
    const page = Math.floor((event.first ?? 0) / rows) + 1;
    this.loading.set(true);
    this.http
      .get<{ items: TeamMemberRow[]; total: number }>(`${environment.apiUrl}/team/memberships`, {
        params: { page, limit: rows },
      })
      .subscribe({
        next: (res) => {
          this.members.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
