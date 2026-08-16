export type UserRole = 'ADMIN' | 'CONTADOR' | 'AUXILIAR' | 'AUDITOR';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  companyId: string;
  companyNit: string;
  companyName: string;
}