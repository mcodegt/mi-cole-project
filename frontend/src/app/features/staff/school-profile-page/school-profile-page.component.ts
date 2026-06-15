import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { FileUploadHandlerEvent, FileUploadModule } from 'primeng/fileupload';
import { ToastModule } from 'primeng/toast';

import { BrandingThemeService } from '../../../core/branding/branding-theme.service';
import {
  DEFAULT_SIDEBAR_COLOR,
  DEFAULT_SIDEBAR_TEXT_COLOR,
  suggestBackgroundFromImage,
  suggestTextColorForBackground,
} from '../../../core/color/sidebar-color.utils';
import { AuthService } from '../../../core/auth/auth.service';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface SchoolProfile {
  school_id: string;
  school_name: string;
  logo_url?: string | null;
  sidebar_color: string;
  sidebar_text_color: string;
  suggested_text_color: string;
}

@Component({
  selector: 'app-school-profile-page',
  standalone: true,
  imports: [FormsModule, ToastModule, FileUploadModule, McPageHeaderComponent],
  providers: [MessageService],
  templateUrl: './school-profile-page.component.html',
  styleUrl: './school-profile-page.component.css',
})
export class SchoolProfilePageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly messages = inject(MessageService);
  private readonly brandingTheme = inject(BrandingThemeService);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly suggestingFromLogo = signal(false);

  schoolName = '';
  logoUrl = '';
  sidebarColor = DEFAULT_SIDEBAR_COLOR;
  sidebarTextColor = DEFAULT_SIDEBAR_TEXT_COLOR;

  readonly suggestedTextColor = computed(() => suggestTextColorForBackground(this.sidebarColor));

  ngOnInit(): void {
    this.loadProfile();
  }

  canWrite(): boolean {
    return this.auth.hasPermission('school.settings.write');
  }

  onSidebarColorChange(): void {
    this.sidebarTextColor = this.suggestedTextColor();
  }

  applySuggestedTextColor(): void {
    this.sidebarTextColor = this.suggestedTextColor();
  }

  async suggestColorFromLogo(): Promise<void> {
    if (!this.logoUrl.trim()) {
      this.messages.add({
        severity: 'warn',
        summary: 'Sin logo',
        detail: 'Suba o indique la URL del logo primero.',
      });
      return;
    }
    this.suggestingFromLogo.set(true);
    const suggested = await suggestBackgroundFromImage(this.logoUrl.trim());
    this.suggestingFromLogo.set(false);
    if (!suggested) {
      this.messages.add({
        severity: 'warn',
        summary: 'No se pudo analizar',
        detail: 'Pruebe subir el archivo o use una URL del mismo sitio (CORS).',
      });
      return;
    }
    this.sidebarColor = suggested;
    this.sidebarTextColor = suggestTextColorForBackground(suggested);
    this.messages.add({
      severity: 'info',
      summary: 'Color sugerido',
      detail: 'Se aplicó un color base del logo. Revise la vista previa y guarde.',
    });
  }

  onLogoUpload(event: FileUploadHandlerEvent): void {
    const file = event.files[0];
    if (!file || !this.canWrite()) {
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    this.http.post<SchoolProfile>(`${environment.apiUrl}/school/profile/logo`, formData).subscribe({
      next: (profile) => {
        this.applyProfile(profile);
        this.brandingTheme.loadStaffProfile();
        this.messages.add({ severity: 'success', summary: 'Logo actualizado' });
      },
      error: () => {
        this.messages.add({ severity: 'error', summary: 'Error', detail: 'No se pudo subir el logo.' });
      },
    });
  }

  save(): void {
    if (!this.canWrite()) {
      return;
    }
    this.saving.set(true);
    this.http
      .patch<SchoolProfile>(`${environment.apiUrl}/school/profile`, {
        logo_url: this.logoUrl.trim() || null,
        sidebar_color: this.sidebarColor,
        sidebar_text_color: this.sidebarTextColor,
      })
      .subscribe({
        next: (profile) => {
          this.applyProfile(profile);
          this.brandingTheme.loadStaffProfile();
          this.saving.set(false);
          this.messages.add({ severity: 'success', summary: 'Perfil guardado' });
        },
        error: () => {
          this.saving.set(false);
          this.messages.add({ severity: 'error', summary: 'Error', detail: 'No se pudo guardar.' });
        },
      });
  }

  clearLogo(): void {
    if (!this.canWrite()) {
      return;
    }
    this.logoUrl = '';
    this.saveWithExtras({ clear_logo: true });
  }

  restoreDefaultColors(): void {
    if (!this.canWrite()) {
      return;
    }
    this.sidebarColor = DEFAULT_SIDEBAR_COLOR;
    this.sidebarTextColor = DEFAULT_SIDEBAR_TEXT_COLOR;
  }

  private saveWithExtras(body: Record<string, unknown>): void {
    this.saving.set(true);
    this.http.patch<SchoolProfile>(`${environment.apiUrl}/school/profile`, body).subscribe({
      next: (profile) => {
        this.applyProfile(profile);
        this.brandingTheme.loadStaffProfile();
        this.saving.set(false);
        this.messages.add({ severity: 'success', summary: 'Perfil actualizado' });
      },
      error: () => {
        this.saving.set(false);
        this.messages.add({ severity: 'error', summary: 'Error', detail: 'No se pudo actualizar.' });
      },
    });
  }

  private loadProfile(): void {
    this.loading.set(true);
    this.http.get<SchoolProfile>(`${environment.apiUrl}/school/profile`).subscribe({
      next: (profile) => {
        this.applyProfile(profile);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private applyProfile(profile: SchoolProfile): void {
    this.schoolName = profile.school_name;
    this.logoUrl = profile.logo_url ?? '';
    this.sidebarColor = profile.sidebar_color;
    this.sidebarTextColor = profile.sidebar_text_color;
  }
}
