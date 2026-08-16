export type PucClase = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9';
export type PucNivel = 'CLASE' | 'GRUPO' | 'CUENTA' | 'SUBCUENTA' | 'AUXILIAR';
export type AccountNature = 'DEBITO' | 'CREDITO';

export interface PucAccount {
  code: string;
  name: string;
  level: PucNivel;
  nature: AccountNature;
  acceptsMovement: boolean;
  parentCode?: string;
}