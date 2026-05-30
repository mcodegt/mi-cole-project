import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MessageModule } from 'primeng/message';
import { TagModule } from 'primeng/tag';
import { TextareaModule } from 'primeng/textarea';

import { McPageHeaderComponent } from '../../../shared/mc-page-header.component';
import { environment } from '../../../../environments/environment';

interface AssignmentDetail {
  id: string;
  title: string;
  description: string | null;
  due_at: string | null;
  status: string;
  submission_status: string | null;
  submitted_at: string | null;
  submission_body: string | null;
}

@Component({
  selector: 'app-student-assignment-detail',
  standalone: true,
  imports: [DatePipe, FormsModule, RouterLink, TagModule, TextareaModule, MessageModule, McPageHeaderComponent],
  template: `
    <a routerLink="/student/assignments" class="mb-4 inline-flex min-h-[44px] items-center gap-1 text-sm text-indigo-500">
      <i class="pi pi-arrow-left"></i> Volver a tareas
    </a>

    @if (assignment(); as a) {
      <mc-page-header [title]="a.title" subtitle="Detalle de la tarea" />

      <div class="mc-card mb-4 space-y-3">
        @if (a.description) {
          <p class="mc-text">{{ a.description }}</p>
        }
        <p class="text-sm mc-text-muted">
          Fecha de entrega: {{ a.due_at ? (a.due_at | date: 'mediumDate') : 'Sin fecha' }}
        </p>
        <p-tag
          [value]="a.submission_status ?? 'pendiente'"
          [severity]="a.submission_status === 'submitted' || a.submission_status === 'graded' ? 'success' : 'warn'"
        />
      </div>

      @if (a.submission_status === 'submitted' || a.submission_status === 'graded') {
        <div class="mc-card">
          <h2 class="mb-2 text-base font-semibold mc-text">Tu entrega</h2>
          <p class="whitespace-pre-wrap mc-text">{{ a.submission_body }}</p>
          @if (a.submitted_at) {
            <p class="mt-3 text-xs mc-text-muted">Enviada el {{ a.submitted_at | date: 'medium' }}</p>
          }
        </div>
      } @else {
        <div class="mc-card">
          <h2 class="mb-3 text-base font-semibold mc-text">Enviar entrega</h2>
          @if (error()) {
            <p-message severity="error" [text]="error()!" styleClass="mb-3 w-full" />
          }
          <label class="mb-1 block text-xs font-medium mc-text-muted">Respuesta / comentarios</label>
          <textarea
            pTextarea
            rows="8"
            class="w-full text-base"
            [(ngModel)]="body"
            placeholder="Escribe tu entrega aquí..."
          ></textarea>
          <button
            type="button"
            class="mc-btn-primary mt-4 min-h-[48px] w-full"
            [disabled]="submitting() || !body.trim()"
            (click)="submit()"
          >
            {{ submitting() ? 'Enviando…' : 'Enviar tarea' }}
          </button>
        </div>
      }
    }
  `,
})
export class StudentAssignmentDetailComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);

  readonly assignment = signal<AssignmentDetail | null>(null);
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  body = '';

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      return;
    }
    this.http.get<AssignmentDetail>(`${environment.apiUrl}/student/assignments/${id}`).subscribe({
      next: (res) => {
        this.assignment.set(res);
        if (res.submission_body) {
          this.body = res.submission_body;
        }
      },
    });
  }

  submit(): void {
    const a = this.assignment();
    if (!a || !this.body.trim()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.http
      .post(`${environment.apiUrl}/student/assignments/${a.id}/submissions`, { body: this.body.trim() })
      .subscribe({
        next: () => {
          this.http.get<AssignmentDetail>(`${environment.apiUrl}/student/assignments/${a.id}`).subscribe({
            next: (res) => {
              this.assignment.set(res);
              this.submitting.set(false);
            },
          });
        },
        error: (err) => {
          this.submitting.set(false);
          this.error.set(err.error?.detail ?? 'No se pudo enviar la entrega');
        },
      });
  }
}
