import React, { useState } from 'react';
import { Product, CartItem, SaleInvoice } from '../../types/store';
import { ProductVariant } from '../../types/productVariant';
import { ProductImage } from '../../types/productMedia';
import { INITIAL_VARIANTS, INITIAL_PRODUCT_IMAGES } from '../../constants/mockVariants';
import { formatCOP, calculateCartTotals } from '../../utils/formatters';
import { ShoppingCart, Plus, Minus, Trash2, CheckCircle2, Search, CreditCard, DollarSign, Smartphone, Package, Sparkles } from 'lucide-react';

interface PosTerminalProps {
  products: Product[];
  variants?: ProductVariant[];
  images?: ProductImage[];
  onCompleteSale: (invoice: SaleInvoice) => void;
}

export const PosTerminal: React.FC<PosTerminalProps> = ({
  products,
  variants = INITIAL_VARIANTS,
  images = INITIAL_PRODUCT_IMAGES,
  onCompleteSale,
}) => {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Todos');
  const [paymentMethod, setPaymentMethod] = useState<'Efectivo' | 'Tarjeta' | 'Nequi / Daviplata'>('Efectivo');
  const [customerDoc, setCustomerDoc] = useState('222222222222'); // Consumidor Final DIAN
  const [customerName, setCustomerName] = useState('Consumidor Final');
  const [selectedVariantModalProduct, setSelectedVariantModalProduct] = useState<Product | null>(null);

  const categories = ['Todos', 'Abarrotes', 'Bebidas', 'Lácteos', 'Aseo', 'Snacks'];

  const getProductImage = (productId: string, variantId?: string) => {
    if (variantId) {
      const varImg =
        images.find((img) => img.variantId === variantId && (img.isPrimary || img.imageType === 'PRIMARY')) ||
        images.find((img) => img.variantId === variantId);
      if (varImg?.url) return varImg.url;
    }
    const primaryProdImg = images.find((img) => img.productId === productId && (img.isPrimary || img.imageType === 'PRIMARY'));
    if (primaryProdImg?.url) return primaryProdImg.url;

    const anyProdImg = images.find((img) => img.productId === productId);
    if (anyProdImg?.url) return anyProdImg.url;

    const prod = products.find((p) => p.id === productId);
    return prod?.image || null;
  };

  const getProductVariants = (productId: string) => {
    return variants.filter((v) => v.productId === productId && v.isActive);
  };

  const filteredProducts = products.filter((p) => {
    const matchesCat = selectedCategory === 'Todos' || p.category === selectedCategory;
    const prodVars = getProductVariants(p.id);
    const variantMatches = prodVars.some(
      (v) => v.name.toLowerCase().includes(search.toLowerCase()) || v.sku.toLowerCase().includes(search.toLowerCase())
    );
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.barcode ? p.barcode.includes(search) : false) ||
      p.sku.toLowerCase().includes(search.toLowerCase()) ||
      variantMatches;
    return matchesCat && matchesSearch;
  });

  const addToCart = (product: Product, variant?: ProductVariant) => {
    const cartProduct: Product = variant
      ? {
          ...product,
          id: `${product.id}-${variant.id}`,
          name: variant.name,
          sku: variant.sku,
          barcode: variant.barcode,
          price: variant.price,
          cost: variant.cost,
          stock: variant.stock,
        }
      : product;

    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === cartProduct.id);
      if (existing) {
        return prev.map((item) =>
          item.product.id === cartProduct.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { product: cartProduct, quantity: 1 }];
    });
  };

  const handleProductCardClick = (product: Product) => {
    const prodVars = getProductVariants(product.id);
    if (prodVars.length > 1) {
      setSelectedVariantModalProduct(product);
    } else if (prodVars.length === 1) {
      addToCart(product, prodVars[0]);
    } else {
      addToCart(product);
    }
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
    setCart([]);
  };

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)]">
      {/* Product Catalog Column */}
      <div className="lg:col-span-7 flex flex-col space-y-4 min-h-0">
        <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700 space-y-3">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar producto por nombre, SKU, variación o código..."
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
          {filteredProducts.map((product) => {
            const prodVars = getProductVariants(product.id);
            const defaultVar = prodVars.find((v) => v.isDefault) || prodVars[0];
            const imgUrl = getProductImage(product.id, defaultVar?.id);
            const displayPrice = defaultVar ? defaultVar.price : product.price;
            const hasMultipleVariants = prodVars.length > 1;

            return (
              <div
                key={product.id}
                className="bg-slate-800/90 border border-slate-700 hover:border-emerald-500/60 rounded-xl overflow-hidden transition flex flex-col justify-between group hover:shadow-lg hover:shadow-emerald-950/20"
              >
                <div className="cursor-pointer" onClick={() => handleProductCardClick(product)}>
                  <div className="relative w-full h-28 bg-slate-900 overflow-hidden flex items-center justify-center">
                    {imgUrl ? (
                      <img
                        src={imgUrl}
                        alt={product.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const parent = e.currentTarget.parentElement;
                          const fallback = parent?.querySelector('.fallback-placeholder');
                          if (fallback) (fallback as HTMLElement).style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div
                      className={`fallback-placeholder flex-col items-center justify-center text-slate-600 ${
                        imgUrl ? 'hidden' : 'flex'
                      }`}
                    >
                      <Package className="w-8 h-8 stroke-[1.5] mb-1" />
                      <span className="text-[10px]">Sin imagen</span>
                    </div>
                  </div>

                  <div className="p-2.5 space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span>{product.sku || product.barcode}</span>
                      <span className="font-medium bg-slate-700/60 px-1.5 py-0.5 rounded text-slate-300">
                        Stock: {product.stock}
                      </span>
                    </div>
                    <h3 className="font-semibold text-white text-xs line-clamp-2 leading-snug group-hover:text-emerald-400 transition">
                      {product.name}
                    </h3>
                  </div>
                </div>

                {/* Quick Variations Chips (if available) */}
                {hasMultipleVariants ? (
                  <div className="px-2.5 py-1 flex flex-wrap gap-1 border-t border-slate-700/40 bg-slate-900/30">
                    {prodVars.slice(0, 3).map((v) => (
                      <button
                        key={v.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          addToCart(product, v);
                        }}
                        title={v.name}
                        className="text-[10px] bg-slate-700/80 hover:bg-emerald-600 hover:text-white text-slate-300 px-1.5 py-0.5 rounded transition truncate max-w-full font-medium"
                      >
                        +{Object.values(v.attributes || {})[0] || v.name.split(' ').slice(-1)[0]}
                      </button>
                    ))}
                  </div>
                ) : null}

                {/* Footer Price & Add Button */}
                <div className="p-2.5 pt-2 border-t border-slate-700/60 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400">IVA: {product.ivaRate > 0 ? '19%' : 'Exento'}</div>
                    <div className="text-emerald-400 font-bold text-sm">{formatCOP(displayPrice)}</div>
                  </div>
                  <button
                    onClick={() => handleProductCardClick(product)}
                    className="w-7 h-7 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center hover:bg-emerald-600 hover:text-white transition shadow-sm"
                    title="Agregar al carrito"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
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

      {/* Modal for Multiple Variations Selection */}
      {selectedVariantModalProduct && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-white text-base">Seleccionar Variación</h3>
                <p className="text-xs text-slate-400">{selectedVariantModalProduct.name}</p>
              </div>
              <button
                onClick={() => setSelectedVariantModalProduct(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded-lg bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {getProductVariants(selectedVariantModalProduct.id).map((v) => (
                <button
                  key={v.id}
                  onClick={() => {
                    addToCart(selectedVariantModalProduct, v);
                    setSelectedVariantModalProduct(null);
                  }}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800/80 hover:bg-emerald-950/60 border border-slate-700 hover:border-emerald-500/50 text-left transition group"
                >
                  <div>
                    <div className="text-sm font-semibold text-white group-hover:text-emerald-300 transition">
                      {v.name}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 flex gap-2 font-mono">
                      <span>SKU: {v.sku}</span>
                      <span>Stock: {v.stock}</span>
                    </div>
                  </div>
                  <div className="text-right pl-2">
                    <div className="text-emerald-400 font-bold text-sm font-mono">{formatCOP(v.price)}</div>
                    <span className="text-[10px] text-emerald-500 font-semibold">+ Agregar</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default PosTerminal;
