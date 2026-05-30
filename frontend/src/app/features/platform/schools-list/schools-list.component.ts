import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface SchoolRow {
  id: string;
  name: string;
  slug: string;
  status: string;
  billing_access_mode: string;
}

@Component({
  selector: 'app-schools-list',
  standalone: true,
  imports: [TableModule, TagModule, McPageHeaderComponent],
  template: `
    <mc-page-header title="Colegios" subtitle="Administración de colegios en la plataforma" />

    @if (error()) {
      <p class="mb-4 text-sm text-red-600">{{ error() }}</p>
    }

    <div class="mc-card overflow-hidden p-0">
      <p-table
        [value]="schools()"
        [lazy]="true"
        [paginator]="true"
        [rows]="pageSize"
        [totalRecords]="total()"
        [loading]="loading()"
        (onLazyLoad)="loadPage($event)"
        styleClass="p-datatable-sm"
      >
        <ng-template #header>
          <tr>
            <th>Nombre</th>
            <th>Slug</th>
            <th>Estado</th>
            <th>Facturación</th>
          </tr>
        </ng-template>
        <ng-template #body let-s>
          <tr>
            <td class="font-medium">{{ s.name }}</td>
            <td>{{ s.slug }}</td>
            <td><p-tag [value]="s.status" /></td>
            <td>{{ s.billing_access_mode }}</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class SchoolsListComponent {
  private readonly http = inject(HttpClient);

  readonly schools = signal<SchoolRow[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly pageSize = 25;

  loadPage(event: TableLazyLoadEvent): void {
    const rows = event.rows ?? this.pageSize;
    const page = Math.floor((event.first ?? 0) / rows) + 1;
    this.loading.set(true);
    this.error.set(null);
    this.http
      .get<{ items: SchoolRow[]; total: number }>(`${environment.apiUrl}/platform/schools`, {
        params: { page, limit: rows },
      })
      .subscribe({
        next: (res) => {
          this.schools.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(err?.error?.detail ?? 'Error al cargar colegios');
          this.loading.set(false);
        },
      });
  }
}
