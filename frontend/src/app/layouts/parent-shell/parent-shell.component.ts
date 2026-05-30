import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { McMobileBottomNavComponent } from '../../shared/mc-mobile-bottom-nav/mc-mobile-bottom-nav.component';
import { McModernSidebarComponent } from '../../shared/mc-modern-sidebar/mc-modern-sidebar.component';
import { McPortalMobileHeaderComponent } from '../../shared/mc-portal-mobile-header/mc-portal-mobile-header.component';
import { McSidebarNavItem } from '../../shared/mc-sidebar-nav-item.model';

@Component({
  selector: 'app-parent-shell',
  standalone: true,
  imports: [
    RouterOutlet,
    McModernSidebarComponent,
    McPortalMobileHeaderComponent,
    McMobileBottomNavComponent,
  ],
  templateUrl: './parent-shell.component.html',
})
export class ParentShellComponent {
  readonly auth = inject(AuthService);

  readonly navItems: McSidebarNavItem[] = [
    { label: 'Inicio', icon: 'pi pi-home', route: '/parent', exact: true },
    { label: 'Tareas', icon: 'pi pi-book', route: '/parent/assignments' },
  ];

  logout(): void {
    const slug = this.auth.session()?.parent?.school_slug ?? 'colegio-demo';
    const campus = 'sede-norte';
    this.auth.logout().subscribe(() => {
      window.location.href = `/login/parent/${slug}/${campus}`;
    });
  }
}
