/** Marca comercial CED — Centro Educativo Digital (by MCodeGT). */
export const CED_BRAND = {
  shortName: 'CED',
  fullName: 'Centro Educativo Digital',
  tagline: 'Todo tu centro educativo conectado en una sola plataforma.',
  assets: {
    icon: 'assets/ced/ced-icon.png',
    logo: 'assets/ced/ced-logo.png',
    header: 'assets/ced/ced-header.png',
  },
};

/** Rutas de acceso públicas (sin colegio hardcodeado). */
export const CED_AUTH_ROUTES = {
  /** Dueño / administración de plataforma MCodeGT. */
  platform: '/login/platform',
  /** Formulario genérico: código de colegio + sede → login del portal. */
  entry: '/login/ingresar',
  entryForPortal: (portal: 'staff' | 'parent' | 'student') =>
    `/login/ingresar?portal=${portal}`,
};
