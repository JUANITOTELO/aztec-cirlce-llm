import React from 'react';
import { MannequinTheme } from '../types/dummy13';
import { X, Check } from 'lucide-react';

interface ThemeCustomizerProps {
  theme: MannequinTheme;
  onChangeTheme: (theme: MannequinTheme) => void;
  onClose: () => void;
}

const THEME_PALETTES: MannequinTheme[] = [
  {
    name: 'Cyberpunk Neon',
    armorColor: '#0f172a',
    frameColor: '#334155',
    jointColor: '#0284c7',
    accentColor: '#00f0ff',
    roughness: 0.25,
    metalness: 0.8
  },
  {
    name: 'T13 Classic Solar Yellow',
    armorColor: '#eab308',
    frameColor: '#18181b',
    jointColor: '#27272a',
    accentColor: '#facc15',
    roughness: 0.4,
    metalness: 0.1
  },
  {
    name: 'Stealth Matte Black',
    armorColor: '#1e2022',
    frameColor: '#0a0a0b',
    jointColor: '#ef4444',
    accentColor: '#dc2626',
    roughness: 0.85,
    metalness: 0.1
  },
  {
    name: 'Eva Unit-01 Mecha',
    armorColor: '#6d28d9',
    frameColor: '#15803d',
    jointColor: '#18181b',
    accentColor: '#f97316',
    roughness: 0.35,
    metalness: 0.4
  },
  {
    name: 'Clean Ceramic White',
    armorColor: '#f8fafc',
    frameColor: '#334155',
    jointColor: '#0ea5e9',
    accentColor: '#38bdf8',
    roughness: 0.15,
    metalness: 0.05
  }
];

export const ThemeCustomizer: React.FC<ThemeCustomizerProps> = ({
  theme,
  onChangeTheme,
  onClose
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-dummyPanel rounded-2xl border border-dummyBorder p-6 shadow-2xl text-slate-100">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-dummyBorder">
          <h2 className="text-lg font-bold">Dummy 13 Color Customizer</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Preset Palettes */}
        <div className="mb-5">
          <label className="text-xs font-semibold text-slate-400 block mb-2">Color Palettes</label>
          <div className="grid grid-cols-1 gap-2">
            {THEME_PALETTES.map((p) => {
              const isSelected = theme.name === p.name;
              return (
                <button
                  key={p.name}
                  onClick={() => onChangeTheme(p)}
                  className={`flex items-center justify-between p-2.5 rounded-xl border text-xs font-medium transition ${
                    isSelected
                      ? 'bg-dummyAccent/20 border-dummyAccent text-white'
                      : 'bg-dummyDark border-dummyBorder text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className="flex -space-x-1">
                      <div className="w-4 h-4 rounded-full border border-black" style={{ backgroundColor: p.armorColor }} />
                      <div className="w-4 h-4 rounded-full border border-black" style={{ backgroundColor: p.frameColor }} />
                      <div className="w-4 h-4 rounded-full border border-black" style={{ backgroundColor: p.accentColor }} />
                    </div>
                    <span>{p.name}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-dummyAccent" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Detailed Swatches */}
        <div className="grid grid-cols-2 gap-3 mb-5">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Armor Plates</label>
            <div className="flex items-center gap-2 bg-dummyDark p-2 rounded-lg border border-dummyBorder">
              <input
                type="color"
                value={theme.armorColor}
                onChange={(e) => onChangeTheme({ ...theme, name: 'Custom', armorColor: e.target.value })}
                className="w-7 h-7 rounded border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs font-mono text-slate-300">{theme.armorColor}</span>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Internal Frame</label>
            <div className="flex items-center gap-2 bg-dummyDark p-2 rounded-lg border border-dummyBorder">
              <input
                type="color"
                value={theme.frameColor}
                onChange={(e) => onChangeTheme({ ...theme, name: 'Custom', frameColor: e.target.value })}
                className="w-7 h-7 rounded border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs font-mono text-slate-300">{theme.frameColor}</span>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Joint Sockets</label>
            <div className="flex items-center gap-2 bg-dummyDark p-2 rounded-lg border border-dummyBorder">
              <input
                type="color"
                value={theme.jointColor}
                onChange={(e) => onChangeTheme({ ...theme, name: 'Custom', jointColor: e.target.value })}
                className="w-7 h-7 rounded border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs font-mono text-slate-300">{theme.jointColor}</span>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Visor Glow</label>
            <div className="flex items-center gap-2 bg-dummyDark p-2 rounded-lg border border-dummyBorder">
              <input
                type="color"
                value={theme.accentColor}
                onChange={(e) => onChangeTheme({ ...theme, name: 'Custom', accentColor: e.target.value })}
                className="w-7 h-7 rounded border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs font-mono text-slate-300">{theme.accentColor}</span>
            </div>
          </div>
        </div>

        {/* Material Properties */}
        <div className="space-y-3 mb-6">
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Roughness (Matte / Gloss)</span>
              <span>{Math.round(theme.roughness * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="1"
              step="0.05"
              value={theme.roughness}
              onChange={(e) => onChangeTheme({ ...theme, roughness: parseFloat(e.target.value) })}
              className="w-full accent-dummyAccent bg-dummyDark h-1.5 rounded-lg cursor-pointer"
            />
          </div>
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Metallic Sheen</span>
              <span>{Math.round(theme.metalness * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={theme.metalness}
              onChange={(e) => onChangeTheme({ ...theme, metalness: parseFloat(e.target.value) })}
              className="w-full accent-dummyAccent bg-dummyDark h-1.5 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 bg-dummyAccent hover:bg-dummyAccentHover text-white rounded-xl font-semibold text-sm transition shadow-lg shadow-blue-500/25"
        >
          Apply & Close
        </button>
      </div>
    </div>
  );
};
