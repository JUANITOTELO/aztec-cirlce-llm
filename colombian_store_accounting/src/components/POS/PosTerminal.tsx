import React, { useState } from 'react';
import { Product, CartItem, SaleInvoice } from '../../types/store';
import { formatCOP, calculateCartTotals } from '../../utils/formatters';
import { ShoppingCart, Plus, Minus, Trash2, CheckCircle2, Search, CreditCard, DollarSign, Smartphone } from 'lucide-react';

interface PosTerminalProps {
  products: Product[];
  onCompleteSale: (invoice: SaleInvoice) => void;
}

export const PosTerminal: React.FC<PosTerminalProps> = ({ products, onCompleteSale }) => {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Todos');
  const [paymentMethod, setPaymentMethod] = useState<'Efectivo' | 'Tarjeta' | 'Nequi / Daviplata'>('Efectivo');
  const [customerDoc, setCustomerDoc] = useState('222222222222'); // Consumidor Final DIAN
  const [customerName, setCustomerName] = useState('Consumidor Final');
  const [lastInvoice, setLastInvoice] = useState<SaleInvoice | null>(null);

  const categories = ['Todos', 'Abarrotes', 'Bebidas', 'Lácteos', 'Aseo', 'Snacks'];

  const filteredProducts = products.filter((p) => {
    const matchesCat = selectedCategory === 'Todos' || p.category === selectedCategory;
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.barcode.includes(search) || p.sku.toLowerCase().includes(search.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  };

  const updateQuantity = (productId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((item) => {
          if (item.product.id === productId) {
            const newQty = item.quantity + delta;
            return newQty > 0 ? { ...item, quantity: newQty } : null;
          }
          return item;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const removeFromCart = (productId: string) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const { subtotal, iva, total } = calculateCartTotals(cart);

  const handleCheckout = () => {
    if (cart.length === 0) return;
    const invoice: SaleInvoice = {
      id: `inv-${Date.now()}`,
      consecutive: `POS-${Math.floor(1000 + Math.random() * 9000)}`,
      date: new Date().toLocaleString('es-CO'),
      customerName,
      customerDoc,
      paymentMethod,
      subtotal,
      iva,
      total,
      items: [...cart],
    };

    onCompleteSale(invoice);
    setLastInvoice(invoice);
    setCart([]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)]">
      {/* Product Catalog Column */}
      <div className="lg:col-span-7 flex flex-col space-y-4 min-h-0">
        <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700 space-y-3">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar producto por nombre, SKU o código de barras..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                  selectedCategory === cat
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Products Grid */}
        <div className="flex-1 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 gap-3 pr-1 content-start auto-rows-max">
          {filteredProducts.map((product) => (
            <div
              key={product.id}
              onClick={() => addToCart(product)}
              className="bg-slate-800/90 border border-slate-700 hover:border-emerald-500/60 p-3 rounded-xl cursor-pointer transition flex flex-col justify-between group hover:shadow-lg hover:shadow-emerald-950/20"
            >
              <div>
                <div className="flex justify-between items-start">
                  <span className="text-[10px] bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded font-mono">
                    {product.sku}
                  </span>
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${product.stock <= product.minStock ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'text-slate-400'}`}>
                    Stock: {product.stock}
                  </span>
                </div>
                <h3 className="font-semibold text-white text-sm mt-2 line-clamp-2 leading-snug group-hover:text-emerald-400 transition">
                  {product.name}
                </h3>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-700/60 flex items-center justify-between">
                <div>
                  <div className="text-xs text-slate-400">IVA: {product.ivaRate > 0 ? '19%' : 'Exento'}</div>
                  <div className="text-emerald-400 font-bold text-base">{formatCOP(product.price)}</div>
                </div>
                <div className="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition">
                  <Plus className="w-4 h-4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cart & Checkout Panel */}
      <div className="lg:col-span-5 bg-slate-800/90 border border-slate-700 rounded-xl p-5 flex flex-col justify-between shadow-xl min-h-0">
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between pb-3 border-b border-slate-700">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-emerald-400" />
              Ticket de Venta POS
            </h2>
            <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full font-medium">
              {cart.reduce((s, i) => s + i.quantity, 0)} items
            </span>
          </div>

          {/* Customer info */}
          <div className="grid grid-cols-2 gap-2 my-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Cédula / NIT (DIAN)</label>
              <input
                type="text"
                value={customerDoc}
                onChange={(e) => setCustomerDoc(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Nombre Cliente</label>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white"
              />
            </div>
          </div>

          {/* Cart Items List */}
          {/* Cart Items List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 my-2">
            {cart.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 py-8">
                <ShoppingCart className="w-10 h-10 mx-auto text-slate-600 mb-2 stroke-[1.5]" />
                <p className="text-sm font-medium">El carrito está vacío</p>
                <p className="text-xs text-slate-500">Selecciona productos del catálogo para comenzar</p>
              </div>
            ) : (
              cart.map((item) => (
                <div key={item.product.id} className="flex items-center justify-between bg-slate-900/80 p-2.5 rounded-lg border border-slate-700/60">
                  <div className="flex-1 pr-2">
                    <div className="font-medium text-white text-xs line-clamp-1">{item.product.name}</div>
                    <div className="text-[11px] text-slate-400">{formatCOP(item.product.price)} c/u</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => updateQuantity(item.product.id, -1)}
                      className="w-6 h-6 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center justify-center text-xs"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="text-xs font-bold text-white w-4 text-center">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.product.id, 1)}
                      className="w-6 h-6 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center justify-center text-xs"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => removeFromCart(item.product.id)}
                      className="w-6 h-6 rounded text-red-400 hover:bg-red-950/40 flex items-center justify-center text-xs ml-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        {/* Totals & Checkout Button */}
        <div className="pt-3 border-t border-slate-700 space-y-3">
          {/* Payment Method Selector */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'Efectivo', icon: DollarSign, label: 'Efectivo' },
              { id: 'Tarjeta', icon: CreditCard, label: 'Tarjeta' },
              { id: 'Nequi / Daviplata', icon: Smartphone, label: 'Transferencia' },
            ].map((pm) => (
              <button
                key={pm.id}
                type="button"
                onClick={() => setPaymentMethod(pm.id as any)}
                className={`flex flex-col items-center py-2 px-1 rounded-lg border text-xs font-medium transition ${
                  paymentMethod === pm.id
                    ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
                }`}
              >
                <pm.icon className="w-4 h-4 mb-1" />
                {pm.label}
              </button>
            ))}
          </div>

          <div className="space-y-1.5 text-xs bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
            <div className="flex justify-between text-slate-400">
              <span>Subtotal Base:</span>
              <span className="font-mono text-slate-200">{formatCOP(subtotal)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>IVA Discriminado (DIAN):</span>
              <span className="font-mono text-emerald-400">{formatCOP(iva)}</span>
            </div>
            <div className="flex justify-between text-base font-bold text-white pt-1.5 border-t border-slate-700">
              <span>Total a Pagar:</span>
              <span className="font-mono text-emerald-400">{formatCOP(total)}</span>
            </div>
          </div>

          <button
            onClick={handleCheckout}
            disabled={cart.length === 0}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-emerald-950/40 transition flex items-center justify-center gap-2"
          >
            <CheckCircle2 className="w-5 h-5" />
            Emitir Factura POS ({formatCOP(total)})
          </button>
        </div>
      </div>
    </div>
  );
};

export default PosTerminal;
