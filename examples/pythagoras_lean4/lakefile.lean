import Lake
open Lake DSL

package «pythagoras» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

@[default_target]
lean_lib «Pythagoras» where
  globs := #[Glob.submodules `Pythagoras]
