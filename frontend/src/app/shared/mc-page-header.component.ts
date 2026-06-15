import { Location } from '@angular/common';
import { Component, inject, input } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'mc-page-header',
  standalone: true,
  template: `
    <header class="mc-page-header">
      @if (showBack()) {
        <button type="button" class="mc-page-header__back" (click)="goBack()">
          <i class="pi pi-arrow-left" aria-hidden="true"></i>
          {{ backLabel() }}
        </button>
      }
      <div class="mc-page-header__row">
        <div class="mc-page-header__titles">
          <h1 class="mc-page-header__title">{{ title() }}</h1>
          @if (subtitle()) {
            <p class="mc-page-header__subtitle">{{ subtitle() }}</p>
          }
        </div>
        <div class="mc-page-header__actions">
          <ng-content />
        </div>
      </div>
    </header>
  `,
  styles: [
    `
      .mc-page-header {
        margin-bottom: 1.25rem;
      }

      .mc-page-header__back {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.85rem;
        padding: 0.5rem 0.9rem;
        border: 1px solid var(--mc-border);
        border-radius: 999px;
        background: var(--mc-surface);
        color: var(--mc-text);
        font-size: 0.875rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 1px 2px rgb(15 23 42 / 0.06);
        transition:
          background 0.15s,
          border-color 0.15s,
          box-shadow 0.15s;
      }

      .mc-page-header__back i {
        color: var(--mc-primary, #2563eb);
        font-size: 0.8rem;
      }

      .mc-page-header__back:hover {
        border-color: color-mix(in srgb, var(--mc-primary, #2563eb) 35%, var(--mc-border) 65%);
        background: color-mix(in srgb, var(--mc-primary, #2563eb) 6%, var(--mc-surface) 94%);
        box-shadow: 0 2px 6px rgb(15 23 42 / 0.08);
      }

      .mc-page-header__row {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }

      @media (min-width: 640px) {
        .mc-page-header {
          margin-bottom: 1.5rem;
        }

        .mc-page-header__row {
          flex-direction: row;
          align-items: flex-end;
          justify-content: space-between;
        }
      }

      .mc-page-header__title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--mc-text);
      }

      @media (min-width: 640px) {
        .mc-page-header__title {
          font-size: 1.5rem;
        }
      }

      .mc-page-header__subtitle {
        margin: 0.25rem 0 0;
        font-size: 0.875rem;
        color: var(--mc-text-muted);
      }

      .mc-page-header__actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.5rem;
      }
    `,
  ],
})
export class McPageHeaderComponent {
  private readonly location = inject(Location);
  private readonly router = inject(Router);

  title = input.required<string>();
  subtitle = input<string>();
  /** Muestra flecha de regreso (activo por defecto en módulos internos). */
  showBack = input(true);
  /** Ruta fija de regreso; si no se indica, usa el historial del navegador. */
  backRoute = input<string | undefined>(undefined);
  backLabel = input('Regresar');

  goBack(): void {
    const route = this.backRoute();
    if (route) {
      void this.router.navigateByUrl(route);
      return;
    }
    this.location.back();
  }
}
