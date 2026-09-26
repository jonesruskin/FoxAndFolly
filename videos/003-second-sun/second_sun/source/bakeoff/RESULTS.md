# Pipeline bake-off — S19 "second sunrise" at test quality

| | A — Blender 4.0.2 (headless bpy) | B — 2.5D Skia + NumPy (chosen) |
|---|---|---|
| Build | skin-modifier Triceratops on an edge skeleton + subsurf, displaced ridge with Saddle notch, split-tree cones, emissive "second sun", sun lamp, glossy lake | procedural layered environment, rigged 2D creatures (IK, foot-locked gaits), rim-lit "lantern luminism" forms, post stack (god rays, bloom, DOF, grade, grain) |
| Cycles, 960×540, 64 spp | **13.5 s/frame**, no denoiser in the distro build (OIDN missing) → visibly noisy; ≈ 55 s/frame at 1080p → **~28 h** for 7,400 frames on 4 cores | — |
| Eevee, 960×540 | 2.4 s/frame via software (surfaceless EGL/llvmpipe) → ≈ 9 s at 1080p → **~18 h**; bloom works, no GPU | — |
| B, 1920×1080 | — | **1.0–2.4 s/frame** (single core) → ≈ 1 h for the film on 4 cores |
| Look | clay-toy forms; making organic, expressive dinosaurs needs sculpt/retopo/rig work well beyond the schedule; flat lighting without long render times | art-directable silhouettes and rim light exactly as the visual bible asks ("sculpted, rim-lit forms with restrained interior detail"); painterly atmosphere cheap |
| Animation | armature rigging of skin-modifier meshes is feasible but slow to iterate headless | per-frame parametric poses, IK and distance-based gaits give zero foot sliding by construction |
| Iteration | minutes per test frame | seconds per test frame |

**Decision: B.** Blender is kept as a documented fallback (`blender_s19.py`), not used in the final.
Frames: `A_blender_cycles_S19.png`, `A_blender_eevee_S19.png`, `B_skia_S19_lockoff.png`, `B_skia_S19_close.png`.
