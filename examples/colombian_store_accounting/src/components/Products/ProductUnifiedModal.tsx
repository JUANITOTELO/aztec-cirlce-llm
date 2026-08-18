import React, { useState, useEffect } from 'react';
import { Product } from '../../types/store';
import { Category } from '../../types/category';
import { ProductVariant } from '../../types/productVariant';
import { ProductImage } from '../../types/productMedia';
import { ProductFormTabs, ProductFormTab } from './ProductFormTabs';
import { ProductFormGeneral } from './ProductFormGeneral';
import { ProductVariantManager } from './ProductVariantManager';
import { ProductMediaCoordinator } from './ProductMediaCoordinator';
import { MediaProvider } from '../../context/MediaContext';
import { db } from '../../db/dexie';
import { X, Save } from 'lucide-react';

interface ProductUnifiedModalProps {
  isOpen: boolean;
  product: Product | null;
  categories: Category[];
  variants: ProductVariant[];
  images: ProductImage[];
  onSave: (product: Product) => void;
  onClose: () => void;
  onUpdateVariants?: (variants: ProductVariant[]) => void;
  onUpdateImages?: (images: ProductImage[]) => void;
}

export const ProductUnifiedModal: React.FC<ProductUnifiedModalProps> = ({
  isOpen,
  product,
  categories,
  variants,
  images,
  onSave,
  onClose,
  onUpdateVariants,
  onUpdateImages,
}) => {
  const [activeTab, setActiveTab] = useState<ProductFormTab>('general');
  const [formData, setFormData] = useState<Partial<Product>>({
    id: '',
    name: '',
    sku: '',
    category: categories[0]?.name || '',
    price: 0,
    cost: 0,
    stock: 0,
    minStock: 5,
    ivaRate: 0.19,
    barcode: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (product) {
      setFormData(product);
    } else {
      const generatedId = `prod-${Date.now()}`;
      setFormData({
        id: generatedId,
        name: '',
        sku: `SKU-${Date.now().toString().slice(-4)}`,
        category: categories[0]?.name || '',
        price: 0,
        cost: 0,
        stock: 0,
        minStock: 5,
        ivaRate: 0.19,
        barcode: '',
      });
    }
    setActiveTab('general');
    setErrors({});
  }, [product, categories, isOpen]);

  if (!isOpen) return null;

  const currentProductId = formData.id || '';
  const activeVariants = currentProductId ? variants.filter((v) => v.productId === currentProductId) : [];
  const activeImages = currentProductId ? images.filter((img) => img.productId === currentProductId) : [];

  const handleFieldChange = (field: keyof Product, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors: Record<string, string> = {};
    if (!formData.name?.trim()) validationErrors.name = 'El nombre es obligatorio';
    if (!formData.sku?.trim()) validationErrors.sku = 'El SKU es obligatorio';
    if (!formData.category?.trim()) validationErrors.category = 'Seleccione una categoría';

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      setActiveTab('general');
      return;
    }

    let primaryImageUrl = formData.image;
    try {
      const dbImgs = await db.productImages.where('productId').equals(currentProductId).toArray();
      const primary = dbImgs.find((img) => img.isPrimary || img.imageType === 'PRIMARY') || dbImgs[0];
      if (primary?.url) {
        primaryImageUrl = primary.url;
      }
      if (onUpdateImages && dbImgs.length > 0) {
        onUpdateImages(dbImgs);
      }
    } catch (err) {
      console.warn('Could not query Dexie productImages on save:', err);
    }

    const finalProduct: Product = {
      ...(formData as Product),
      image: primaryImageUrl,
    };

    onSave(finalProduct);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <MediaProvider
        productId={currentProductId}
        variants={activeVariants}
        initialImages={images}
        onImagesUpdated={onUpdateImages}
      >
        <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden my-auto">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/80">
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                {product ? 'Editar Producto & Variantes' : 'Crear Nuevo Producto'}
                <span className="text-xs font-normal text-slate-400 font-mono bg-slate-800 px-2 py-0.5 rounded">
                  {formData.sku || 'Nuevo'}
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">Administre catálogo, atributos, existencias e imágenes sincronizadas.</p>
            </div>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <ProductFormTabs
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            variantCount={activeVariants.length}
            imageCount={activeImages.length}
          />

          <div className="flex-1 overflow-y-auto">
            {activeTab === 'general' && (
              <ProductFormGeneral
                formData={formData}
                onChange={handleFieldChange}
                categories={categories}
                errors={errors}
              />
            )}
            {activeTab === 'variants' && (
              <div className="p-6">
                <ProductVariantManager
                  productId={currentProductId}
                  productSku={formData.sku}
                  productPrice={formData.price}
                  productCost={formData.cost}
                  variants={activeVariants}
                  images={activeImages}
                  onVariantsUpdated={onUpdateVariants}
                  onImagesUpdated={onUpdateImages}
                />
              </div>
            )}
            {activeTab === 'media' && (
              <div className="p-6">
                <ProductMediaCoordinator
                  product={formData as Product}
                  productId={currentProductId}
                  variants={activeVariants}
                  inline={true}
                />
              </div>
            )}
          </div>

          <div className="flex items-center justify-between px-6 py-3 border-t border-slate-800 bg-slate-950/80">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-900/30 transition-all"
            >
              <Save className="w-4 h-4" />
              <span>Guardar Producto Completo</span>
            </button>
          </div>
        </div>
      </MediaProvider>
    </div>
  );
};
