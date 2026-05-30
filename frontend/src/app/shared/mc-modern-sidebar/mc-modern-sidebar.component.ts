import { NgClass } from '@angular/common';
import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { ThemeService } from '../../core/theme/theme.service';
import { McSidebarNavItem } from '../mc-sidebar-nav-item.model';

@Component({
  selector: 'mc-modern-sidebar',
  standalone: true,
  imports: [FormsModule, RouterLink, RouterLinkActive, NgClass],
  template: `
    <aside
      class="mc-sidebar flex shrink-0 flex-col transition-all duration-300 ease-in-out"
      [class.mc-sidebar--collapsed]="collapsed()"
    >
      <!-- Brand -->
      <div class="mc-sidebar__brand">
        <div class="mc-sidebar__logo" [ngClass]="logoAccentClass()">
          <i [class]="brandIcon()"></i>
        </div>
        @if (!collapsed()) {
          <div class="min-w-0">
            <p class="truncate text-sm font-bold mc-text">{{ brandTitle() }}</p>
            @if (brandSubtitle()) {
              <p class="truncate text-xs mc-text-muted">{{ brandSubtitle() }}</p>
            }
          </div>
        }
      </div>

      <!-- Search -->
      @if (showSearch() && !collapsed()) {
        <div class="mc-sidebar__search">
          <i class="pi pi-search text-[var(--mc-sidebar-icon)]"></i>
          <input
            type="search"
            placeholder="Buscar…"
            [(ngModel)]="searchQuery"
            (ngModelChange)="onSearchChange()"
          />
        </div>
      }
      @if (showSearch() && collapsed()) {
        <button type="button" class="mc-sidebar__search-icon" title="Buscar">
          <i class="pi pi-search"></i>
        </button>
      }

      <!-- Nav -->
      <nav class="mc-sidebar__nav flex-1 overflow-y-auto">
        @for (item of filteredItems(); track item.label) {
          <a
            [routerLink]="item.route"
            routerLinkActive="mc-sidebar__link--active"
            [routerLinkActiveOptions]="{ exact: item.exact ?? false }"
            class="mc-sidebar__link"
            [title]="collapsed() ? item.label : ''"
          >
            <i [class]="item.icon + ' mc-sidebar__link-icon'"></i>
            @if (!collapsed()) {
              <span class="truncate">{{ item.label }}</span>
              @if (item.badge !== undefined && item.badge !== null && item.badge !== '') {
                <span class="mc-sidebar__badge">{{ item.badge }}</span>
              }
            }
          </a>
        }
      </nav>

      <!-- User -->
      <div class="mc-sidebar__footer">
        <div class="mc-sidebar__user">
          <div class="mc-sidebar__avatar" [ngClass]="logoAccentClass()">
            {{ userInitials() }}
          </div>
          @if (!collapsed()) {
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold mc-text">{{ userName() }}</p>
              <p class="truncate text-xs mc-text-muted">{{ userEmail() }}</p>
            </div>
            <button
              type="button"
              class="mc-sidebar__action"
              [title]="theme.preferenceLabel()"
              (click)="theme.toggle()"
            >
              <i [class]="theme.isDark() ? 'pi pi-sun' : 'pi pi-moon'"></i>
            </button>
            <button type="button" class="mc-sidebar__logout" title="Salir" (click)="logoutClick.emit()">
              <i class="pi pi-sign-out"></i>
            </button>
          }
        </div>
        @if (collapsed()) {
          <button
            type="button"
            class="mc-sidebar__action mc-sidebar__action--collapsed"
            [title]="theme.preferenceLabel()"
            (click)="theme.toggle()"
          >
            <i [class]="theme.isDark() ? 'pi pi-sun' : 'pi pi-moon'"></i>
          </button>
          <button
            type="button"
            class="mc-sidebar__logout mc-sidebar__logout--collapsed"
            title="Salir"
            (click)="logoutClick.emit()"
          >
            <i class="pi pi-sign-out"></i>
          </button>
        }
      </div>

      <!-- Collapse toggle -->
      <button
        type="button"
        class="mc-sidebar__toggle"
        [title]="collapsed() ? 'Expandir menú' : 'Contraer menú'"
        (click)="toggleCollapsed()"
      >
        <i [class]="collapsed() ? 'pi pi-angle-right' : 'pi pi-angle-left'"></i>
      </button>
    </aside>
  `,
  styles: [
    `
      .mc-sidebar {
        position: relative;
        width: 16.5rem;
        height: calc(100vh - 1.5rem);
        max-height: calc(100vh - 1.5rem);
        margin: 0;
        padding: 1rem 0.75rem;
        background: var(--mc-sidebar-surface);
        border: 1px solid var(--mc-sidebar-border);
        border-radius: 1.25rem;
        box-shadow: var(--mc-sidebar-shadow);
      }

      .mc-sidebar--collapsed {
        width: 4.75rem;
        padding-left: 0.625rem;
        padding-right: 0.625rem;
      }

      .mc-sidebar__brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.25rem 0.5rem 1rem;
      }

      .mc-sidebar__logo {
        display: flex;
        height: 2.5rem;
        width: 2.5rem;
        shrink: 0;
        align-items: center;
        justify-content: center;
        border-radius: 0.75rem;
        color: white;
        font-size: 1.125rem;
      }

      .mc-sidebar__avatar.mc-sidebar__logo--staff,
      .mc-sidebar__logo.mc-sidebar__logo--staff {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
      }
      .mc-sidebar__avatar.mc-sidebar__logo--platform,
      .mc-sidebar__logo.mc-sidebar__logo--platform {
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
      }
      .mc-sidebar__avatar.mc-sidebar__logo--parent,
      .mc-sidebar__logo.mc-sidebar__logo--parent {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
      }
      .mc-sidebar__avatar.mc-sidebar__logo--student,
      .mc-sidebar__logo.mc-sidebar__logo--student {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      }

      .mc-sidebar__search {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0 0.375rem 0.75rem;
        padding: 0.5rem 0.875rem;
        border-radius: 9999px;
        background: var(--mc-sidebar-search-bg);
      }

      .mc-sidebar__search input {
        width: 100%;
        border: none;
        background: transparent;
        font-size: 0.875rem;
        color: var(--mc-sidebar-search-text);
        outline: none;
      }

      .mc-sidebar__search input::placeholder {
        color: var(--mc-sidebar-search-placeholder);
      }

      .mc-sidebar__search-icon {
        display: flex;
        margin: 0 auto 0.75rem;
        height: 2.5rem;
        width: 2.5rem;
        align-items: center;
        justify-content: center;
        border-radius: 0.75rem;
        color: var(--mc-sidebar-muted);
        background: var(--mc-sidebar-search-bg);
        border: none;
        cursor: pointer;
      }

      .mc-sidebar__nav {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 0 0.25rem;
      }

      .mc-sidebar__link {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.625rem 0.875rem;
        border-radius: 0.75rem;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--mc-sidebar-link);
        text-decoration: none;
        transition:
          background 0.15s ease,
          color 0.15s ease;
      }

      .mc-sidebar__link:hover {
        background: var(--mc-sidebar-link-hover-bg);
        color: var(--mc-sidebar-link-hover);
      }

      .mc-sidebar__link--active {
        background: var(--mc-primary) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgb(37 99 235 / 0.25);
      }

      .mc-sidebar__link--active .mc-sidebar__link-icon {
        color: #ffffff;
      }

      .mc-sidebar__link-icon {
        width: 1.25rem;
        text-align: center;
        font-size: 1rem;
        color: var(--mc-sidebar-icon);
        transition: color 0.15s ease;
      }

      .mc-sidebar--collapsed .mc-sidebar__link {
        justify-content: center;
        padding: 0.625rem;
      }

      .mc-sidebar__badge {
        margin-left: auto;
        min-width: 1.25rem;
        padding: 0.125rem 0.5rem;
        border-radius: 9999px;
        background: var(--mc-sidebar-badge-bg);
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--mc-sidebar-badge-text);
        text-align: center;
      }

      .mc-sidebar__link--active .mc-sidebar__badge {
        background: rgb(255 255 255 / 0.25);
        color: #ffffff;
      }

      .mc-sidebar__footer {
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid var(--mc-sidebar-footer-border);
      }

      .mc-sidebar__user {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 0.375rem 0.5rem;
      }

      .mc-sidebar__avatar {
        display: flex;
        height: 2.25rem;
        width: 2.25rem;
        shrink: 0;
        align-items: center;
        justify-content: center;
        border-radius: 9999px;
        font-size: 0.6875rem;
        font-weight: 700;
        color: white;
      }

      .mc-sidebar__action {
        display: flex;
        height: 2rem;
        width: 2rem;
        shrink: 0;
        align-items: center;
        justify-content: center;
        border: none;
        border-radius: 0.5rem;
        background: transparent;
        color: var(--mc-sidebar-action-text);
        cursor: pointer;
        transition:
          background 0.15s ease,
          color 0.15s ease;
      }

      .mc-sidebar__action:hover {
        background: var(--mc-sidebar-action-hover-bg);
        color: var(--mc-primary);
      }

      .mc-sidebar__action--collapsed {
        margin: 0.25rem auto 0;
      }

      .mc-sidebar__logout {
        display: flex;
        height: 2rem;
        width: 2rem;
        shrink: 0;
        align-items: center;
        justify-content: center;
        border: none;
        border-radius: 0.5rem;
        background: transparent;
        color: var(--mc-sidebar-action-text);
        cursor: pointer;
        transition:
          background 0.15s ease,
          color 0.15s ease;
      }

      .mc-sidebar__logout:hover {
        background: var(--mc-sidebar-logout-hover-bg);
        color: #dc2626;
      }

      .mc-sidebar__logout--collapsed {
        margin: 0.25rem auto 0;
      }

      .mc-sidebar__toggle {
        position: absolute;
        top: 50%;
        right: -0.75rem;
        z-index: 10;
        display: flex;
        height: 1.5rem;
        width: 1.5rem;
        align-items: center;
        justify-content: center;
        transform: translateY(-50%);
        border: 1px solid var(--mc-sidebar-toggle-border);
        border-radius: 9999px;
        background: var(--mc-sidebar-toggle-bg);
        color: var(--mc-sidebar-toggle-text);
        font-size: 0.625rem;
        cursor: pointer;
        box-shadow: 0 2px 6px rgb(15 23 42 / 0.08);
        transition:
          background 0.15s ease,
          color 0.15s ease;
      }

      .mc-sidebar__toggle:hover {
        background: var(--mc-sidebar-toggle-hover-bg);
        color: var(--mc-primary);
      }
    `,
  ],
})
export class McModernSidebarComponent {
  readonly theme = inject(ThemeService);

  readonly brandTitle = input('Mi Cole');
  readonly brandSubtitle = input<string | undefined>(undefined);
  readonly brandIcon = input('pi pi-graduation-cap');
  readonly accent = input<'staff' | 'platform' | 'parent' | 'student'>('staff');
  readonly navItems = input<McSidebarNavItem[]>([]);
  readonly userName = input('');
  readonly userEmail = input('');
  readonly showSearch = input(true);

  readonly logoutClick = output<void>();

  readonly collapsed = signal(false);
  searchQuery = '';
  private searchFilter = signal('');

  readonly filteredItems = signal<McSidebarNavItem[]>([]);

  constructor() {
    effect(() => {
      this.navItems();
      this.applyFilter();
    });
  }

  logoAccentClass(): string {
    return `mc-sidebar__logo--${this.accent()}`;
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

  toggleCollapsed(): void {
    this.collapsed.update((v) => !v);
  }

  onSearchChange(): void {
    this.searchFilter.set(this.searchQuery.trim().toLowerCase());
    this.applyFilter();
  }

  private applyFilter(): void {
    const items = this.navItems();
    const q = this.searchFilter();
    if (!q) {
      this.filteredItems.set(items);
      return;
    }
    this.filteredItems.set(items.filter((item) => item.label.toLowerCase().includes(q)));
  }
}
