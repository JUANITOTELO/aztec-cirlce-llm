import Lake
open Lake DSL

package «pythagoras» where
  version := v!"0.1.0"
  keywords := #["math", "geometry", "formal-verification", "pythagoras"]
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

@[default_target]
lean_lib «Pythagoras» where
  globs := #[Glob.submodules `Pythagoras]