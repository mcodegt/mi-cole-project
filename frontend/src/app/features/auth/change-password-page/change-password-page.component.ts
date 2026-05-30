import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-change-password-page',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="flex min-h-screen items-center justify-center p-4" style="background: var(--mc-app-shell-bg)">
      <div class="mc-card w-full max-w-md">
        <h1 class="mb-2 text-xl font-bold mc-text">Cambiar contraseña</h1>
        <p class="mb-6 text-sm mc-text-muted">
          Debes establecer una contraseña nueva antes de continuar.
        </p>

        @if (error()) {
          <p class="mb-4 text-sm text-red-600 dark:text-red-400">{{ error() }}</p>
        }

        <form [formGroup]="form" (ngSubmit)="submit()" class="space-y-4">
          <div>
            <label class="mb-1 block text-xs font-medium mc-text-muted">Contraseña actual</label>
            <input type="password" class="mc-input" formControlName="current_password" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium mc-text-muted">Nueva contraseña</label>
            <input type="password" class="mc-input" formControlName="new_password" />
          </div>
          <button type="submit" class="mc-btn-primary w-full" [disabled]="form.invalid || loading()">
            {{ loading() ? 'Guardando…' : 'Guardar y continuar' }}
          </button>
        </form>
      </div>
    </div>
  `,
})
export class ChangePasswordPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly error = signal<string | null>(null);
  readonly loading = signal(false);

  readonly form = this.fb.nonNullable.group({
    current_password: ['', Validators.required],
    new_password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    const { current_password, new_password } = this.form.getRawValue();
    this.auth.changePassword(current_password, new_password).subscribe({
      next: () => {
        const portal = this.auth.session()?.portal ?? 'platform';
        void this.auth.initFromStorage().then(() => {
          this.loading.set(false);
          void this.router.navigate(this.auth.portalHome(portal));
        });
      },
      error: (err: { error?: { detail?: string } }) => {
        this.loading.set(false);
        this.error.set(err.error?.detail ?? 'No se pudo cambiar la contraseña');
      },
    });
  }
}
