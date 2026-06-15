const HEX_COLOR = /^#[0-9A-Fa-f]{6}$/;

export function parseHexColor(value: string): { r: number; g: number; b: number } | null {
  const match = HEX_COLOR.exec(value.trim());
  if (!match) {
    return null;
  }
  const raw = value.trim().slice(1);
  return {
    r: parseInt(raw.slice(0, 2), 16),
    g: parseInt(raw.slice(2, 4), 16),
    b: parseInt(raw.slice(4, 6), 16),
  };
}

export function relativeLuminance(hex: string): number | null {
  const rgb = parseHexColor(hex);
  if (!rgb) {
    return null;
  }
  const channel = (value: number): number => {
    const s = value / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  const r = channel(rgb.r);
  const g = channel(rgb.g);
  const b = channel(rgb.b);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function suggestTextColorForBackground(hex: string): string {
  const lum = relativeLuminance(hex);
  if (lum === null) {
    return '#f8fafc';
  }
  return lum > 0.179 ? '#0f172a' : '#f8fafc';
}

export function mixHex(fg: string, bg: string, ratio: number): string {
  const a = parseHexColor(fg);
  const b = parseHexColor(bg);
  if (!a || !b) {
    return fg;
  }
  const mix = (x: number, y: number) => Math.round(x * ratio + y * (1 - ratio));
  const r = mix(a.r, b.r);
  const g = mix(a.g, b.g);
  const bl = mix(a.b, b.b);
  return `#${[r, g, bl].map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

export function sidebarActiveColors(surface: string, text: string): { bg: string; fg: string } {
  const surfaceLum = relativeLuminance(surface) ?? 0.5;
  if (surfaceLum <= 0.179) {
    const bg = mixHex('#ffffff', surface, 0.2);
    return { bg, fg: text };
  }
  const bg = mixHex('#0f172a', surface, 0.84);
  return { bg, fg: '#ffffff' };
}

export function applySidebarTheme(surface: string, text: string): void {
  const root = document.documentElement;
  const active = sidebarActiveColors(surface, text);
  const tokens: Record<string, string> = {
    '--mc-sidebar-surface': surface,
    '--mc-sidebar-border': mixHex(text, surface, 0.18),
    '--mc-sidebar-link': mixHex(text, surface, 0.72),
    '--mc-sidebar-link-hover': text,
    '--mc-sidebar-link-hover-bg': mixHex(text, surface, 0.1),
    '--mc-sidebar-icon': mixHex(text, surface, 0.62),
    '--mc-sidebar-active-bg': active.bg,
    '--mc-sidebar-active-text': active.fg,
    '--mc-sidebar-search-bg': mixHex(text, surface, 0.08),
    '--mc-sidebar-search-text': text,
    '--mc-sidebar-search-placeholder': mixHex(text, surface, 0.45),
    '--mc-sidebar-badge-bg': mixHex(text, surface, 0.14),
    '--mc-sidebar-badge-text': text,
    '--mc-sidebar-footer-border': mixHex(text, surface, 0.16),
    '--mc-sidebar-muted': mixHex(text, surface, 0.68),
    '--mc-sidebar-toggle-bg': mixHex(text, surface, 0.1),
    '--mc-sidebar-toggle-border': mixHex(text, surface, 0.22),
    '--mc-sidebar-toggle-text': text,
    '--mc-sidebar-toggle-hover-bg': mixHex(text, surface, 0.16),
    '--mc-sidebar-action-text': mixHex(text, surface, 0.62),
    '--mc-sidebar-action-hover-bg': mixHex(text, surface, 0.12),
    '--mc-sidebar-action-active-bg': active.bg,
    '--mc-sidebar-action-active-text': active.fg,
    '--mc-sidebar-logout-hover-bg':
      relativeLuminance(surface) !== null && relativeLuminance(surface)! <= 0.179
        ? 'rgb(239 68 68 / 0.15)'
        : '#fef2f2',
  };

  for (const [key, value] of Object.entries(tokens)) {
    root.style.setProperty(key, value);
  }
}

export async function suggestBackgroundFromImage(url: string): Promise<string | null> {
  try {
    const img = await loadImage(url);
    const canvas = document.createElement('canvas');
    const size = 32;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return null;
    }
    ctx.drawImage(img, 0, 0, size, size);
    const { data } = ctx.getImageData(0, 0, size, size);
    let r = 0;
    let g = 0;
    let b = 0;
    let count = 0;
    for (let i = 0; i < data.length; i += 4) {
      const alpha = data[i + 3];
      if (alpha < 40) {
        continue;
      }
      r += data[i];
      g += data[i + 1];
      b += data[i + 2];
      count += 1;
    }
    if (!count) {
      return null;
    }
    const toHex = (v: number) =>
      Math.round(v / count)
        .toString(16)
        .padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  } catch {
    return null;
  }
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('No se pudo cargar la imagen'));
    img.src = url;
  });
}

export function ensureButtonAccent(hex: string | null | undefined, fallback = '#2563eb'): string {
  if (!hex || !hex.startsWith('#')) {
    return fallback;
  }
  const lum = relativeLuminance(hex);
  if (lum === null || lum > 0.55) {
    return fallback;
  }
  return hex;
}

export const DEFAULT_SIDEBAR_COLOR = '#ffffff';
export const DEFAULT_SIDEBAR_TEXT_COLOR = '#0f172a';
