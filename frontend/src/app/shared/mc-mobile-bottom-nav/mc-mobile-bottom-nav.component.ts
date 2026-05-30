import { Component, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { McSidebarNavItem } from '../mc-sidebar-nav-item.model';

@Component({
  selector: 'mc-mobile-bottom-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <nav
      class="mc-bottom-nav"
      [class.mc-bottom-nav--parent]="accent() === 'parent'"
      [class.mc-bottom-nav--student]="accent() === 'student'"
      aria-label="Navegación principal"
    >
      @for (item of items(); track item.label) {
        <a
          [routerLink]="item.route"
          routerLinkActive="mc-bottom-nav__link--active"
          [routerLinkActiveOptions]="{ exact: item.exact ?? false }"
          class="mc-bottom-nav__link"
        >
          <i [class]="item.icon"></i>
          <span>{{ item.label }}</span>
        </a>
      }
    </nav>
  `,
  styles: [
    `
      .mc-bottom-nav {
        position: fixed;
        right: 0;
        bottom: 0;
        left: 0;
        z-index: 30;
        display: flex;
        align-items: stretch;
        justify-content: space-around;
        gap: 0.25rem;
        padding: 0.375rem 0.5rem calc(0.375rem + env(safe-area-inset-bottom, 0px));
        border-top: 1px solid var(--mc-border);
        background: var(--mc-surface);
        box-shadow: 0 -4px 24px rgb(15 23 42 / 0.06);
      }

      .mc-bottom-nav__link {
        display: flex;
        min-width: 0;
        flex: 1;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.125rem;
        padding: 0.5rem 0.25rem;
        border-radius: 0.75rem;
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--mc-text-muted);
        text-decoration: none;
        transition:
          background 0.15s ease,
          color 0.15s ease;
      }

      .mc-bottom-nav__link i {
        font-size: 1.25rem;
      }

      .mc-bottom-nav__link--active {
        color: var(--mc-bottom-nav-active);
        background: var(--mc-bottom-nav-active-bg);
      }

      .mc-bottom-nav--parent {
        --mc-bottom-nav-active: #059669;
        --mc-bottom-nav-active-bg: rgb(5 150 105 / 0.12);
      }

      .mc-bottom-nav--student {
        --mc-bottom-nav-active: #6366f1;
        --mc-bottom-nav-active-bg: rgb(99 102 241 / 0.12);
      }

      :host-context(.dark) .mc-bottom-nav--parent {
        --mc-bottom-nav-active-bg: rgb(5 150 105 / 0.2);
      }

      :host-context(.dark) .mc-bottom-nav--student {
        --mc-bottom-nav-active-bg: rgb(99 102 241 / 0.2);
      }
    `,
  ],
})
export class McMobileBottomNavComponent {
  readonly items = input<McSidebarNavItem[]>([]);
  readonly accent = input<'parent' | 'student'>('parent');
}
