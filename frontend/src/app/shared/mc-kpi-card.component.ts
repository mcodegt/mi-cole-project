import { Component, input } from '@angular/core';

@Component({
  selector: 'mc-kpi-card',
  standalone: true,
  template: `
    <div class="mc-card">
      <p class="text-xs font-semibold uppercase tracking-wide mc-text-muted">{{ label() }}</p>
      <p class="mt-2 text-2xl font-bold mc-text-accent sm:text-3xl">{{ value() }}</p>
      @if (hint()) {
        <p class="mt-1 text-xs mc-text-subtle">{{ hint() }}</p>
      }
    </div>
  `,
})
export class McKpiCardComponent {
  label = input.required<string>();
  value = input.required<string | number>();
  hint = input<string>();
}
