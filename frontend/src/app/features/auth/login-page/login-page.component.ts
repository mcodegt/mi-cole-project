import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { BrandingThemeService } from '../../../core/branding/branding-theme.service';
import { ensureButtonAccent } from '../../../core/color/sidebar-color.utils';
import { CED_AUTH_ROUTES, CED_BRAND } from '../../../core/brand/ced-brand';
import { AuthService } from '../../../core/auth/auth.service';
import { LoginContextResponse, Portal } from '../../../core/models/auth.models';

type SchoolPortal = Extract<Portal, 'staff' | 'parent' | 'student'>;

interface HeroFeature {
  icon: string;
  label: string;
}

interface PortalLoginCopy {
  badge: string;
  welcome: string;
  lead: string;
  submit: string;
  emailLabel: string;
  emailPlaceholder: string;
  heroFeatures: HeroFeature[];
}

const PORTAL_LOGIN_COPY: Record<SchoolPortal, PortalLoginCopy> = {
  staff: {
    badge: 'Administración',
    welcome: 'Bienvenido, equipo del colegio',
    lead: 'Gestiona sedes, estudiantes y operación diaria.',
    submit: 'Entrar al panel',
    emailLabel: 'Correo institucional',
    emailPlaceholder: 'tu@colegio.edu',
    heroFeatures: [
      { icon: 'pi pi-building', label: 'Administración' },
      { icon: 'pi pi-users', label: 'Maestros' },
      { icon: 'pi pi-chart-bar', label: 'Reportes' },
    ],
  },
  parent: {
    badge: 'Padres de familia',
    welcome: 'Bienvenido, padre de familia',
    lead: 'Consulta avisos, calificaciones y comunicación del colegio.',
    submit: 'Entrar al portal',
    emailLabel: 'Correo registrado',
    emailPlaceholder: 'padre@ejemplo.com',
    heroFeatures: [
      { icon: 'pi pi-bell', label: 'Avisos' },
      { icon: 'pi pi-star', label: 'Calificaciones' },
      { icon: 'pi pi-comments', label: 'Comunicación' },
    ],
  },
  student: {
    badge: 'Estudiantes',
    welcome: 'Bienvenido, estudiante',
    lead: 'Revisa tareas, entregas y avisos de tu sede.',
    submit: 'Entrar al portal',
    emailLabel: 'Correo estudiantil',
    emailPlaceholder: 'estudiante@ejemplo.com',
    heroFeatures: [
      { icon: 'pi pi-book', label: 'Tareas' },
      { icon: 'pi pi-upload', label: 'Entregas' },
      { icon: 'pi pi-megaphone', label: 'Avisos' },
    ],
  },
};

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.css',
})
export class LoginPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly brandingTheme = inject(BrandingThemeService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly branding = signal<LoginContextResponse | null>(null);
  readonly brandingLoading = signal(false);
  readonly ced = CED_BRAND;
  readonly authRoutes = CED_AUTH_ROUTES;
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);

  portal: Portal = 'platform';
  schoolSlug = '';
  campusSlug = '';

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  ngOnInit(): void {
    const dataPortal = this.route.snapshot.data['portal'] as Portal | undefined;
    this.portal = (this.route.snapshot.paramMap.get('portal') as Portal) ?? dataPortal ?? 'platform';
    this.schoolSlug = this.route.snapshot.paramMap.get('schoolSlug') ?? '';
    this.campusSlug = this.route.snapshot.paramMap.get('campusSlug') ?? '';

    if (this.portal !== 'platform' && this.schoolSlug && this.campusSlug) {
      this.brandingLoading.set(true);
      this.auth
        .fetchLoginContext({
          school_slug: this.schoolSlug,
          campus_slug: this.campusSlug,
          portal: this.portal,
        })
        .subscribe({
          next: (ctx) => {
            this.branding.set(ctx);
            this.brandingLoading.set(false);
            this.brandingTheme.applyPrimary(ensureButtonAccent(ctx.branding.primary_color_hex));
          },
          error: () => {
            this.brandingLoading.set(false);
            this.error.set('Login no disponible para este portal');
          },
        });
    }
  }

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    const { email, password } = this.form.getRawValue();
    this.auth
      .login({
        email,
        password,
        portal: this.portal,
        school_slug: this.portal !== 'platform' ? this.schoolSlug : undefined,
        campus_slug: this.portal !== 'platform' ? this.campusSlug : undefined,
      })
      .subscribe({
        next: (res) => {
          this.loading.set(false);
          if (res.user.must_change_password) {
            void this.router.navigate(['/change-password']);
            return;
          }
          void this.router.navigate(this.auth.portalHome(this.portal));
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(err?.error?.detail ?? 'Credenciales inválidas');
        },
      });
  }

  portalCopy(): PortalLoginCopy | null {
    if (this.portal === 'staff' || this.portal === 'parent' || this.portal === 'student') {
      return PORTAL_LOGIN_COPY[this.portal];
    }
    return null;
  }

  loginAccentColor(): string {
    return ensureButtonAccent(this.branding()?.branding.primary_color_hex);
  }

  accentColor(): string {
    return this.loginAccentColor();
  }

  schoolInitials(name: string): string {
    return name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word[0]?.toUpperCase() ?? '')
      .join('');
  }
}
