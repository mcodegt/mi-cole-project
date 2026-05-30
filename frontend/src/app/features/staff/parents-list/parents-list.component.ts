import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface ParentRow {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  relationship: string;
  status: string;
}

@Component({
  selector: 'app-parents-list',
  standalone: true,
  imports: [
    FormsModule,
    TableModule,
    TagModule,
    InputTextModule,
    SelectModule,
    ButtonModule,
    McPageHeaderComponent,
  ],
  template: `
    <mc-page-header title="Padres" [subtitle]="total() + ' registrados en el colegio'" />

    <div class="mc-card mb-4 flex flex-wrap items-end gap-3 p-4">
      <div class="min-w-[12rem] flex-1">
        <label class="mb-1 block text-xs font-medium text-slate-500">Buscar</label>
        <input
          pInputText
          class="w-full"
          placeholder="Nombre o email…"
          [(ngModel)]="searchInput"
          (keyup.enter)="applyFilters()"
        />
      </div>
      <div class="w-40">
        <label class="mb-1 block text-xs font-medium text-slate-500">Estado</label>
        <p-select
          [options]="statusOptions"
          [(ngModel)]="statusInput"
          optionLabel="label"
          optionValue="value"
          placeholder="Todos"
          [showClear]="true"
          styleClass="w-full"
        />
      </div>
      <p-button label="Buscar" icon="pi pi-search" (onClick)="applyFilters()" />
    </div>

    <div class="mc-card overflow-hidden p-0">
      <p-table
        [value]="parents()"
        [lazy]="true"
        [paginator]="true"
        [rows]="pageSize"
        [totalRecords]="total()"
        [loading]="loading()"
        [rowsPerPageOptions]="[10, 25, 50]"
        (onLazyLoad)="loadPage($event)"
        styleClass="p-datatable-sm"
        [tableStyle]="{ 'min-width': '48rem' }"
      >
        <ng-template #header>
          <tr>
            <th>Nombre</th>
            <th>Email</th>
            <th>Teléfono</th>
            <th>Relación</th>
            <th>Estado</th>
          </tr>
        </ng-template>
        <ng-template #body let-p>
          <tr>
            <td class="font-medium text-slate-800">{{ p.full_name }}</td>
            <td>{{ p.email || '—' }}</td>
            <td>{{ p.phone || '—' }}</td>
            <td>{{ relationshipLabel(p.relationship) }}</td>
            <td>
              <p-tag
                [value]="p.status"
                [severity]="p.status === 'active' ? 'success' : 'secondary'"
              />
            </td>
          </tr>
        </ng-template>
        <ng-template #emptymessage>
          <tr>
            <td colspan="5" class="py-8 text-center text-slate-500">Sin padres</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class ParentsListComponent {
  private readonly http = inject(HttpClient);

  readonly parents = signal<ParentRow[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageSize = 25;

  searchInput = '';
  statusInput: string | null = null;
  private searchQuery = '';
  private statusFilter: string | null = null;
  private lastEvent: TableLazyLoadEvent | null = null;

  readonly statusOptions = [
    { label: 'Activo', value: 'active' },
    { label: 'Inactivo', value: 'inactive' },
  ];

  applyFilters(): void {
    this.searchQuery = this.searchInput.trim();
    this.statusFilter = this.statusInput;
    this.loadPage({
      first: 0,
      rows: this.lastEvent?.rows ?? this.pageSize,
    });
  }

  loadPage(event: TableLazyLoadEvent): void {
    this.lastEvent = event;
    const rows = event.rows ?? this.pageSize;
    const page = Math.floor((event.first ?? 0) / rows) + 1;
    let params = new HttpParams().set('page', page).set('limit', rows);
    if (this.searchQuery) {
      params = params.set('q', this.searchQuery);
    }
    if (this.statusFilter) {
      params = params.set('status', this.statusFilter);
    }
    this.loading.set(true);
    this.http
      .get<{ items: ParentRow[]; total: number }>(`${environment.apiUrl}/parents`, { params })
      .subscribe({
        next: (res) => {
          this.parents.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  relationshipLabel(value: string): string {
    const labels: Record<string, string> = {
      father: 'Padre',
      mother: 'Madre',
      guardian: 'Tutor',
      other: 'Otro',
    };
    return labels[value] ?? value;
  }
}
