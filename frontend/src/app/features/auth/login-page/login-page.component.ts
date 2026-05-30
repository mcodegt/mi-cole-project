import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { BrandingThemeService } from '../../../core/branding/branding-theme.service';
import { AuthService } from '../../../core/auth/auth.service';
import { LoginContextResponse, Portal } from '../../../core/models/auth.models';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login-page.component.html',
})
export class LoginPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly brandingTheme = inject(BrandingThemeService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly branding = signal<LoginContextResponse | null>(null);
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
      this.auth
        .fetchLoginContext({
          school_slug: this.schoolSlug,
          campus_slug: this.campusSlug,
          portal: this.portal,
        })
        .subscribe({
          next: (ctx) => {
            this.branding.set(ctx);
            this.brandingTheme.applyPrimary(ctx.branding.primary_color_hex);
          },
          error: () => this.error.set('Login no disponible para este portal'),
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
        next: () => {
          this.loading.set(false);
          void this.router.navigate(this.auth.portalHome(this.portal));
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(err?.error?.detail ?? 'Credenciales inválidas');
        },
      });
  }

  accentColor(): string {
    return this.branding()?.branding.primary_color_hex ?? '#2563eb';
  }
}
