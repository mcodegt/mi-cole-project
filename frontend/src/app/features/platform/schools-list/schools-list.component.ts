import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { SelectModule } from 'primeng/select';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';

import { McFormFieldComponent } from '../../../shared/mc-form-field.component';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface SchoolRow {
  id: string;
  name: string;
  slug: string;
  status: string;
  subscription_plan_id: string | null;
  billing_access_mode: string;
  payment_reference_code: string | null;
  currency: string;
  notes: string | null;
}

interface PlanOption {
  label: string;
  value: string | null;
}

interface ConfigForm {
  id: string;
  slug: string;
  name: string;
  status: string;
  subscription_plan_id: string | null;
  billing_access_mode: string;
  currency: string;
  notes: string | null;
  payment_reference_code: string | null;
}

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const PROTECTED_SCHOOL_SLUGS = new Set(['colegio-demo']);

function slugify(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-');
}

function apiErrorDetail(err: unknown, fallback: string): string {
  const detail = (err as { error?: { detail?: unknown } })?.error?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') {
          return item;
        }
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg);
        }
        return JSON.stringify(item);
      })
      .join('; ');
  }
  return fallback;
}

@Component({
  selector: 'app-schools-list',
  standalone: true,
  imports: [
    FormsModule,
    TableModule,
    TagModule,
    ButtonModule,
    DialogModule,
    SelectModule,
    ToastModule,
    McFormFieldComponent,
    McPageHeaderComponent,
  ],
  providers: [MessageService],
  templateUrl: './schools-list.component.html',
})
export class SchoolsListComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly messages = inject(MessageService);

  readonly schools = signal<SchoolRow[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly createLoading = signal(false);
  readonly createSlugError = signal<string | null>(null);
  readonly createVisible = signal(false);
  readonly planOptions = signal<PlanOption[]>([]);
  readonly configVisible = signal(false);
  readonly configLoading = signal(false);
  readonly configSaving = signal(false);
  readonly configForm = signal<ConfigForm | null>(null);
  readonly deleteStepActive = signal(false);
  readonly deleteLoading = signal(false);

  deleteSlugInput = '';

  configDialogTitle(): string {
    const form = this.configForm();
    return form ? `Configurar — ${form.name}` : 'Configurar colegio';
  }

  readonly pageSize = 25;

  createName = '';
  createSlug = '';
  createPlanId: string | null = null;
  createOwnerEmail = '';
  createOwnerName = '';
  createOwnerPassword = '';
  private createSlugManual = false;

  searchInput = '';
  statusInput: string | null = null;
  private searchQuery = '';
  private statusFilter: string | null = null;
  private lastEvent: TableLazyLoadEvent | null = null;

  readonly statusFilterOptions = [
    { label: 'Activo', value: 'active' },
    { label: 'Inactivo', value: 'inactive' },
    { label: 'Prueba', value: 'trial' },
    { label: 'Suspendido', value: 'suspended' },
  ];

  readonly statusEditOptions = [...this.statusFilterOptions];

  readonly billingOptions = [
    { label: 'Completo', value: 'full' },
    { label: 'Solo comprobante', value: 'payment_evidence_only' },
  ];

  ngOnInit(): void {
    this.loadPlans();
  }

  openCreateModal(): void {
    this.configVisible.set(false);
    this.configForm.set(null);
    this.resetDeleteStep();
    this.resetCreateForm();
    this.createVisible.set(true);
  }

  onCreateVisibleChange(visible: boolean): void {
    this.createVisible.set(visible);
    if (!visible && !this.createLoading()) {
      this.resetCreateForm();
    }
  }

  onCreateNameChange(value: string): void {
    if (!this.createSlugManual) {
      this.createSlug = slugify(value);
      this.createSlugError.set(null);
    }
  }

  onCreateSlugChange(): void {
    this.createSlugManual = true;
    this.validateCreateSlug();
  }

  validateCreateSlug(): boolean {
    const slug = this.createSlug.trim();
    if (!slug) {
      this.createSlugError.set('El slug es obligatorio');
      return false;
    }
    if (!SLUG_PATTERN.test(slug)) {
      this.createSlugError.set('Use solo minúsculas, números y guiones (ej. colegio-demo)');
      return false;
    }
    this.createSlugError.set(null);
    return true;
  }

  createSchool(): void {
    const name = this.createName.trim();
    const slug = this.createSlug.trim();
    const email = this.createOwnerEmail.trim();
    const fullName = this.createOwnerName.trim();
    const password = this.createOwnerPassword;

    if (!name || !slug || !email || !fullName || !password) {
      this.messages.add({
        severity: 'warn',
        summary: 'Campos incompletos',
        detail: 'Complete nombre, slug y datos del dueño.',
      });
      return;
    }
    if (!this.validateCreateSlug()) {
      return;
    }
    if (password.length < 8) {
      this.messages.add({
        severity: 'warn',
        summary: 'Contraseña corta',
        detail: 'La contraseña del dueño debe tener al menos 8 caracteres.',
      });
      return;
    }

    this.createLoading.set(true);
    this.http
      .post<SchoolRow>(`${environment.apiUrl}/platform/schools`, {
        name,
        slug,
        subscription_plan_id: this.createPlanId,
        owner: {
          email,
          full_name: fullName,
          password,
        },
      })
      .subscribe({
        next: () => {
          this.createLoading.set(false);
          this.createVisible.set(false);
          this.messages.add({
            severity: 'success',
            summary: 'Colegio creado',
            detail: `${name} está listo. Dueño: ${email}`,
          });
          this.resetCreateForm();
          this.loadPage(this.lastEvent ?? { first: 0, rows: this.pageSize });
        },
        error: (err) => {
          this.createLoading.set(false);
          const detail = apiErrorDetail(err, 'No se pudo crear el colegio');
          if (err?.status === 409 || detail.toLowerCase().includes('slug')) {
            this.createSlugError.set('Slug de colegio ya existe');
          }
          this.messages.add({ severity: 'error', summary: 'Error', detail });
        },
      });
  }

  resetCreateForm(): void {
    this.createName = '';
    this.createSlug = '';
    this.createPlanId = null;
    this.createOwnerEmail = '';
    this.createOwnerName = '';
    this.createOwnerPassword = '';
    this.createSlugManual = false;
    this.createSlugError.set(null);
  }

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
      .get<{ items: SchoolRow[]; total: number }>(`${environment.apiUrl}/platform/schools`, {
        params,
      })
      .subscribe({
        next: (res) => {
          this.schools.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.messages.add({
            severity: 'error',
            summary: 'Error',
            detail: apiErrorDetail(err, 'Error al cargar colegios'),
          });
        },
      });
  }

  loadPlans(): void {
    this.http
      .get<{ items: { id: string; name: string; code: string }[] }>(
        `${environment.apiUrl}/platform/subscription-plans`,
        { params: { is_active: true, limit: 100 } },
      )
      .subscribe({
        next: (res) => {
          this.planOptions.set(
            res.items.map((p) => ({
              label: `${p.name} (${p.code})`,
              value: p.id,
            })),
          );
        },
        error: () => {
          this.messages.add({
            severity: 'warn',
            summary: 'Planes',
            detail: 'No se pudieron cargar los planes de suscripción.',
          });
        },
      });
  }

  openConfig(row: SchoolRow): void {
    this.createVisible.set(false);
    this.configVisible.set(true);
    this.configLoading.set(true);
    this.configForm.set(null);
    this.resetDeleteStep();
    this.http.get<SchoolRow>(`${environment.apiUrl}/platform/schools/${row.id}`).subscribe({
      next: (school) => {
        this.configForm.set({
          id: school.id,
          slug: school.slug,
          name: school.name,
          status: school.status,
          subscription_plan_id: school.subscription_plan_id,
          billing_access_mode: school.billing_access_mode,
          currency: school.currency,
          notes: school.notes ?? '',
          payment_reference_code: school.payment_reference_code,
        });
        this.configLoading.set(false);
      },
      error: (err) => {
        this.configLoading.set(false);
        this.configVisible.set(false);
        this.messages.add({
          severity: 'error',
          summary: 'Error',
          detail: apiErrorDetail(err, 'No se pudo cargar el colegio'),
        });
      },
    });
  }

  onConfigVisibleChange(visible: boolean): void {
    this.configVisible.set(visible);
    if (!visible) {
      this.configForm.set(null);
      this.resetDeleteStep();
    }
  }

  isProtectedSchool(slug: string): boolean {
    return PROTECTED_SCHOOL_SLUGS.has(slug);
  }

  startDeleteStep(): void {
    this.deleteSlugInput = '';
    this.deleteStepActive.set(true);
  }

  cancelDeleteStep(): void {
    this.resetDeleteStep();
  }

  resetDeleteStep(): void {
    this.deleteStepActive.set(false);
    this.deleteSlugInput = '';
  }

  deleteSlugMatches(): boolean {
    const form = this.configForm();
    if (!form) {
      return false;
    }
    return this.deleteSlugInput.trim().toLowerCase() === form.slug.toLowerCase();
  }

  confirmDeleteSchool(): void {
    const form = this.configForm();
    if (!form || !this.deleteSlugMatches()) {
      return;
    }
    this.deleteLoading.set(true);
    this.http
      .post(`${environment.apiUrl}/platform/schools/${form.id}/delete`, {
        slug: this.deleteSlugInput.trim().toLowerCase(),
      })
      .subscribe({
        next: () => {
          this.deleteLoading.set(false);
          this.configVisible.set(false);
          this.configForm.set(null);
          this.resetDeleteStep();
          this.messages.add({
            severity: 'success',
            summary: 'Colegio eliminado',
            detail: `${form.name} fue eliminado permanentemente.`,
          });
          this.loadPage(this.lastEvent ?? { first: 0, rows: this.pageSize });
        },
        error: (err) => {
          this.deleteLoading.set(false);
          this.messages.add({
            severity: 'error',
            summary: 'No se pudo eliminar',
            detail: apiErrorDetail(err, 'Error al eliminar el colegio'),
          });
        },
      });
  }

  saveConfig(): void {
    const form = this.configForm();
    if (!form) {
      return;
    }
    const name = form.name.trim();
    if (!name) {
      this.messages.add({
        severity: 'warn',
        summary: 'Nombre requerido',
        detail: 'Indique el nombre del colegio.',
      });
      return;
    }
    const currency = form.currency.trim().toUpperCase();
    if (currency.length !== 3) {
      this.messages.add({
        severity: 'warn',
        summary: 'Moneda inválida',
        detail: 'Use un código ISO de 3 letras (ej. GTQ).',
      });
      return;
    }

    this.configSaving.set(true);
    this.http
      .patch<SchoolRow>(`${environment.apiUrl}/platform/schools/${form.id}`, {
        name,
        status: form.status,
        subscription_plan_id: form.subscription_plan_id,
        billing_access_mode: form.billing_access_mode,
        currency,
        notes: form.notes?.trim() || null,
      })
      .subscribe({
        next: () => {
          this.configSaving.set(false);
          this.configVisible.set(false);
          this.configForm.set(null);
          this.messages.add({
            severity: 'success',
            summary: 'Guardado',
            detail: 'Colegio actualizado correctamente.',
          });
          this.loadPage(this.lastEvent ?? { first: 0, rows: this.pageSize });
        },
        error: (err) => {
          this.configSaving.set(false);
          this.messages.add({
            severity: 'error',
            summary: 'Error',
            detail: apiErrorDetail(err, 'No se pudo guardar'),
          });
        },
      });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Activo',
      inactive: 'Inactivo',
      trial: 'Prueba',
      suspended: 'Suspendido',
    };
    return labels[status] ?? status;
  }

  statusSeverity(status: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | undefined {
    const map: Record<string, 'success' | 'secondary' | 'info' | 'warn'> = {
      active: 'success',
      inactive: 'secondary',
      trial: 'info',
      suspended: 'warn',
    };
    return map[status];
  }

  billingLabel(mode: string): string {
    const labels: Record<string, string> = {
      full: 'Completo',
      payment_evidence_only: 'Solo comprobante',
    };
    return labels[mode] ?? mode;
  }
}
