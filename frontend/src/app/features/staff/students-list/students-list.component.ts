import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface StudentRow {
  id: string;
  code: string | null;
  full_name: string;
  status: string;
}

interface CampusOption {
  id: string;
  name: string;
}

@Component({
  selector: 'app-students-list',
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
    <mc-page-header
      title="Estudiantes"
      [subtitle]="total() + ' registrados en el colegio'"
    />

    <div class="mc-card mb-4 flex flex-wrap items-end gap-3 p-4">
      <div class="min-w-[12rem] flex-1">
        <label class="mb-1 block text-xs font-medium text-slate-500">Buscar</label>
        <input
          pInputText
          class="w-full"
          placeholder="Nombre o código…"
          [(ngModel)]="searchInput"
          (keyup.enter)="applyFilters()"
        />
      </div>
      <div class="w-44">
        <label class="mb-1 block text-xs font-medium text-slate-500">Sede</label>
        <p-select
          [options]="campuses()"
          [(ngModel)]="campusInput"
          optionLabel="name"
          optionValue="id"
          placeholder="Todas"
          [showClear]="true"
          styleClass="w-full"
        />
      </div>
      <div class="w-36">
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
        [value]="students()"
        [lazy]="true"
        [paginator]="true"
        [rows]="pageSize"
        [totalRecords]="total()"
        [loading]="loading()"
        [rowsPerPageOptions]="[10, 25, 50]"
        (onLazyLoad)="loadPage($event)"
        styleClass="p-datatable-sm"
        [tableStyle]="{ 'min-width': '40rem' }"
      >
        <ng-template #header>
          <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>Estado</th>
          </tr>
        </ng-template>
        <ng-template #body let-s>
          <tr>
            <td class="font-medium text-slate-800">{{ s.code || '—' }}</td>
            <td>{{ s.full_name }}</td>
            <td>
              <p-tag [value]="s.status" [severity]="s.status === 'active' ? 'success' : 'secondary'" />
            </td>
          </tr>
        </ng-template>
        <ng-template #emptymessage>
          <tr>
            <td colspan="3" class="py-8 text-center text-slate-500">Sin estudiantes</td>
          </tr>
        </ng-template>
      </p-table>
    </div>
  `,
})
export class StudentsListComponent implements OnInit {
  private readonly http = inject(HttpClient);

  readonly students = signal<StudentRow[]>([]);
  readonly campuses = signal<CampusOption[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageSize = 25;

  searchInput = '';
  campusInput: string | null = null;
  statusInput: string | null = null;
  private searchQuery = '';
  private campusFilter: string | null = null;
  private statusFilter: string | null = null;
  private lastEvent: TableLazyLoadEvent | null = null;

  readonly statusOptions = [
    { label: 'Activo', value: 'active' },
    { label: 'Inactivo', value: 'inactive' },
  ];

  ngOnInit(): void {
    this.http
      .get<{ items: CampusOption[] }>(`${environment.apiUrl}/campuses`, {
        params: { page: 1, limit: 100 },
      })
      .subscribe((res) => this.campuses.set(res.items));
  }

  applyFilters(): void {
    this.searchQuery = this.searchInput.trim();
    this.campusFilter = this.campusInput;
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
    if (this.campusFilter) {
      params = params.set('campus_id', this.campusFilter);
    }
    if (this.statusFilter) {
      params = params.set('status', this.statusFilter);
    }
    this.loading.set(true);
    this.http
      .get<{ items: StudentRow[]; total: number }>(`${environment.apiUrl}/students`, { params })
      .subscribe({
        next: (res) => {
          this.students.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
