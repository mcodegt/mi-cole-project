import { Component, input } from '@angular/core';

@Component({
  selector: 'mc-form-field',
  standalone: true,
  template: `
    <div class="mc-form-field" [class.mc-form-field--compact]="compact()">
      @if (label()) {
        <label class="mc-form-field__label" [attr.for]="forId()">
          @if (icon()) {
            <span class="mc-form-field__icon-wrap" aria-hidden="true">
              <i [class]="icon()"></i>
            </span>
          }
          <span>{{ label() }}</span>
        </label>
      }
      <div class="mc-form-field__control">
        <ng-content />
      </div>
      @if (hint()) {
        <p class="mc-form-field__hint">{{ hint() }}</p>
      }
      @if (error()) {
        <p class="mc-form-field__error">{{ error() }}</p>
      }
    </div>
  `,
})
export class McFormFieldComponent {
  label = input<string>();
  hint = input<string>();
  error = input<string | null>();
  icon = input<string>();
  forId = input<string>();
  compact = input(false);
}
