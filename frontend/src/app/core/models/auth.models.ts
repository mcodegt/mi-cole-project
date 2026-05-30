export type Portal = 'platform' | 'staff' | 'parent' | 'student';

export interface UserInfo {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  must_change_password?: boolean;
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

export interface StudentMeContext {
  student_id: string;
  school_id: string;
  school_slug: string;
  school_name: string;
  campus_name?: string;
  student_code?: string;
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
  stid?: string;
  campus_id?: string;
  portals?: string[];
}

export interface MeResponse {
  user: UserInfo;
  portal: Portal;
  platform?: PlatformContext;
  staff?: StaffMeContext;
  parent?: ParentMeContext;
  student?: StudentMeContext;
  sid?: string;
  mid?: string;
  pid?: string;
  stid?: string;
  campus_id?: string;
  portals?: string[];
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
  studentId?: string;
  campusId?: string;
  staff?: StaffMeContext;
  parent?: ParentMeContext;
  student?: StudentMeContext;
  platform?: PlatformContext;
  mustChangePassword?: boolean;
  portals?: string[];
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
