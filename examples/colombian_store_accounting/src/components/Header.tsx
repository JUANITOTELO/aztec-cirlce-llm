import React from 'react';
import { UserAccount, AppModule } from '../types/store';
import {
  Store,
  LogOut,
  RotateCcw,
  ShoppingCart,
  Package,
  Boxes,
  BookOpen,
  FileSpreadsheet,
  Layers,
  Users
} from 'lucide-react';
import SyncStatusIndicator from './POS/SyncStatusIndicator';

interface HeaderProps {
  currentUser: UserAccount;
  activeTab: AppModule;
  setActiveTab: (tab: AppModule) => void;
  allowedModules: AppModule[];
  onLogout: () => void;
  onResetData: () => void;
}

const NAV_ITEMS: { id: AppModule; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'pos', label: 'POS Caja', icon: ShoppingCart },
  { id: 'products', label: 'Catálogo', icon: Package },
  { id: 'inventory', label: 'Inventario', icon: Boxes },
  { id: 'ledger', label: 'Libro Diario', icon: BookOpen },
  { id: 'dian', label: 'DIAN Impuestos', icon: FileSpreadsheet },
  { id: 'puc', label: 'Plan PUC', icon: Layers },
  { id: 'users', label: 'Usuarios / Roles', icon: Users },
];

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  activeTab,
  setActiveTab,
  allowedModules,
  onLogout,
  onResetData,
}) => {
  const visibleNav = NAV_ITEMS.filter((item) => allowedModules.includes(item.id));

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white shadow-lg sticky top-0 z-50">
      <div className="px-6 py-3 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/60">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-900/30">
            <Store className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Aztec POS &amp; Contabilidad
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-medium px-2 py-0.5 rounded border border-emerald-500/30">
                Colombia DIAN
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Punto de Venta • PUC • Liquidación Tributaria • Partida Doble</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <SyncStatusIndicator />
          <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
            <button
              onClick={onResetData}
              title="Restablecer datos a valores iniciales"
              className="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-slate-200">{currentUser.name}</p>
              <p className="text-[10px] text-slate-400 capitalize">{currentUser.role || 'Usuario'}</p>
            </div>
            <button
              onClick={onLogout}
              title="Cerrar Sesión"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <nav className="px-6 flex items-center gap-1 overflow-x-auto bg-slate-950/40">
        {visibleNav.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-emerald-500 text-emerald-400 bg-emerald-500/10 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};

export default Header;
