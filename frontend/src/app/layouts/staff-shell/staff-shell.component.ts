import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { SelectModule } from 'primeng/select';

import { BrandingThemeService } from '../../core/branding/branding-theme.service';
import { AuthService } from '../../core/auth/auth.service';
import { McModernSidebarComponent } from '../../shared/mc-modern-sidebar/mc-modern-sidebar.component';
import { McSidebarNavItem } from '../../shared/mc-sidebar-nav-item.model';
import { environment } from '../../../environments/environment';

interface CampusItem {
  id: string;
  name: string;
  slug: string;
}

@Component({
  selector: 'app-staff-shell',
  standalone: true,
  imports: [FormsModule, RouterOutlet, SelectModule, McModernSidebarComponent],
  templateUrl: './staff-shell.component.html',
})
export class StaffShellComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);
  private readonly brandingTheme = inject(BrandingThemeService);

  readonly campuses = signal<CampusItem[]>([]);
  selectedCampusId = '';

  readonly navItems = computed<McSidebarNavItem[]>(() => {
    if (this.restricted()) {
      return [{ label: 'Suscripción', icon: 'pi pi-wallet', route: '/app/subscription' }];
    }
    const items: McSidebarNavItem[] = [
      { label: 'Inicio', icon: 'pi pi-home', route: '/app', exact: true },
    ];
    if (this.can('school.campuses.read')) {
      items.push({ label: 'Sedes', icon: 'pi pi-building', route: '/app/campuses' });
    }
    if (this.can('school.students.read')) {
      items.push({ label: 'Estudiantes', icon: 'pi pi-users', route: '/app/students' });
    }
    if (this.can('school.parents.read')) {
      items.push({ label: 'Padres', icon: 'pi pi-user', route: '/app/parents' });
    }
    if (this.can('school.team.read')) {
      items.push({ label: 'Equipo', icon: 'pi pi-id-card', route: '/app/team' });
    }
    if (this.can('school.subscription.read')) {
      items.push({ label: 'Suscripción', icon: 'pi pi-credit-card', route: '/app/subscription' });
    }
    return items;
  });

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

  canSwitchToParent(): boolean {
    return (this.auth.session()?.portals ?? []).includes('parent');
  }

  switchToParentPortal(): void {
    const staff = this.auth.session()?.staff;
    const campus = this.campuses().find((c) => c.id === this.selectedCampusId);
    if (!staff || !campus) {
      return;
    }
    this.auth
      .switchPortal({
        portal: 'parent',
        school_slug: staff.school_slug,
        campus_slug: campus.slug,
      })
      .subscribe({
        next: () => {
          window.location.href = '/parent';
        },
      });
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
