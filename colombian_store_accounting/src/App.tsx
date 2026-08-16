import React, { useEffect } from 'react';
import { Product, LedgerEntry, UserAccount, RoleItem, AppModule, SaleInvoice } from './types/store';
import { Category } from './types/category';
import { INITIAL_PRODUCTS, INITIAL_LEDGER_ENTRIES, MOCK_USERS, INITIAL_ROLES } from './constants/mockData';
import { INITIAL_CATEGORIES } from './constants/mockCategories';
import { usePersistentState } from './hooks/usePersistentState';
import { useCategoryList } from './hooks/useCategoryList';
import { reassignProductsToCategory } from './engine/categoryConstraints';
import { ProductLedgerOrchestrator } from './engine/productLedgerOrchestrator';
import { Header } from './components/Header';
import { LoginScreen } from './components/Auth/LoginScreen';
import { PosTerminal } from './components/POS/PosTerminal';
import { ProductManagementView } from './components/Products/ProductManagementView';
import { InventoryManager } from './components/Inventory/InventoryManager';
import { LedgerJournal } from './components/Accounting/LedgerJournal';
import { DianTaxSettlement } from './components/Accounting/DianTaxSettlement';
import { PucExplorer } from './components/Accounting/PucExplorer';
import { UserRoleManager } from './components/Admin/UserRoleManager';

export function App() {
  const [currentUser, setCurrentUser] = usePersistentState<UserAccount | null>('aztec_current_user', MOCK_USERS[0]);
  const [users, setUsers] = usePersistentState<UserAccount[]>('aztec_users', MOCK_USERS);
  const [roles, setRoles] = usePersistentState<RoleItem[]>('aztec_roles', INITIAL_ROLES);
  const [activeTab, setActiveTab] = usePersistentState<AppModule>('aztec_active_tab', 'pos');
  const [products, setProducts] = usePersistentState<Product[]>('aztec_products', INITIAL_PRODUCTS);
  const [persistedCategories, setPersistedCategories] = usePersistentState<Category[]>('aztec_categories', INITIAL_CATEGORIES);
  const [ledgerEntries, setLedgerEntries] = usePersistentState<LedgerEntry[]>('aztec_ledger_entries', INITIAL_LEDGER_ENTRIES);

  const { categories, setCategories, addCategory, updateCategory, deleteCategory } = useCategoryList(persistedCategories);

  useEffect(() => {
    setPersistedCategories(categories);
  }, [categories, setPersistedCategories]);

  if (!currentUser) {
    return <LoginScreen users={users} onLogin={(user) => setCurrentUser(user)} />;
  }

  const currentRole = roles.find((r) => r.id === currentUser.roleId) || roles.find((r) => r.name?.toLowerCase() === (currentUser.role || '').toLowerCase()) || INITIAL_ROLES[0];
  const isAdmin = currentUser.role?.toLowerCase() === 'admin' || currentUser.roleId === 'role-admin' || currentRole?.name?.toLowerCase() === 'admin';
  const allowedModules: AppModule[] = isAdmin
    ? ['pos', 'products', 'inventory', 'ledger', 'dian', 'puc', 'users']
    : (currentRole?.modules || ['pos', 'products']);

  const handleLogout = () => setCurrentUser(null);
  const handleResetData = () => {
    if (window.confirm('¿Restablecer datos a los valores iniciales del sistema?')) {
      setProducts(INITIAL_PRODUCTS);
      setCategories(INITIAL_CATEGORIES);
      setLedgerEntries(INITIAL_LEDGER_ENTRIES);
      setUsers(MOCK_USERS);
      setRoles(INITIAL_ROLES);
    }
  };

  const handleReassignCategory = (sourceName: string, targetName: string) => {
    setProducts((prev) => reassignProductsToCategory(prev, sourceName, targetName));
  };

  const handleCompleteSale = (invoice: SaleInvoice) => {
    const saleEntries = ProductLedgerOrchestrator.generateSaleEntries(invoice, categories);
    setLedgerEntries((prev) => [...prev, ...saleEntries]);
    setProducts((prev) =>
      prev.map((p) => {
        const item = invoice.items?.find((it) => it.product.id === p.id);
        if (item) {
          return { ...p, stock: Math.max(0, p.stock - item.quantity) };
        }
        return p;
      })
    );
  };

  const handleUpdateStock = (id: string, newStock: number) => {
    setProducts((prev) => prev.map((p) => (p.id === id ? { ...p, stock: newStock } : p)));
  };

  const handleAddUser = (user: UserAccount) => setUsers((prev) => [...prev, user]);
  const handleDeleteUser = (id: string) => setUsers((prev) => prev.filter((u) => u.id !== id));
  const handleAddRole = (role: RoleItem) => setRoles((prev) => [...prev, role]);
  const handleUpdateRole = (role: RoleItem) => setRoles((prev) => prev.map((r) => (r.id === role.id ? role : r)));
  const handleDeleteRole = (id: string) => setRoles((prev) => prev.filter((r) => r.id !== id));

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      <Header
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        allowedModules={allowedModules}
        onLogout={handleLogout}
        onResetData={handleResetData}
      />
      <main className="flex-1 p-4 md:p-6 overflow-auto">
        {activeTab === 'pos' && (
          <PosTerminal
            products={products}
            onCompleteSale={handleCompleteSale}
          />
        )}
        {activeTab === 'products' && (
          <ProductManagementView
            products={products}
            setProducts={setProducts}
            categories={categories}
            onAddCategory={addCategory}
            onUpdateCategory={updateCategory}
            onDeleteCategory={deleteCategory}
            onReassignCategory={handleReassignCategory}
            currentUser={currentUser}
            roles={roles}
          />
        )}
        {activeTab === 'inventory' && (
          <InventoryManager
            products={products}
            onUpdateStock={handleUpdateStock}
          />
        )}
        {activeTab === 'ledger' && (
          <LedgerJournal
            ledgerEntries={ledgerEntries}
            setLedgerEntries={setLedgerEntries}
          />
        )}
        {activeTab === 'dian' && (
          <DianTaxSettlement />
        )}
        {activeTab === 'puc' && <PucExplorer />}
        {activeTab === 'users' && (
          <UserRoleManager
            users={users}
            roles={roles}
            onAddUser={handleAddUser}
            onDeleteUser={handleDeleteUser}
            onAddRole={handleAddRole}
            onUpdateRole={handleUpdateRole}
            onDeleteRole={handleDeleteRole}
          />
        )}
      </main>
    </div>
  );
}

export default App;
