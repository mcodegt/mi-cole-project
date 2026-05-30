import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, firstValueFrom, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  AuthSession,
  LoginContextResponse,
  LoginResponse,
  MeResponse,
  MembershipSummary,
  Portal,
} from '../models/auth.models';

const STORAGE_KEY = 'micole.session';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly api = environment.apiUrl;

  private readonly sessionState = signal<AuthSession | null>(this.readStorage());

  readonly session = this.sessionState.asReadonly();

  async initFromStorage(): Promise<void> {
    const stored = this.readStorage();
    if (!stored?.accessToken) {
      return;
    }
    try {
      const me = await firstValueFrom(
        this.http.get<MeResponse>(`${this.api}/auth/me`, {
          headers: { Authorization: `Bearer ${stored.accessToken}` },
        }),
      );
      this.applyMe(stored.accessToken, stored.refreshToken, me);
    } catch {
      this.clearSession();
    }
  }

  login(body: {
    email: string;
    password: string;
    portal: Portal;
    school_slug?: string;
    campus_slug?: string;
  }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.api}/auth/login`, body).pipe(
      tap((res) => this.applyLogin(res)),
    );
  }

  logout(): Observable<void> {
    const current = this.sessionState();
    const req = current?.refreshToken
      ? this.http.post<void>(`${this.api}/auth/logout`, { refresh_token: current.refreshToken })
      : null;
    this.clearSession();
    if (req) {
      return req;
    }
    return new Observable((sub) => {
      sub.next();
      sub.complete();
    });
  }

  refreshToken(): Observable<LoginResponse> {
    const current = this.sessionState();
    if (!current?.refreshToken) {
      throw new Error('Sin refresh token');
    }
    return this.http
      .post<LoginResponse>(`${this.api}/auth/refresh`, { refresh_token: current.refreshToken })
      .pipe(tap((res) => this.applyLogin(res)));
  }

  loadMemberships(): Observable<MembershipSummary[]> {
    return this.http.get<MembershipSummary[]>(`${this.api}/auth/memberships`);
  }

  switchSchool(membershipId: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.api}/auth/switch-school`, { membership_id: membershipId })
      .pipe(tap((res) => this.applyLogin(res)));
  }

  switchCampus(campusId: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.api}/auth/switch-campus`, { campus_id: campusId })
      .pipe(tap((res) => this.applyLogin(res)));
  }

  switchPortal(body: {
    portal: Portal;
    school_slug: string;
    campus_slug: string;
  }): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.api}/auth/switch-portal`, body)
      .pipe(tap((res) => this.applyLogin(res)));
  }

  changePassword(currentPassword: string, newPassword: string): Observable<void> {
    return this.http.post<void>(`${this.api}/auth/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  fetchLoginContext(params: {
    school_slug: string;
    campus_slug: string;
    portal: Portal;
  }): Observable<LoginContextResponse> {
    return this.http.get<LoginContextResponse>(`${this.api}/public/login-context`, { params });
  }

  hasPermission(code: string): boolean {
    const s = this.sessionState();
    if (!s) {
      return false;
    }
    if (s.portal === 'platform') {
      return s.platform?.permissions.includes(code) ?? false;
    }
    if (s.portal === 'staff') {
      return s.staff?.permissions.includes(code) ?? false;
    }
    return false;
  }

  isBillingRestricted(): boolean {
    return this.sessionState()?.staff?.billing_access_mode === 'payment_evidence_only';
  }

  portalHome(portal: Portal): string[] {
    switch (portal) {
      case 'platform':
        return ['/platform/schools'];
      case 'staff':
        return this.isBillingRestricted() ? ['/app/subscription'] : ['/app'];
      case 'parent':
        return ['/parent'];
      case 'student':
        return ['/student'];
      default:
        return ['/'];
    }
  }

  private applyLogin(res: LoginResponse): void {
    const session: AuthSession = {
      accessToken: res.access_token,
      refreshToken: res.refresh_token,
      portal: res.portal,
      user: res.user,
      schoolId: res.sid,
      membershipId: res.mid,
      parentId: res.pid,
      studentId: res.stid,
      campusId: res.campus_id,
      platform: res.platform,
      mustChangePassword: res.user.must_change_password ?? false,
      portals: res.portals ?? [],
    };
    this.sessionState.set(session);
    this.writeStorage(session);
    firstValueFrom(this.http.get<MeResponse>(`${this.api}/auth/me`)).then((me) =>
      this.applyMe(res.access_token, res.refresh_token, me),
    );
  }

  private applyMe(accessToken: string, refreshToken: string, me: MeResponse): void {
    const prev = this.sessionState();
    const session: AuthSession = {
      accessToken,
      refreshToken,
      portal: me.portal,
      user: me.user,
      schoolId: me.sid,
      membershipId: me.mid,
      parentId: me.pid,
      studentId: me.stid,
      campusId: me.campus_id ?? prev?.campusId,
      platform: me.platform,
      staff: me.staff,
      parent: me.parent,
      student: me.student,
      mustChangePassword: me.user.must_change_password ?? false,
      portals: me.portals ?? prev?.portals ?? [],
    };
    this.sessionState.set(session);
    this.writeStorage(session);
  }

  clearSession(): void {
    this.sessionState.set(null);
    sessionStorage.removeItem(STORAGE_KEY);
  }

  private readStorage(): AuthSession | null {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as AuthSession) : null;
    } catch {
      return null;
    }
  }

  private writeStorage(session: AuthSession): void {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }
}
