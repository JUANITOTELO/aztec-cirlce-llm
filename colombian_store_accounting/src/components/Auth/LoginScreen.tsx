import React, { useState } from 'react';
import { UserAccount } from '../../types/store';
import { Store, ShieldCheck, ArrowRight, Lock, User as UserIcon, AlertCircle } from 'lucide-react';

interface LoginScreenProps {
  users: UserAccount[];
  onLogin: (user: UserAccount) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ users, onLogin }) => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleDirectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const idClean = identifier.trim().toLowerCase();
    const passClean = password.trim();

    const matched = users.find(
      (u) =>
        (u.email.toLowerCase() === idClean || u.name.toLowerCase() === idClean) &&
        (u.password ? u.password === passClean : passClean === 'admin')
    );

    if (matched) {
      onLogin(matched);
    } else {
      setError('Credenciales inválidas. Verifique usuario y contraseña.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 text-slate-100">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 bg-emerald-600 rounded-xl mx-auto flex items-center justify-center shadow-lg shadow-emerald-900/40">
            <Store className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Aztec POS &amp; Contabilidad</h1>
          <p className="text-xs text-slate-400">Acceso restringido &bull; Sistema Tributario DIAN Colombia</p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleDirectSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Usuario o Correo</label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                required
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="ej. admin"
                className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Contraseña</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
          <button
            type="submit"
            className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition-all cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4" /> Iniciar Sesión <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800 text-[11px] text-slate-400 text-center">
          Credenciales iniciales de administrador: <span className="text-emerald-400 font-mono font-semibold">admin / admin</span>
        </div>
      </div>
    </div>
  );
};
