import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SelectModule } from 'primeng/select';

import { BrandingThemeService } from '../../core/branding/branding-theme.service';
import { AuthService } from '../../core/auth/auth.service';
import { environment } from '../../../environments/environment';

interface CampusItem {
  id: string;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-staff-shell',
  standalone: true,
  imports: [FormsModule, RouterOutlet, RouterLink, RouterLinkActive, SelectModule],
  templateUrl: './staff-shell.component.html',
})
export class StaffShellComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);
  private readonly brandingTheme = inject(BrandingThemeService);

  readonly campuses = signal<CampusItem[]>([]);
  selectedCampusId = '';

  ngOnInit(): void {
    this.selectedCampusId = this.auth.session()?.campusId ?? '';
    this.http
      .get<{ items: CampusItem[] }>(`${environment.apiUrl}/campuses`, {
        params: { page: 1, limit: 100 },
      })
      .subscribe({
        next: (res) => {
          this.campuses.set(res.items);
          this.applyThemeForCampus(this.selectedCampusId);
        },
      });
  }

  onCampusChange(): void {
    if (!this.selectedCampusId) {
      return;
    }
    this.auth.switchCampus(this.selectedCampusId).subscribe({
      next: () => this.applyThemeForCampus(this.selectedCampusId),
    });
  }

  can(code: string): boolean {
    return this.auth.hasPermission(code);
  }

  restricted(): boolean {
    return this.auth.isBillingRestricted();
  }

  logout(): void {
    const slug = this.auth.session()?.staff?.school_slug ?? 'colegio-demo';
    const campus = this.campuses().find((c) => c.id === this.selectedCampusId)?.slug ?? 'sede-norte';
    this.auth.logout().subscribe(() => {
      window.location.href = `/login/staff/${slug}/${campus}`;
    });
  }

  private applyThemeForCampus(campusId: string): void {
    const staff = this.auth.session()?.staff;
    const campus = this.campuses().find((c) => c.id === campusId);
    if (staff && campus) {
      this.brandingTheme.loadStaffTheme(staff.school_slug, campus.slug);
    }
  }
}
