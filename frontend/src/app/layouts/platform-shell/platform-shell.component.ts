import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-platform-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './platform-shell.component.html',
})
export class PlatformShellComponent {
  readonly auth = inject(AuthService);

  logout(): void {
    this.auth.logout().subscribe(() => {
      window.location.href = '/login/platform';
    });
  }
}
