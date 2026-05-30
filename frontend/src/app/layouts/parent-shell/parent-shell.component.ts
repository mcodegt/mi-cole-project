import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-parent-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './parent-shell.component.html',
})
export class ParentShellComponent {
  readonly auth = inject(AuthService);

  logout(): void {
    const slug = this.auth.session()?.parent?.school_slug ?? 'colegio-demo';
    const campus = 'sede-norte';
    this.auth.logout().subscribe(() => {
      window.location.href = `/login/parent/${slug}/${campus}`;
    });
  }
}
