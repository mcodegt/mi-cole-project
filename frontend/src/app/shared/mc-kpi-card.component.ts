import { Component, input } from '@angular/core';

@Component({
  selector: 'mc-kpi-card',
  standalone: true,
  template: `
    <div class="mc-card">
      <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ label() }}</p>
      <p class="mt-2 text-3xl font-bold text-primary">{{ value() }}</p>
      @if (hint()) {
        <p class="mt-1 text-xs text-slate-500">{{ hint() }}</p>
      }
    </div>
  `,
})
export class McKpiCardComponent {
  label = input.required<string>();
  value = input.required<string | number>();
  hint = input<string>();
}
