import { create } from 'zustand';
import { UserProfile, UserRole } from '../types/auth';

interface AuthState {
  currentUser: UserProfile;
  switchRole: (role: UserRole) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  currentUser: {
    id: 'USR-001',
    name: 'Dra. Claudia Morales',
    email: 'c.morales@colombiacontable.com',
    role: 'CONTADOR',
    companyId: 'COMP-901',
    companyNit: '901.458.922-1',
    companyName: 'INVERSIONES ANDINAS S.A.S.',
  },
  switchRole: (role: UserRole) =>
    set((state) => ({
      currentUser: { ...state.currentUser, role },
    })),
}));