import { Component, input } from '@angular/core';

@Component({
  selector: 'mc-page-header',
  standalone: true,
  template: `
    <div class="mb-5 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-xl font-bold tracking-tight mc-text sm:text-2xl">{{ title() }}</h1>
        @if (subtitle()) {
          <p class="mt-1 text-sm mc-text-muted">{{ subtitle() }}</p>
        }
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <ng-content />
      </div>
    </div>
  `,
})
export class McPageHeaderComponent {
  title = input.required<string>();
  subtitle = input<string>();
}
