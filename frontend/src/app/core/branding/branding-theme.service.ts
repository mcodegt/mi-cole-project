import { Injectable, inject } from '@angular/core';

import { HttpClient } from '@angular/common/http';

import { AuthService } from '../auth/auth.service';
import { applySidebarTheme, ensureButtonAccent } from '../color/sidebar-color.utils';
import { environment } from '../../../environments/environment';

const DEFAULT_PRIMARY = '#2563eb';

interface SchoolProfileTheme {
  sidebar_color: string;
  sidebar_text_color: string;
  logo_url?: string | null;
}

@Injectable({ providedIn: 'root' })
export class BrandingThemeService {
  private readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);

  applyPrimary(hex: string | null | undefined): void {
    const color = ensureButtonAccent(hex);
    document.documentElement.style.setProperty('--mc-primary', color);
    document.documentElement.style.setProperty('--mc-primary-hover', color);
  }

  loadStaffTheme(_schoolSlug: string, _campusSlug: string): void {
    this.applyPrimary(DEFAULT_PRIMARY);
    this.loadStaffProfile();
  }

  loadStaffProfile(): void {
    const session = this.auth.session();
    if (!session?.staff || session.portal !== 'staff') {
      return;
    }
    this.http.get<SchoolProfileTheme>(`${environment.apiUrl}/school/profile`).subscribe({
      next: (profile) => {
        applySidebarTheme(profile.sidebar_color, profile.sidebar_text_color);
      },
      error: () => undefined,
    });
  }
}
