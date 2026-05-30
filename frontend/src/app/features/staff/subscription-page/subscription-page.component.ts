import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { MessageService } from 'primeng/api';
import { FileUploadHandlerEvent, FileUploadModule } from 'primeng/fileupload';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';

import { AuthService } from '../../../core/auth/auth.service';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface SubscriptionDashboard {
  plan?: { name: string };
  billing: {
    billing_access_mode: string;
    has_pending_evidence?: boolean;
    current_period?: { period_month: number; period_year: number };
  };
  usage: Record<string, { current: number; max?: number }>;
}

@Component({
  selector: 'app-subscription-page',
  standalone: true,
  imports: [TagModule, ToastModule, FileUploadModule, McPageHeaderComponent],
  providers: [MessageService],
  templateUrl: './subscription-page.component.html',
})
export class SubscriptionPageComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);
  private readonly messages = inject(MessageService);

  readonly dashboard = signal<SubscriptionDashboard | null>(null);
  readonly uploading = signal(false);

  ngOnInit(): void {
    this.loadDashboard();
  }

  canUpload(): boolean {
    return this.auth.hasPermission('school.subscription.write');
  }

  onUpload(event: FileUploadHandlerEvent): void {
    const file = event.files[0];
    if (!file) {
      return;
    }
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('kind', 'monthly');

    this.uploading.set(true);
    this.http
      .post<{ message: string }>(`${environment.apiUrl}/subscription/payment-evidence`, formData)
      .subscribe({
        next: (res) => {
          this.uploading.set(false);
          this.messages.add({
            severity: 'success',
            summary: 'Comprobante enviado',
            detail: res.message,
          });
          this.loadDashboard();
        },
        error: (err) => {
          this.uploading.set(false);
          this.messages.add({
            severity: 'error',
            summary: 'Error al subir',
            detail: err?.error?.detail ?? 'No se pudo enviar el archivo',
          });
        },
      });
  }

  private loadDashboard(): void {
    this.http.get<SubscriptionDashboard>(`${environment.apiUrl}/subscription/dashboard`).subscribe({
      next: (res) => this.dashboard.set(res),
    });
  }
}
