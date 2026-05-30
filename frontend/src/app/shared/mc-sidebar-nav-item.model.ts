export interface McSidebarNavItem {
  label: string;
  icon: string;
  route: string | string[];
  exact?: boolean;
  badge?: number | string;
}
