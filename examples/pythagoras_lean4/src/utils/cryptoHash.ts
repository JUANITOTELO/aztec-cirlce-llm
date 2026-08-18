/**
 * Computes deterministic FNV-1a 32-bit hash representation
 * for Merklized tactic step validation.
 */
export function computeProofHash(data: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < data.length; i++) {
    hash ^= data.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return '0x' + (hash >>> 0).toString(16).padStart(8, '0');
}

export function computeMerkleRoot(hashes: readonly string[]): string {
  if (hashes.length === 0) return '0x00000000';
  return hashes.reduce((acc, curr) => computeProofHash(`${acc}:${curr}`));
}