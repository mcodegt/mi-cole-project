import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { McModernSidebarComponent } from '../../shared/mc-modern-sidebar/mc-modern-sidebar.component';
import { McSidebarNavItem } from '../../shared/mc-sidebar-nav-item.model';

@Component({
  selector: 'app-platform-shell',
  standalone: true,
  imports: [RouterOutlet, McModernSidebarComponent],
  templateUrl: './platform-shell.component.html',
})
export class PlatformShellComponent {
  readonly auth = inject(AuthService);

  readonly navItems: McSidebarNavItem[] = [
    { label: 'Colegios', icon: 'pi pi-building', route: '/platform/schools' },
    { label: 'Facturación', icon: 'pi pi-inbox', route: '/platform/billing' },
  ];

  logout(): void {
    this.auth.logout().subscribe(() => {
      window.location.href = '/login/platform';
    });
  }
}
