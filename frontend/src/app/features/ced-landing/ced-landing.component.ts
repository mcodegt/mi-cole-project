import { Component, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { CED_AUTH_ROUTES, CED_BRAND } from '../../core/brand/ced-brand';

interface NavLink {
  label: string;
  fragment: string;
}

interface StatItem {
  value: string;
  label: string;
  icon: string;
}

interface RoleSection {
  id: string;
  title: string;
  description: string;
  bullets: string[];
  portal: 'staff' | 'parent' | 'student';
  cta: string;
  icon: string;
  reversed: boolean;
}

@Component({
  selector: 'app-ced-landing',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './ced-landing.component.html',
  styleUrl: './ced-landing.component.css',
})
export class CedLandingComponent {
  readonly brand = CED_BRAND;
  readonly auth = CED_AUTH_ROUTES;
  readonly navOpen = signal(false);
  readonly year = new Date().getFullYear();
  readonly demoEmail = 'info@mcodegt.com';
  readonly whatsappUrl =
    'https://wa.me/50255564990?text=' +
    encodeURIComponent('Hola, me interesa conocer CED — Centro Educativo Digital.');

  readonly navLinks: NavLink[] = [
    { label: 'Inicio', fragment: 'inicio' },
    { label: 'Administradores', fragment: 'administradores' },
    { label: 'Maestros', fragment: 'maestros' },
    { label: 'Padres de familia', fragment: 'padres' },
    { label: 'Estudiantes', fragment: 'estudiantes' },
    { label: 'Contacto', fragment: 'contacto' },
  ];

  readonly stats: StatItem[] = [
    { value: '3', label: 'Portales de acceso', icon: 'pi pi-th-large' },
    { value: 'Multi', label: 'Sede por colegio', icon: 'pi pi-building' },
    { value: 'GT', label: 'Hecho para Guatemala', icon: 'pi pi-map-marker' },
  ];

  readonly roles: RoleSection[] = [
    {
      id: 'administradores',
      title: 'Administradores',
      description:
        'Organiza y centraliza sedes, estudiantes, padres de familia, equipo y suscripción desde un solo panel.',
      bullets: ['Gestión de sedes y campus', 'Estudiantes y padres de familia', 'Equipo e identidad del colegio'],
      portal: 'staff',
      cta: 'Ingresar como administrador',
      icon: 'pi pi-building',
      reversed: false,
    },
    {
      id: 'maestros',
      title: 'Maestros',
      description:
        'Opera el día a día de tu sede con acceso al panel staff: estudiantes, tareas y la información que necesitas en clase.',
      bullets: ['Acceso por colegio y sede', 'Vista operativa del centro', 'Mismo portal que administración'],
      portal: 'staff',
      cta: 'Ingresar como maestro',
      icon: 'pi pi-users',
      reversed: true,
    },
    {
      id: 'padres',
      title: 'Padres de familia',
      description:
        'Consulta tareas e información académica de tus hijos con un acceso claro, por colegio y sede.',
      bullets: ['Portal dedicado para encargados', 'Tareas e información de hijos', 'Login con marca del colegio'],
      portal: 'parent',
      cta: 'Ingresar como padre de familia',
      icon: 'pi pi-heart',
      reversed: false,
    },
    {
      id: 'estudiantes',
      title: 'Estudiantes',
      description:
        'Revisa tareas, entregas y avisos académicos con un acceso ordenado desde tu sede.',
      bullets: ['Tareas y entregas', 'Detalle por actividad', 'Acceso estudiantil por sede'],
      portal: 'student',
      cta: 'Ingresar como estudiante',
      icon: 'pi pi-book',
      reversed: true,
    },
  ];

  toggleNav(): void {
    this.navOpen.update((v) => !v);
  }

  closeNav(): void {
    this.navOpen.set(false);
  }
}
