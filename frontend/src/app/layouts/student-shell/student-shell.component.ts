import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-student-shell',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="placeholder">
      <h1>Portal estudiantes</h1>
      <p>Disponible en fase 11. Usuario: {{ auth.session()?.user?.email }}</p>
      <router-outlet />
    </div>
  `,
  styles: [
    `
      .placeholder {
        padding: 2rem;
      }
    `,
  ],
})
export class StudentShellComponent {
  readonly auth = inject(AuthService);
}
