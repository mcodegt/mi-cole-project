import { Component, input } from '@angular/core';

@Component({
  selector: 'mc-form-panel',
  standalone: true,
  template: `
    <section class="mc-form-panel">
      <header class="mc-form-panel__header">
        <div class="mc-form-panel__icon" aria-hidden="true">
          <i [class]="icon()"></i>
        </div>
        <div class="mc-form-panel__titles">
          <h2 class="mc-form-panel__title">{{ title() }}</h2>
          @if (description()) {
            <p class="mc-form-panel__desc">{{ description() }}</p>
          }
        </div>
      </header>
      <div class="mc-form-panel__body">
        <ng-content />
      </div>
      @if (showFooter()) {
        <footer class="mc-form-panel__footer">
          <ng-content select="[mcFormPanelFooter]" />
        </footer>
      }
    </section>
  `,
})
export class McFormPanelComponent {
  title = input.required<string>();
  description = input<string>();
  icon = input('pi pi-file-edit');
  showFooter = input(false);
}
