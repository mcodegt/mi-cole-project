import { NgClass } from '@angular/common';
import { Component, inject, input, output, signal } from '@angular/core';

import { ThemeService } from '../../core/theme/theme.service';

@Component({
  selector: 'mc-portal-mobile-header',
  standalone: true,
  imports: [NgClass],
  template: `
    <header class="mc-portal-header">
      <div class="mc-portal-header__brand">
        <div class="mc-portal-header__logo" [ngClass]="logoAccentClass()">
          <i [class]="brandIcon()"></i>
        </div>
        <div class="min-w-0">
          <p class="truncate text-sm font-bold mc-text">{{ brandTitle() }}</p>
          @if (brandSubtitle()) {
            <p class="truncate text-xs mc-text-muted">{{ brandSubtitle() }}</p>
          }
        </div>
      </div>

      <button
        type="button"
        class="mc-portal-header__menu-btn"
        aria-label="Menú de cuenta"
        [attr.aria-expanded]="menuOpen()"
        (click)="toggleMenu()"
      >
        <i class="pi pi-ellipsis-v"></i>
      </button>
    </header>

    @if (menuOpen()) {
      <button
        type="button"
        class="mc-portal-header__backdrop"
        aria-label="Cerrar menú"
        (click)="closeMenu()"
      ></button>
      <div class="mc-portal-header__menu" role="menu">
        <div class="mc-portal-header__menu-user">
          <div class="mc-portal-header__avatar" [ngClass]="logoAccentClass()">
            {{ userInitials() }}
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold mc-text">{{ userName() }}</p>
            @if (userEmail()) {
              <p class="truncate text-xs mc-text-muted">{{ userEmail() }}</p>
            }
          </div>
        </div>
        <button type="button" class="mc-portal-header__menu-item" role="menuitem" (click)="onThemeToggle()">
          <i [class]="theme.isDark() ? 'pi pi-sun' : 'pi pi-moon'"></i>
          {{ theme.preferenceLabel() }}
        </button>
        <button type="button" class="mc-portal-header__menu-item mc-portal-header__menu-item--danger" role="menuitem" (click)="onLogout()">
          <i class="pi pi-sign-out"></i>
          Cerrar sesión
        </button>
      </div>
    }
  `,
  styles: [
    `
      .mc-portal-header {
        position: sticky;
        top: 0;
        z-index: 20;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        padding: calc(0.75rem + env(safe-area-inset-top, 0px)) 1rem 0.75rem;
        border-bottom: 1px solid var(--mc-border);
        background: var(--mc-surface);
      }

      .mc-portal-header__brand {
        display: flex;
        min-width: 0;
        align-items: center;
        gap: 0.625rem;
      }

      .mc-portal-header__logo,
      .mc-portal-header__avatar {
        display: flex;
        height: 2.25rem;
        width: 2.25rem;
        shrink: 0;
        align-items: center;
        justify-content: center;
        border-radius: 0.625rem;
        color: white;
        font-size: 1rem;
      }

      .mc-portal-header__avatar {
        border-radius: 9999px;
        font-size: 0.6875rem;
        font-weight: 700;
      }

      .mc-portal-header__logo--parent,
      .mc-portal-header__avatar.mc-portal-header__logo--parent {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
      }

      .mc-portal-header__logo--student,
      .mc-portal-header__avatar.mc-portal-header__logo--student {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      }

      .mc-portal-header__menu-btn {
        display: flex;
        height: 2.5rem;
        width: 2.5rem;
        shrink: 0;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--mc-border);
        border-radius: 0.75rem;
        background: var(--mc-surface-muted);
        color: var(--mc-text-muted);
        cursor: pointer;
      }

      .mc-portal-header__backdrop {
        position: fixed;
        inset: 0;
        z-index: 40;
        border: none;
        background: rgb(15 23 42 / 0.35);
        cursor: pointer;
      }

      .mc-portal-header__menu {
        position: fixed;
        top: calc(3.75rem + env(safe-area-inset-top, 0px));
        right: 0.75rem;
        z-index: 50;
        width: min(18rem, calc(100vw - 1.5rem));
        overflow: hidden;
        border: 1px solid var(--mc-border);
        border-radius: 1rem;
        background: var(--mc-surface);
        box-shadow: 0 12px 40px rgb(15 23 42 / 0.15);
      }

      .mc-portal-header__menu-user {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 1rem;
        border-bottom: 1px solid var(--mc-border);
      }

      .mc-portal-header__menu-item {
        display: flex;
        width: 100%;
        align-items: center;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        border: none;
        background: transparent;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--mc-text);
        text-align: left;
        cursor: pointer;
      }

      .mc-portal-header__menu-item:hover {
        background: var(--mc-surface-muted);
      }

      .mc-portal-header__menu-item--danger {
        color: #dc2626;
      }
    `,
  ],
})
export class McPortalMobileHeaderComponent {
  readonly theme = inject(ThemeService);

  readonly brandTitle = input('Mi Cole');
  readonly brandSubtitle = input<string | undefined>(undefined);
  readonly brandIcon = input('pi pi-graduation-cap');
  readonly accent = input<'parent' | 'student'>('parent');
  readonly userName = input('');
  readonly userEmail = input('');

  readonly logoutClick = output<void>();

  readonly menuOpen = signal(false);

  logoAccentClass(): string {
    return `mc-portal-header__logo--${this.accent()}`;
  }

  userInitials(): string {
    const parts = this.userName()
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    if (parts.length === 0) {
      return '?';
    }
    if (parts.length === 1) {
      return parts[0].slice(0, 2).toUpperCase();
    }
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  toggleMenu(): void {
    this.menuOpen.update((v) => !v);
  }

  closeMenu(): void {
    this.menuOpen.set(false);
  }

  onThemeToggle(): void {
    this.theme.toggle();
    this.closeMenu();
  }

  onLogout(): void {
    this.closeMenu();
    this.logoutClick.emit();
  }
}
