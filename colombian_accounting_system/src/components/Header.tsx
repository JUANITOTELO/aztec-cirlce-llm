import React from 'react';
import { Shield, Building2, UserCircle2, Lock, Unlock } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useAccountingStore } from '../store/accountingStore';
import { UserRole } from '../types/auth';

export const Header: React.FC = () => {
  const { currentUser, switchRole } = useAuthStore();
  const { activePeriod, lockedPeriods, togglePeriodLock, setActivePeriod } = useAccountingStore();
  const isCurrentPeriodLocked = lockedPeriods.includes(activePeriod);

  const roles: UserRole[] = ['ADMIN', 'CONTADOR', 'AUXILIAR', 'AUDITOR'];

  return (
    <header className="bg-slate-900/90 backdrop-blur border-b border-slate-800 sticky top-0 z-50 px-6 py-3.5">
      <div className="flex flex-wrap items-center justify-between gap-4 max-w-7xl mx-auto">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold">
            SIF
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-semibold text-slate-100 text-base leading-tight">SIFCO Colombia</h1>
              <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-1.5 py-0.5 rounded font-mono">DIAN v2.1</span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5">
              <Building2 className="w-3 h-3 text-slate-500" />
              {currentUser.companyName} &bull; NIT: {currentUser.companyNit}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Period Selector & Lock Control */}
          <div className="flex items-center bg-slate-800/80 border border-slate-700 rounded-lg p-1 text-xs">
            <select
              value={activePeriod}
              onChange={(e) => setActivePeriod(e.target.value)}
              className="bg-transparent border-none text-slate-200 font-mono focus:ring-0 px-2 cursor-pointer"
            >
              <option value="2025-01" className="bg-slate-900">2025-01 (Enero)</option>
              <option value="2025-02" className="bg-slate-900">2025-02 (Febrero)</option>
              <option value="2025-03" className="bg-slate-900">2025-03 (Marzo)</option>
            </select>
            <button
              onClick={() => togglePeriodLock(activePeriod)}
              disabled={currentUser.role !== 'ADMIN' && currentUser.role !== 'CONTADOR'}
              className={`flex items-center gap-1 px-2.5 py-1 rounded transition-colors ${
                isCurrentPeriodLocked ? 'bg-rose-950/70 text-rose-300 border border-rose-800/60' : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
              }`}
              title={isCurrentPeriodLocked ? 'Periodo Bloqueado' : 'Periodo Abierto'}
            >
              {isCurrentPeriodLocked ? <Lock className="w-3 h-3 text-rose-400" /> : <Unlock className="w-3 h-3 text-emerald-400" />}
              <span className="font-mono text-[11px]">{isCurrentPeriodLocked ? 'CERRADO' : 'ABIERTO'}</span>
            </button>
          </div>

          {/* RBAC Role Switcher */}
          <div className="flex items-center gap-2 bg-slate-800/50 border border-slate-700/70 rounded-lg px-3 py-1.5">
            <UserCircle2 className="w-4 h-4 text-emerald-400" />
            <div className="text-right">
              <div className="text-xs font-medium text-slate-200">{currentUser.name}</div>
              <div className="flex items-center gap-1 justify-end">
                <Shield className="w-3 h-3 text-slate-400" />
                <select
                  value={currentUser.role}
                  onChange={(e) => switchRole(e.target.value as UserRole)}
                  className="text-[11px] bg-transparent text-emerald-400 font-semibold focus:outline-none cursor-pointer"
                >
                  {roles.map((r) => (
                    <option key={r} value={r} className="bg-slate-900 text-slate-200">
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};