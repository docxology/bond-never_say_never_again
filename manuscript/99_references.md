# References

Bibliography entries live in `manuscript/references.bib` and are cited by key
in the prose sections; this page is the human-readable mirror. Every model this
package implements is attributed to a real, checkable source — nothing is cited
that the code does not implement.

## Models implemented here

1. Nemhauser, G. L., Wolsey, L. A., & Fisher, M. L. (1978). An Analysis of
   Approximations for Maximizing Submodular Set Functions—I. *Mathematical
   Programming*, 14(1), 265–294. doi:10.1007/BF01588971 — the greedy
   marginal-gain setting behind `asset_allocator.py`. Their `(1 - 1/e)` bound is
   the general monotone-submodular case; the allocator's separable-concave
   instance is the easier one where greedy is exactly optimal.
2. Wright, T. P. (1936). Factors Affecting the Cost of Airplanes. *Journal of
   the Aeronautical Sciences*, 3(4), 122–128. doi:10.2514/8.155 — the learning
   curve behind `learning_curve.py`.
3. Barlow, R. E., & Proschan, F. (1975). *Statistical Theory of Reliability and
   Life Testing: Probability Models.* Holt, Rinehart and Winston — the
   series/parallel reliability block diagram in `remount_risk.py`.
4. Ross, S. M. (2019). *Introduction to Probability Models* (12th ed.).
   Academic Press — the homogeneous Poisson detection hazard in
   `remount_risk.py`.
5. Verhulst, P.-F. (1838). Notice sur la loi que la population suit dans son
   accroissement. *Correspondance Mathématique et Physique*, 10, 113–121 — the
   logistic success curve in `mission_replay.py`.
6. National Institute of Standards and Technology (2015). *Secure Hash Standard
   (SHS)*, FIPS PUB 180-4. doi:10.6028/NIST.FIPS.180-4 — SHA-256 asset
   fingerprinting in `legacy_assets.py`.
7. The Unicode Consortium (2023). *Unicode Standard Annex #15: Unicode
   Normalization Forms.* <https://www.unicode.org/reports/tr15/> — the NFC
   normalization applied before hashing.

## BOND suite (unpublished local working trees)

8. Friedman, D. A. (2026). *BOND-API: The Frozen Mission Protocol Contract for
   the BOND Film Suite.* Unpublished software, PROJECT BOND local working tree
   (`projects/working/bond/bond-api`) — no remote, no DOI. The protocol
   `mission.py` implements.
9. Friedman, D. A. (2026). *BOND-Utilities (Q-BRANCH): Layer 0 Foundation.*
   Unpublished software, PROJECT BOND local working tree
   (`projects/working/bond/bond-utilities`) — no remote, no DOI. Not bound by
   this package; listed because `TODO.md` names it as a declared integration
   point.

## Source work

10. *Never Say Never Again* (1983). Directed by Irvin Kershner. Warner Bros. —
    a remount of *Thunderball* (1965), the premise this package models.
