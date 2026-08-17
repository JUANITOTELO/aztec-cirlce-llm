import React, { useState } from 'react';
import { UserAccount, RoleItem, AppModule } from '../../types/store';
import { Shield, UserPlus, Users, KeyRound, PlusCircle, Trash2, CheckSquare, Square, Edit2, XCircle, Check } from 'lucide-react';

const AVAILABLE_MODULES: { id: AppModule; label: string }[] = [
  { id: 'pos', label: 'Punto de Venta (POS)' },
  { id: 'inventory', label: 'Inventario & Alertas' },
  { id: 'ledger', label: 'Libro Mayor & Diario' },
  { id: 'dian', label: 'Liquidación DIAN' },
  { id: 'puc', label: 'Catálogo PUC' },
  { id: 'users', label: 'Usuarios & Roles' },
  { id: 'multimedia', label: 'Subida de Multimedia' },
];

interface UserRoleManagerProps {
  users: UserAccount[];
  roles: RoleItem[];
  onAddUser: (user: UserAccount) => void;
  onDeleteUser: (id: string) => void;
  onAddRole: (role: RoleItem) => void;
  onUpdateRole?: (role: RoleItem) => void;
  onDeleteRole?: (id: string) => void;
}

export const UserRoleManager: React.FC<UserRoleManagerProps> = ({
  users,
  roles,
  onAddUser,
  onDeleteUser,
  onAddRole,
  onUpdateRole,
  onDeleteRole,
}) => {
  const [activeTab, setActiveTab] = useState<'users' | 'roles'>('users');
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userPassword, setUserPassword] = useState('');
  const [userRoleId, setUserRoleId] = useState(roles[0]?.id || 'role-admin');
  const [editingRoleId, setEditingRoleId] = useState<string | null>(null);
  const [roleName, setRoleName] = useState('');
  const [roleDesc, setRoleDesc] = useState('');
  const [selectedModules, setSelectedModules] = useState<AppModule[]>(['pos']);

  const toggleModule = (mod: AppModule) => {
    setSelectedModules((prev) => (prev.includes(mod) ? prev.filter((m) => m !== mod) : [...prev, mod]));
  };

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userName.trim() || !userEmail.trim()) return;
    const assignedRole = roles.find((r) => r.id === userRoleId);
    onAddUser({
      id: `usr-${Date.now()}`,
      name: userName.trim(),
      email: userEmail.trim().toLowerCase(),
      password: userPassword.trim() || '123456',
      roleId: userRoleId,
      role: assignedRole?.name || 'Cajero',
      isActive: true,
    });
    setUserName('');
    setUserEmail('');
    setUserPassword('');
  };

  const handleSaveRole = (e: React.FormEvent) => {
    e.preventDefault();
    if (!roleName.trim() || selectedModules.length === 0) return;

    if (editingRoleId) {
      if (onUpdateRole) {
        const current = roles.find((r) => r.id === editingRoleId);
        onUpdateRole({
          id: editingRoleId,
          name: roleName.trim(),
          description: roleDesc.trim() || 'Rol personalizado con acceso a módulos',
          modules: selectedModules,
          isSystem: current?.isSystem,
        });
      }
      setEditingRoleId(null);
    } else {
      onAddRole({
        id: `role-${Date.now()}`,
        name: roleName.trim(),
        description: roleDesc.trim() || 'Rol personalizado con acceso a módulos',
        modules: selectedModules,
        isSystem: false,
      });
    }

    setRoleName('');
    setRoleDesc('');
    setSelectedModules(['pos']);
  };

  const handleSelectRoleToEdit = (role: RoleItem) => {
    setEditingRoleId(role.id);
    setRoleName(role.name);
    setRoleDesc(role.description || '');
    setSelectedModules(role.modules || []);
  };

  const handleCancelRoleEdit = () => {
    setEditingRoleId(null);
    setRoleName('');
    setRoleDesc('');
    setSelectedModules(['pos']);
  };

  const handleDeleteRole = (e: React.MouseEvent, roleId: string) => {
    e.stopPropagation();
    if (onDeleteRole) {
      if (editingRoleId === roleId) {
        handleCancelRoleEdit();
      }
      onDeleteRole(roleId);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" /> Matriz de Accesos &amp; Permisos
          </h2>
          <p className="text-xs text-slate-400">Control RBAC de usuarios, roles y módulos del sistema</p>
        </div>
        <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
          <button onClick={() => setActiveTab('users')} className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition ${activeTab === 'users' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`}>
            <Users className="w-3.5 h-3.5" /> Usuarios ({users?.length ?? 0})
          </button>
          <button onClick={() => setActiveTab('roles')} className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition ${activeTab === 'roles' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`}>
            <KeyRound className="w-3.5 h-3.5" /> Roles ({roles?.length ?? 0})
          </button>
        </div>
      </div>

      {activeTab === 'users' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <form onSubmit={handleCreateUser} className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2"><UserPlus className="w-4 h-4" /> Registrar Usuario</h3>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre Completo</label>
              <input required value={userName} onChange={(e) => setUserName(e.target.value)} placeholder="ej. Carlos Ramírez" className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Usuario / Correo</label>
              <input required value={userEmail} onChange={(e) => setUserEmail(e.target.value)} placeholder="ej. carlos / carlos@aztec.co" className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Contraseña</label>
              <input required type="password" value={userPassword} onChange={(e) => setUserPassword(e.target.value)} placeholder="••••••" className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Rol Asignado</label>
              <select value={userRoleId} onChange={(e) => setUserRoleId(e.target.value)} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white">
                {roles.map((r) => (<option key={r.id} value={r.id}>{r.name} ({(r.modules?.length ?? 0)} módulos)</option>))}
              </select>
            </div>
            <button type="submit" className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5"><PlusCircle className="w-4 h-4" /> Guardar Usuario</button>
          </form>
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 font-bold text-xs text-slate-300">Usuarios Registrados</div>
            <div className="divide-y divide-slate-800 max-h-[420px] overflow-y-auto">
              {users.map((u) => {
                const userRole = roles.find((r) => r.id === u.roleId) || { name: u.role || 'Cajero', modules: [] };
                return (
                  <div key={u.id} className="p-3.5 flex items-center justify-between hover:bg-slate-800/40">
                    <div>
                      <p className="text-xs font-bold text-white">{u.name}</p>
                      <p className="text-[11px] text-slate-400">{u.email}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/50">{userRole.name}</span>
                      {u.email !== 'admin' && (
                        <button onClick={() => onDeleteUser(u.id)} className="text-slate-500 hover:text-rose-400 p-1"><Trash2 className="w-3.5 h-3.5" /></button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <form onSubmit={handleSaveRole} className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                {editingRoleId ? <Edit2 className="w-4 h-4" /> : <PlusCircle className="w-4 h-4" />}
                {editingRoleId ? 'Editar Rol Seleccionado' : 'Configurar Rol & Módulos'}
              </h3>
              {editingRoleId && (
                <button
                  type="button"
                  onClick={handleCancelRoleEdit}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
                >
                  <XCircle className="w-3.5 h-3.5" /> Cancelar
                </button>
              )}
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Nombre del Rol</label>
              <input required value={roleName} onChange={(e) => setRoleName(e.target.value)} placeholder="ej. Supervisor, Auditor" className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Descripción</label>
              <input value={roleDesc} onChange={(e) => setRoleDesc(e.target.value)} placeholder="Propósito del perfil..." className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-2">Módulos Autorizados</label>
              <div className="space-y-1.5 bg-slate-800/60 p-3 rounded-lg border border-slate-700">
                {AVAILABLE_MODULES.map((mod) => {
                  const isChecked = selectedModules.includes(mod.id);
                  return (
                    <button type="button" key={mod.id} onClick={() => toggleModule(mod.id)} className="w-full flex items-center gap-2 text-left text-xs text-slate-200 py-1 hover:text-white">
                      {isChecked ? <CheckSquare className="w-3.5 h-3.5 text-emerald-400" /> : <Square className="w-3.5 h-3.5 text-slate-500" />}
                      <span>{mod.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            <button
              type="submit"
              disabled={selectedModules.length === 0}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
            >
              {editingRoleId ? <Check className="w-4 h-4" /> : <PlusCircle className="w-4 h-4" />}
              {editingRoleId ? 'Guardar Cambios de Rol' : 'Guardar Rol'}
            </button>
          </form>
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-800 font-bold text-xs text-slate-300 flex items-center justify-between">
              <span>Roles y Módulos Autorizados</span>
              <span className="text-[10px] text-slate-500 font-normal">Haz clic en un rol para editarlo</span>
            </div>
            <div className="divide-y divide-slate-800 max-h-[420px] overflow-y-auto">
              {roles.map((r) => {
                const isEditing = editingRoleId === r.id;
                const isDeletable = r.id !== 'role-admin' && !r.isSystem && onDeleteRole;
                return (
                  <div
                    key={r.id}
                    onClick={() => handleSelectRoleToEdit(r)}
                    className={`p-4 space-y-2 cursor-pointer transition border-l-2 ${
                      isEditing
                        ? 'bg-emerald-950/25 border-emerald-400'
                        : 'border-transparent hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-bold text-white">{r.name}</p>
                        {isEditing && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-900/60 text-emerald-300 border border-emerald-700/50 uppercase font-semibold">
                            Editando
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-400 font-mono">{(r.modules?.length ?? 0)} módulos</span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectRoleToEdit(r);
                          }}
                          className="p-1 text-slate-400 hover:text-emerald-400 rounded transition"
                          title="Editar rol"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        {isDeletable && (
                          <button
                            type="button"
                            onClick={(e) => handleDeleteRole(e, r.id)}
                            className="p-1 text-slate-500 hover:text-rose-400 rounded transition"
                            title="Eliminar rol"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-400">{r.description}</p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {(r.modules || []).map((m) => (
                        <span key={m} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 uppercase font-medium">{m}</span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
