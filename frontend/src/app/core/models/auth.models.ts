export type Portal = 'platform' | 'staff' | 'parent' | 'student';

export interface UserInfo {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface PlatformContext {
  is_superadmin: boolean;
  permissions: string[];
}

export interface StaffMeContext {
  school_id: string;
  school_slug: string;
  school_name: string;
  billing_access_mode: 'full' | 'payment_evidence_only';
  permissions: string[];
  all_campuses: boolean;
}

export interface ParentMeContext {
  parent_id: string;
  school_id: string;
  school_slug: string;
  school_name: string;
  campus_name?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
  portal: Portal;
  platform?: PlatformContext;
  sid?: string;
  mid?: string;
  pid?: string;
  campus_id?: string;
}

export interface MeResponse {
  user: UserInfo;
  portal: Portal;
  platform?: PlatformContext;
  staff?: StaffMeContext;
  parent?: ParentMeContext;
  sid?: string;
  mid?: string;
  pid?: string;
  campus_id?: string;
}

export interface MembershipSummary {
  membership_id: string;
  school_id: string;
  school_slug: string;
  school_name: string;
  role_code: string;
  all_campuses: boolean;
}

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  portal: Portal;
  user: UserInfo;
  schoolId?: string;
  membershipId?: string;
  parentId?: string;
  campusId?: string;
  staff?: StaffMeContext;
  parent?: ParentMeContext;
  platform?: PlatformContext;
}

export interface LoginContextResponse {
  school: { id: string; slug: string; name: string };
  campus: { id: string; slug: string; name: string };
  portal: Portal;
  login_enabled: boolean;
  branding: {
    login_title?: string;
    login_subtitle?: string;
    primary_color_hex?: string;
    logo_url?: string;
  };
  login_path: string;
}
