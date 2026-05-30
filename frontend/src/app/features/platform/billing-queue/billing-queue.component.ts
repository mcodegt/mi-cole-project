import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface QueueItem {
  id: string;
  school_name?: string;
  period_year?: number;
  period_month?: number;
  review_status: string;
  created_at: string;
}

@Component({
  selector: 'app-billing-queue',
  standalone: true,
  imports: [
    DatePipe,
    FormsModule,
    TableModule,
    TagModule,
    ButtonModule,
    DialogModule,
    ToastModule,
    McPageHeaderComponent,
  ],
  providers: [MessageService],
  templateUrl: './billing-queue.component.html',
})
export class BillingQueueComponent {
  private readonly http = inject(HttpClient);
  private readonly messages = inject(MessageService);

  readonly items = signal<QueueItem[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly rejectVisible = signal(false);
  readonly rejectReason = signal('');
  readonly selectedId = signal<string | null>(null);
  readonly actionLoading = signal(false);
  readonly pageSize = 25;

  loadPage(event: TableLazyLoadEvent): void {
    const rows = event.rows ?? this.pageSize;
    const page = Math.floor((event.first ?? 0) / rows) + 1;
    this.loading.set(true);
    this.http
      .get<{ items: QueueItem[]; total: number }>(`${environment.apiUrl}/platform/billing/queue`, {
        params: { page, limit: rows },
      })
      .subscribe({
        next: (res) => {
          this.items.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  approve(item: QueueItem): void {
    this.actionLoading.set(true);
    this.http
      .post(`${environment.apiUrl}/platform/billing/evidence/${item.id}/approve`, {})
      .subscribe({
        next: () => {
          this.actionLoading.set(false);
          this.messages.add({
            severity: 'success',
            summary: 'Aprobado',
            detail: `Comprobante de ${item.school_name ?? 'colegio'} aprobado.`,
          });
          this.loadPage({ first: 0, rows: this.pageSize });
        },
        error: (err) => {
          this.actionLoading.set(false);
          this.messages.add({
            severity: 'error',
            summary: 'Error',
            detail: err?.error?.detail ?? 'No se pudo aprobar',
          });
        },
      });
  }

  openReject(item: QueueItem): void {
    this.selectedId.set(item.id);
    this.rejectReason.set('');
    this.rejectVisible.set(true);
  }

  confirmReject(): void {
    const id = this.selectedId();
    const reason = this.rejectReason().trim();
    if (!id || !reason) {
      return;
    }
    this.actionLoading.set(true);
    this.http
      .post(`${environment.apiUrl}/platform/billing/evidence/${id}/reject`, { reason })
      .subscribe({
        next: () => {
          this.actionLoading.set(false);
          this.rejectVisible.set(false);
          this.messages.add({ severity: 'info', summary: 'Rechazado', detail: 'Comprobante rechazado.' });
          this.loadPage({ first: 0, rows: this.pageSize });
        },
        error: (err) => {
          this.actionLoading.set(false);
          this.messages.add({
            severity: 'error',
            summary: 'Error',
            detail: err?.error?.detail ?? 'No se pudo rechazar',
          });
        },
      });
  }
}
