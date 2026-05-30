import { Injectable, signal } from '@angular/core';

export type ThemePreference = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'mc-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly preference = signal<ThemePreference>(this.readStored());
  readonly isDark = signal(false);

  init(): void {
    this.applyResolved(this.resolveDark());

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (this.preference() === 'system') {
        this.applyResolved(this.resolveDark());
      }
    });
  }

  toggle(): void {
    this.setPreference(this.isDark() ? 'light' : 'dark');
  }

  setPreference(mode: ThemePreference): void {
    this.preference.set(mode);
    localStorage.setItem(STORAGE_KEY, mode);
    this.applyResolved(this.resolveDark());
  }

  preferenceLabel(): string {
    return this.isDark() ? 'Modo claro' : 'Modo oscuro';
  }

  private resolveDark(): boolean {
    const pref = this.preference();
    if (pref === 'dark') {
      return true;
    }
    if (pref === 'light') {
      return false;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  private applyResolved(dark: boolean): void {
    this.isDark.set(dark);
    document.documentElement.classList.toggle('dark', dark);
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  }

  private readStored(): ThemePreference {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
    return 'system';
  }
}
