"""Service layer — the functions a FastAPI app will wrap 1:1 (ARCHITECTURE §2.7 rule 4).

🛑 **THIS PACKAGE IS EMPTY AND THE `cli -> api -> core` BOUNDARY IS ASPIRATIONAL,
NOT REAL.** Stated plainly here because a layer that is documented but absent
reads as satisfied to the next session — the same failure shape as a guard that
is documented and not implemented.

Measured 2026-08-06 (session `3d`, B5): this package contains **zero functions**,
**nothing anywhere imports it**, and **5 of 7 `cli/` entry points import `core/`
directly** (`crosswalk`, `mechanics`, `profile`, `relationships`, `sim`; the
other two are `rebuild`, a subprocess runner, and `browse`, which shells out to
Datasette). The 1a-era note that *"`spell_profile()` (Task 7) is the first"*
module to land here was a plan, not a record — Task 7 shipped as
`core/spells/profile.py` + `cli/profile.py`, bypassing this layer entirely.

⚠ `PHASE_4_*`'s premise *"the web app is a thin layer: `api/` already exists"*
is therefore **false comfort**. The directory exists; the layer does not.

**The decision the package name encodes is still worth keeping** — a web API
must be able to call the identical function a CLI does, and `core/` purity
(enforced, 47 files, 0 violations) is what actually makes that possible. The
honest statement is that `core/` is the reusable layer today and `api/` is a
reserved name. Whoever first needs a served function should build it here and
route one CLI through it, converting this from a reservation into a boundary.

The intended layering, when it becomes real:

    cli/  ->  api/  ->  core/          never the reverse, and never cli/ -> core/
                                       directly once the api/ function exists
"""
