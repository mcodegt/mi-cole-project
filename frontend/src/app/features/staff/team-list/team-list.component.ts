import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { TableModule } from 'primeng/table';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-team-list',
  standalone: true,
  imports: [TableModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Equipo" subtitle="Membresías staff del colegio" />

    <div class="mc-card overflow-hidden p-0">
      <p-table [value]="members()" styleClass="p-datatable-sm">
        <ng-template #header>
          <tr>
            <th>Nombre</th>
            <th>Rol</th>
          </tr>
        </ng-template>
        <ng-template #body let-m>
          <tr>
            <td>{{ m.user.full_name }}</td>
            <td>{{ m.role_code }}</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class TeamListComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly members = signal<
    { membership_id: string; role_code: string; user: { full_name: string } }[]
  >([]);

  ngOnInit(): void {
    this.http
      .get<{
        items: { membership_id: string; role_code: string; user: { full_name: string } }[];
      }>(`${environment.apiUrl}/team`, { params: { page: 1, limit: 50 } })
      .subscribe((res) => this.members.set(res.items));
  }
}
