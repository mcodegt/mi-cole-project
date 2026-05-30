import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-campuses-list',
  standalone: true,
  imports: [McPageHeaderComponent],
  template: `
    <mc-page-header title="Sedes" subtitle="Campus del colegio" />

    <ul class="mc-card divide-y divide-slate-100 p-0">
      @for (c of campuses(); track c.id) {
        <li class="flex items-center justify-between px-5 py-3">
          <span class="font-medium mc-text">{{ c.name }}</span>
          <span class="text-sm mc-text-muted">{{ c.slug }}</span>
        </li>
      }
    </ul>
  `,
})
export class CampusesListComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly campuses = signal<{ id: string; name: string; slug: string }[]>([]);

  ngOnInit(): void {
    this.http
      .get<{ items: { id: string; name: string; slug: string }[] }>(
        `${environment.apiUrl}/campuses`,
        { params: { page: 1, limit: 100 } },
      )
      .subscribe((res) => this.campuses.set(res.items));
  }
}
