- 2026-10-11 (after freeze, before the official run): runner `tools/run_official.py` tested on dev seed 3
  (`runs/dev/seed3/`, NOT RESULTS; not included here). It ran in 37 s, and pool K=2 median $14.39 matched theory ×0.143. The dev test
  also showed the crowd average peaking at flip 648, outside my frozen 100-250 guess. Re-derived by hand: my ~146
  estimate was the flip where the crowd average starts to fall *behind* 1.05ⁿ (the players carrying the average run
  out). The *peak* comes later, when even the luckiest players left stop growing faster than they thin out: solving
  (q·ln1.5 + (1−q)·ln0.6)·ln(q/(1−q)) = ln(2.5)·KL(q‖½) gives q ≈ 0.613, n ≈ ln(10⁶)/KL ≈ 540 (plus finite-size
  corrections). Prediction 2 stays frozen as written; if seed 108 also lands outside 100-250, the slip gets a cross and
  the video explains this mistake (STORYBOARD §5 branch). Also said aloud: the dev test came after the freeze.
- 2026-10-11: OFFICIAL RESULTS (seed 108, re-run 109; `numbers.json` from `tools/make_numbers.py`, predictions scored
  by code against the frozen rules):
  1. ✓ 99.95 % ruined at 1,000 flips (999,506 of 1 M; re-run 99.96 %); 140 players ahead (re-run 138).
  2. ✗ **My guess was wrong.** The crowd average peaked at flip 693 (re-run 555), not 100-250. Cause: see the dev-test
     note above (I estimated where the average starts to slip, not where it peaks). Goes in the video as is.
  3. ✓ betting 25 % gives the best typical result ($100 → $49,833); betting half ends at exactly $100.
  4. ✓ pairs who share still shrink ($14.39 typical) though 42.5 % of pairs are ahead; groups of 10 and 100 grow
     astronomically (every group ahead).
  Not predicted, found: at 1,000 flips the crowd average is still $616 (above the $100 start), but one single player
  holds 60 % of all the money (re-run 99 %) → wording "more than half". The average is "making money" because of
  one person.
  Title by the frozen rule: "This Bet Makes Money on Average. It Ruined 999,506 of 1 Million People."
