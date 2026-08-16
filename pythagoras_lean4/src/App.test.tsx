import { describe, it, expect } from 'vitest';
import { validateGeometry } from './engine/geometryEngine';
import { LeanKernelSimulator } from './engine/leanKernelSimulator';
import { generateLeanProject } from './engine/proofExporter';

describe('Pythagorean Domain Verification Engine', () => {
  it('validates Euclidean right triangle geometry and computes hypotenuse', () => {
    const params = validateGeometry(3, 4);
    expect(params.isValid).toBe(true);
    expect(params.c).toBe(5);
  });

  it('generates a verified 6-step Lean 4 tactic progression', () => {
    const simulator = new LeanKernelSimulator();
    const params = validateGeometry(6, 8);
    const tactics = simulator.generateTacticSequence(params);
    expect(tactics.length).toBe(6);
    expect(simulator.verifyProofCertificate(tactics)).toBe(true);
    expect(tactics[5].status).toBe('PROVEN');
  });

  it('exports mathlib-compatible Lean 4 code with cryptographic checksum', () => {
    const params = validateGeometry(5, 12);
    const project = generateLeanProject(params);
    expect(project.leanSource).toContain('theorem pythagorean_dissection');
    expect(project.leanSource).toContain('t.a^2 + t.b^2 = t.c^2');
    expect(project.verificationHash).toMatch(/^0x[0-9a-f]{8}$/);
  });
});