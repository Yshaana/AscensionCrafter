# Pre-registration — `3g` close-out, the holdout read

> **`FINDING 2026-08-07`** — a prediction made before the measurement that tests it.
> True as of its date and **not maintained**. **Expires when `3g`'s session record
> lands** and records the outcome beside it. *(Born with a status line and an expiry
> condition, per `3f` F8c.)*

**Committed BEFORE `--read-holdout` is run.** The holdout's entire value is that
nothing was tuned against it, and a prediction written afterwards is worth
nothing. Same construction as `prereg_3g_e13.md` and `prereg_3g_e14.md`: this
file lands in one commit, the read in the next.

Members: **460, 461, 462, 463, 7661** (`holdout_3e_crawled_gate_validation_set`,
registered in `3d`, split out of the headline in `3e` A1).

Last read at `3e`'s close-out, stamped with the commit that took it (`c7d2892`):
**0 of 5**, deltas **−45% to −98%**, three members carrying **27–69%** coverage.

🛑 **Read ONCE, at close-out, after G1, G2, G3 and G4 have all landed** — owner
decision §0.8.3, and not after E13 alone.

---

## What I know without reading it, and what I am therefore predicting

Everything below follows from the tuning set's behaviour plus the mechanism, not
from any holdout number.

**1. `0 of 5` within ±20%.** It was 0 of 5 before, every delta was negative, and
both fixes this session move deltas **down**:

* **E13** removes a factor of exactly 100 from every white swing. On the tuning
  set the auto was 89–96% of sim damage for fourteen of 36 characters, and the
  cohort's median slice accuracy fell 64.3% → 20.5%. Any holdout member with a
  melee auto moves sharply more negative.
* **E14** is mixed for these five: two of them hold cards it touches (460 holds
  `281103` Mycelial Ring, 3 → 10 ticks, and `285133` Devour Mind, 2 → 4; 462
  holds `282977` Summon Void Zone, which now **refuses** on a non-positive
  sentinel duration and loses that component). So 460 gains a little and 462
  loses a little.

A member at −45% would need to *gain* to reach −20%, and nothing in this session
adds damage on net.

**2. Some members become NOT SCOREABLE rather than False.** G4's 20% coverage
floor is in force. `3e` recorded three members at 27–69% coverage, which leaves
**two below 27%**; if either is under 20% it now reports `None`. **I do not know
how many** — stated as unknown rather than guessed.

**3. The holdout should look like the tuning set, and that is the real test.**
Post-`3g` the tuning set is one-sidedly negative with a median slice accuracy of
**20.5%** — the sim reproduces about a fifth of what it models. If the holdout's
deltas land in the same family, the tuning set's numbers are not an artifact of
having been looked at. **If the holdout looks materially BETTER than the tuning
set, that is the finding**, and it would mean something about the tuning set is
selection-shaped rather than model-shaped.

## What would falsify the session's own story

* **Any holdout member inside ±20%** would be surprising and would need
  explaining rather than celebrating — nothing this session did adds damage.
* **A holdout median slice accuracy near the old 64.3%** rather than near 20.5%
  would say E13's exposure is specific to the tuning set, which nothing suggests
  (E13 is a unit error in shared code, not a property of a board).

🛑 **The result is recorded unsoftened whichever way it goes**, and stamped with
the commit that took it — the pattern `3f` used when it carried `3e`'s reading
forward rather than erasing it.
