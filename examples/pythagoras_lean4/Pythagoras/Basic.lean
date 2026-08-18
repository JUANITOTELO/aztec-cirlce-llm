-- Formal Verification of Geometric Dissections (Pythagoras, Binomial Euclid II.4, Gougu)

namespace DissectionProofs

/-- Pythagorean Theorem via Geometric Square Dissection -/
theorem pythagoras_dissection_nat (a b c : Nat)
    (h_outer : (a + b) * (a + b) = c * c + 2 * a * b) :
    a * a + b * b = c * c := by
  omega

/-- Binomial Square Dissection (Euclid II.4 / Yang Hui) -/
theorem binomial_dissection_nat (a b : Nat) :
    (a + b) * (a + b) = a * a + 2 * a * b + b * b := by
  omega

/-- Zhao Shuang Xian Tu Dissection -/
theorem gougu_xiantu_dissection_nat (gou gu xian : Nat)
    (h_xiantu : xian * xian = 2 * gou * gu + (gu - gou) * (gu - gou)) :
    gou * gou + gu * gu = xian * xian := by
  omega

end DissectionProofs

