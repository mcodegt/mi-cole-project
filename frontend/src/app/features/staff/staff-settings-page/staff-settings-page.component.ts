import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../core/auth/auth.service';
import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';

interface SettingsLink {
  title: string;
  description: string;
  icon: string;
  route: string;
}

@Component({
  selector: 'app-staff-settings-page',
  standalone: true,
  imports: [RouterLink, McPageHeaderComponent],
  templateUrl: './staff-settings-page.component.html',
  styleUrl: './staff-settings-page.component.css',
})
export class StaffSettingsPageComponent {
  private readonly auth = inject(AuthService);

  readonly links = computed<SettingsLink[]>(() => {
    this.auth.session();
    const items: SettingsLink[] = [];
    if (this.auth.isSchoolOwner() || this.can('school.settings.read')) {
      items.push({
        title: 'Perfil del colegio',
        description: 'Logo, colores del menú y apariencia del portal.',
        icon: 'pi pi-palette',
        route: '/app/school-profile',
      });
    }
    if (this.can('school.team.read')) {
      items.push({
        title: 'Equipo',
        description: 'Membresías staff, roles y accesos del colegio.',
        icon: 'pi pi-id-card',
        route: '/app/team',
      });
    }
    if (this.can('school.subscription.read')) {
      items.push({
        title: 'Suscripción',
        description: 'Plan, límites, facturación y comprobantes de pago.',
        icon: 'pi pi-credit-card',
        route: '/app/subscription',
      });
    }
    return items;
  });

  private can(code: string): boolean {
    return this.auth.hasPermission(code);
  }
}
