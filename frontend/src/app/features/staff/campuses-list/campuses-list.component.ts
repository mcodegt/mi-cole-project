import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface CampusRow {
  id: string;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-campuses-list',
  standalone: true,
  imports: [TableModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Sedes" subtitle="Campus del colegio" backRoute="/app" />

    <div class="mc-card mc-table-card">
      <p-table
        [value]="campuses()"
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
            <th>Slug</th>
          </tr>
        </ng-template>
        <ng-template #body let-c>
          <tr>
            <td class="font-medium mc-text">{{ c.name }}</td>
            <td class="mc-text-subtle">{{ c.slug }}</td>
          </tr>
        </ng-template>
        <ng-template #emptymessage>
          <tr>
            <td colspan="2" class="py-8 text-center mc-text-muted">Sin sedes registradas</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class CampusesListComponent {
  private readonly http = inject(HttpClient);

  readonly campuses = signal<CampusRow[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageSize = 25;

  loadPage(event: TableLazyLoadEvent): void {
    const rows = event.rows ?? this.pageSize;
    const page = Math.floor((event.first ?? 0) / rows) + 1;
    this.loading.set(true);
    this.http
      .get<{ items: CampusRow[]; total: number }>(`${environment.apiUrl}/campuses`, {
        params: { page, limit: rows },
      })
      .subscribe({
        next: (res) => {
          this.campuses.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
