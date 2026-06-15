import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { debounceTime, distinctUntilChanged, filter, switchMap, tap, catchError, of } from 'rxjs';

import { AuthService } from '../../../core/auth/auth.service';
import { CED_BRAND } from '../../../core/brand/ced-brand';
import { Portal, PublicSchoolSearchItem } from '../../../core/models/auth.models';

type SchoolPortal = Extract<Portal, 'staff' | 'parent' | 'student'>;

const PORTAL_LABELS: Record<SchoolPortal, string> = {
  staff: 'Administración y maestros',
  parent: 'Padres de familia',
  student: 'Estudiantes',
};

const PORTAL_CARDS: { value: SchoolPortal; label: string; hint: string; icon: string }[] = [
  { value: 'staff', label: 'Administración y maestros', hint: 'CED Admin · Maestros', icon: 'pi pi-building' },
  { value: 'parent', label: 'Padres de familia', hint: 'Portal padres de familia', icon: 'pi pi-heart' },
  { value: 'student', label: 'Estudiantes', hint: 'Portal estudiantes', icon: 'pi pi-book' },
];

const HERO_MODULES = [
  { label: 'CED Admin', icon: 'pi pi-building' },
  { label: 'CED Maestros', icon: 'pi pi-users' },
  { label: 'CED Padres de familia', icon: 'pi pi-heart' },
  { label: 'CED Estudiantes', icon: 'pi pi-book' },
];

@Component({
  selector: 'app-login-entry-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login-entry-page.component.html',
  styleUrl: './login-entry-page.component.css',
})
export class LoginEntryPageComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly brand = CED_BRAND;
  readonly portalLabels = PORTAL_LABELS;
  readonly portalCards = PORTAL_CARDS;
  readonly heroModules = HERO_MODULES;

  readonly searchControl = new FormControl('', { nonNullable: true });
  readonly portal = signal<SchoolPortal>('staff');
  readonly results = signal<PublicSchoolSearchItem[]>([]);
  readonly searching = signal(false);
  readonly searchError = signal<string | null>(null);
  readonly selectedSchool = signal<PublicSchoolSearchItem | null>(null);

  ngOnInit(): void {
    const portalParam = this.route.snapshot.queryParamMap.get('portal');
    if (portalParam === 'staff' || portalParam === 'parent' || portalParam === 'student') {
      this.portal.set(portalParam);
    }

    this.searchControl.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        tap(() => {
          this.searchError.set(null);
          this.selectedSchool.set(null);
        }),
        tap((q) => {
          if (q.trim().length < 2) {
            this.results.set([]);
            this.searching.set(false);
          }
        }),
        filter((q) => q.trim().length >= 2),
        tap(() => this.searching.set(true)),
        switchMap((q) =>
          this.auth.searchSchools(q.trim()).pipe(
            catchError(() => {
              this.searchError.set('No se pudo buscar colegios. Intenta de nuevo.');
              return of({ items: [], total: 0 });
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (res) => {
          this.results.set(res.items);
          this.searching.set(false);
        },
      });
  }

  setPortal(value: SchoolPortal): void {
    this.portal.set(value);
  }

  selectSchool(school: PublicSchoolSearchItem): void {
    if (school.campuses.length === 1) {
      this.goToLogin(school.slug, school.campuses[0].slug);
      return;
    }
    this.selectedSchool.set(school);
  }

  backToSearch(): void {
    this.selectedSchool.set(null);
  }

  selectCampus(campusSlug: string): void {
    const school = this.selectedSchool();
    if (!school) {
      return;
    }
    this.goToLogin(school.slug, campusSlug);
  }

  private goToLogin(schoolSlug: string, campusSlug: string): void {
    void this.router.navigate(['/login', this.portal(), schoolSlug, campusSlug]);
  }
}
