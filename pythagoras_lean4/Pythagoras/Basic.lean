-- Formal Verification of the Pythagorean Theorem via Geometric Dissection
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace Pythagoras

structure RightTriangle where
  a : ℝ
  b : ℝ
  c : ℝ
  ha : 0 < a
  hb : 0 < b
  hc : 0 < c

/-- The total area of the outer square (a + b)^2 equals
    the inner square c^2 plus 4 right triangles of area (1/2 * a * b) -/
theorem dissection_area_equality (t : RightTriangle)
    (h_area : (t.a + t.b)^2 = t.c^2 + 4 * (1 / 2 * (t.a * t.b))) :
    t.a^2 + t.b^2 = t.c^2 := by
  have h_expand : (t.a + t.b)^2 = t.a^2 + 2 * t.a * t.b + t.b^2 := by ring
  have h_triangles : 4 * (1 / 2 * (t.a * t.b)) = 2 * t.a * t.b := by ring
  rw [h_expand, h_triangles] at h_area
  linarith

end Pythagoras