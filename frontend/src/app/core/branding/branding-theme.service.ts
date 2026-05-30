import { Injectable, inject } from '@angular/core';

import { AuthService } from '../auth/auth.service';
import { Portal } from '../models/auth.models';

const DEFAULT_PRIMARY = '#2563eb';

@Injectable({ providedIn: 'root' })
export class BrandingThemeService {
  private readonly auth = inject(AuthService);

  applyPrimary(hex: string | null | undefined): void {
    const color = hex && hex.startsWith('#') ? hex : DEFAULT_PRIMARY;
    document.documentElement.style.setProperty('--mc-primary', color);
    document.documentElement.style.setProperty('--mc-primary-hover', color);
  }

  loadStaffTheme(schoolSlug: string, campusSlug: string): void {
    this.auth
      .fetchLoginContext({
        school_slug: schoolSlug,
        campus_slug: campusSlug,
        portal: 'staff' as Portal,
      })
      .subscribe({
        next: (ctx) => this.applyPrimary(ctx.branding.primary_color_hex),
        error: () => this.applyPrimary(DEFAULT_PRIMARY),
      });
  }
}
