import { inject, Injectable } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';

const APP_NAME = 'Mi Cole';

const PORTAL_LABELS: Record<string, string> = {
  platform: 'Platform',
  staff: 'Staff',
  parent: 'Padres',
  student: 'Estudiantes',
};

@Injectable({ providedIn: 'root' })
export class McTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);

  override updateTitle(snapshot: RouterStateSnapshot): void {
    this.title.setTitle(this.buildDocumentTitle(snapshot));
  }

  private buildDocumentTitle(snapshot: RouterStateSnapshot): string {
    let route = snapshot.root;
    let portalTitle: string | undefined;
    let pageTitle: string | undefined;

    while (route.firstChild) {
      route = route.firstChild;
      const dataPortal = route.data['portalTitle'] as string | undefined;
      if (dataPortal) {
        portalTitle = dataPortal;
      }
      const portalParam = route.paramMap.get('portal');
      if (portalParam && PORTAL_LABELS[portalParam]) {
        portalTitle = PORTAL_LABELS[portalParam];
      }
      const dataTitle = route.data['title'] as string | undefined;
      if (dataTitle) {
        pageTitle = dataTitle;
      }
    }

    const parts = [APP_NAME];
    if (portalTitle) {
      parts.push(portalTitle);
    }
    if (pageTitle && pageTitle !== portalTitle) {
      parts.push(pageTitle);
    }
    return parts.join(' - ');
  }
}
