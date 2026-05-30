import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
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
  portal_access: boolean;
}

interface CampusOption {
  id: string;
  name: string;
}

interface InviteResult {
  login_path: string;
  temporary_password: string;
  email: string;
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
    DialogModule,
    McPageHeaderComponent,
  ],
  template: `
    <mc-page-header
      title="Estudiantes"
      [subtitle]="total() + ' registrados en el colegio'"
    />

    <div class="mc-card mb-4 flex flex-wrap items-end gap-3 p-4">
      <div class="min-w-[12rem] flex-1">
        <label class="mb-1 block text-xs font-medium mc-text-muted">Buscar</label>
        <input
          pInputText
          class="w-full"
          placeholder="Nombre o código…"
          [(ngModel)]="searchInput"
          (keyup.enter)="applyFilters()"
        />
      </div>
      <div class="w-44">
        <label class="mb-1 block text-xs font-medium mc-text-muted">Sede</label>
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
        <label class="mb-1 block text-xs font-medium mc-text-muted">Estado</label>
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
        [tableStyle]="{ 'min-width': '44rem' }"
      >
        <ng-template #header>
          <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>Estado</th>
            <th>Portal</th>
            <th></th>
          </tr>
        </ng-template>
        <ng-template #body let-s>
          <tr>
            <td class="font-medium mc-text">{{ s.code || '—' }}</td>
            <td>{{ s.full_name }}</td>
            <td>
              <p-tag [value]="s.status" [severity]="s.status === 'active' ? 'success' : 'secondary'" />
            </td>
            <td>
              @if (s.portal_access) {
                <p-tag value="activo" severity="success" />
              } @else {
                <p-tag value="sin acceso" severity="secondary" />
              }
            </td>
            <td>
              @if (!s.portal_access && s.status === 'active') {
                <p-button
                  label="Invitar"
                  icon="pi pi-send"
                  size="small"
                  [text]="true"
                  (onClick)="openInvite(s)"
                />
              }
            </td>
          </tr>
        </ng-template>
        <ng-template #emptymessage>
          <tr>
            <td colspan="5" class="py-8 text-center mc-text-muted">Sin estudiantes</td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <p-dialog
      header="Invitar al portal de estudiantes"
      [(visible)]="inviteVisible"
      [modal]="true"
      [style]="{ width: '28rem', maxWidth: '95vw' }"
    >
      @if (!inviteResult()) {
        <p class="mb-4 text-sm mc-text-muted">
          El estudiante recibirá acceso con contraseña temporal al portal de su sede.
        </p>
        <label class="mb-1 block text-xs font-medium mc-text-muted">Correo del estudiante</label>
        <input pInputText class="w-full" type="email" [(ngModel)]="inviteEmail" />
        @if (inviteError()) {
          <p class="mt-2 text-sm text-red-600">{{ inviteError() }}</p>
        }
        <ng-template #footer>
          <p-button label="Cancelar" severity="secondary" [text]="true" (onClick)="inviteVisible = false" />
          <p-button label="Invitar" [loading]="inviteLoading()" (onClick)="sendInvite()" />
        </ng-template>
      } @else {
        <div class="space-y-3 text-sm">
          <p class="font-medium text-emerald-700 dark:text-emerald-300">Invitación creada</p>
          <div>
            <span class="mc-text-muted">Enlace</span>
            <p class="mt-1 break-all rounded p-2 font-mono text-xs" style="background: var(--mc-surface-muted)">{{ inviteLoginUrl() }}</p>
          </div>
          <div>
            <span class="mc-text-muted">Contraseña temporal</span>
            <p class="mt-1 rounded p-2 font-mono" style="background: var(--mc-surface-muted)">{{ inviteResult()?.temporary_password }}</p>
          </div>
          <p-button label="Copiar enlace" icon="pi pi-copy" (onClick)="copyInviteUrl()" />
        </div>
        <ng-template #footer>
          <p-button label="Cerrar" (onClick)="closeInvite()" />
        </ng-template>
      }
    </p-dialog>
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

  inviteVisible = false;
  inviteEmail = '';
  inviteTargetId: string | null = null;
  readonly inviteLoading = signal(false);
  readonly inviteError = signal<string | null>(null);
  readonly inviteResult = signal<InviteResult | null>(null);

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

  openInvite(student: StudentRow): void {
    this.inviteTargetId = student.id;
    this.inviteEmail = '';
    this.inviteError.set(null);
    this.inviteResult.set(null);
    this.inviteVisible = true;
  }

  sendInvite(): void {
    if (!this.inviteTargetId || !this.inviteEmail.trim()) {
      return;
    }
    this.inviteLoading.set(true);
    this.inviteError.set(null);
    this.http
      .post<InviteResult>(`${environment.apiUrl}/students/${this.inviteTargetId}/invite`, {
        email: this.inviteEmail.trim(),
      })
      .subscribe({
        next: (res) => {
          this.inviteResult.set(res);
          this.inviteLoading.set(false);
          this.loadPage(this.lastEvent ?? { first: 0, rows: this.pageSize });
        },
        error: (err) => {
          this.inviteLoading.set(false);
          this.inviteError.set(err.error?.detail ?? 'No se pudo invitar');
        },
      });
  }

  inviteLoginUrl(): string {
    const path = this.inviteResult()?.login_path ?? '';
    return `${window.location.origin}${path}`;
  }

  copyInviteUrl(): void {
    void navigator.clipboard.writeText(this.inviteLoginUrl());
  }

  closeInvite(): void {
    this.inviteVisible = false;
    this.inviteResult.set(null);
  }
}
