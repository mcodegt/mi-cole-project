import { Injectable } from '@angular/core';

const STORAGE_KEY = 'mc-theme';

/** Tema fijo claro: la identidad visual del colegio se configura por perfil, no por dark mode. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  init(): void {
    try {
      localStorage.setItem(STORAGE_KEY, 'light');
    } catch {
      /* ignore */
    }
    document.documentElement.classList.remove('dark');
    document.documentElement.setAttribute('data-theme', 'light');
  }
}
