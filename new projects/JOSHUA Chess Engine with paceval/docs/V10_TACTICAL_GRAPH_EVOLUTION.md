# JOSHUA V10: mathematical scope, graph evolution and reproducibility

## Scientific motivation

JOSHUA's older coefficient learner could not create a new mathematical relationship. V10 allows bounded, named nonlinear template expressions to be added to the score graph and activated from a persistent TSV. The C++ host remains responsible for chess move generation, search tree control, state, board-feature extraction and UCI process orchestration. Real paceval handles evaluate the V4 neural graphs, adaptive composite score and supported mathematical reductions. Stockfish is an external reference only, not an implementation of paceval's mathematics.

## Graph catalog

The code builds every expression via `Engine::create`, storing a handle-to-index registration. The evaluations from `Engine::eval`, `Engine::single`, `Engine::multi`, and the initial multi-graph layout probe increment the corresponding actual-point counter. The engine writes `paceval_all_graphs.csv` after the game move(s) along with a separate adaptive TXT and CSV. Long neural expressions are preserved *without abbreviation* in the CSV `paceval_expression` field. Graph IDs are process-local sequential IDs, not stable global hashes. Each engine launch re-registers its graphs. The active adaptive expression is identified by its saved version and a SHA-256 of the exported TXT. A graph with `evaluated_points=0` was registered but not evaluated during that run.

The original `formulas/v4_graph_expressions.tsv` contains the V4 training-derived graph formulas; the V10 full catalog records which graphs were created and executed in a specific run. Counts from a subprocess must not be summed across its orchestration or independent control replays and described as unique graphs.

## Bounded structural grammar

Eight linear feature differences persist from V9. The V10 nonlinear whitelist consists of:

| Template | Exact paceval mathematical text |
|---|---|
| `king_alarm` | `((bkingDanger*bkingDanger)-(wkingDanger*wkingDanger))` |
| `king_tactics` | `((bkingDanger*(1+bqueenThreat+brookThreat))-(wkingDanger*(1+wqueenThreat+wrookThreat)))` |
| `hanging_pressure` | `((bhanging*bhanging)-(whanging*whanging))` |
| `queen_exposure` | `((bqueenThreat*battacked)-(wqueenThreat*wattacked))` |
| `rook_exposure` | `((brookThreat*battacked)-(wrookThreat*wattacked))` |
| `check_pressure` | `(bcheck-wcheck)` |
| `pawn_race` | `((wpassed*wpassed)-(bpassed*bpassed))` |
| `active_captures` | `((wmob*wcaps)-(bmob*bcaps))` |

A template reflects limited board-derived threat proxies and should not be mistaken for legal combinations, tactical proof or forced-mate recognition. Checkmates and legality are managed separately by chess-rule logic. Coefficients are finite decimal values with at most four fractional digits, absolute magnitude at most 8 for nonlinear terms, and a maximum of six nonzero added terms. Linear adjustments retain an absolute bound of 32. The final correction score is clamped between -160 and +160. Template names are fixed in C++ code, so a malicious TSV expression cannot reach the SDK parser as untrusted formula source.

## Tactical analysis and score

The original V9 mean CP loss was dominated by substituted mate scores near thirty thousand. V10 preserves original UCI `cp` or `mate` scores and logs a separate mate alert. Its heuristic expected-score function is $p(c)=1/(1+\exp(-c/180))$, and an actual move is compared with the before/after teacher estimates. With $p_b$ from the player-to-move perspective before the move and $p_o$ from the opponent perspective after the move, the bounded loss is $100\max(0,p_b+p_o-1)$. Scores cannot establish an absolute Elo rating, nor is this function claimed to be calibrated to official Stockfish WDL. The actual reference teacher is Stockfish when available; unit tests use deliberately marked mocks.

## Promotion controls

The initial four matched color pairs per version preserve the base model for baseline evidence. For later pairs, the host selects high-loss FENs from the last matching pair, selects a tactical term (king templates prioritized for mate alerts) and tries signed bounded perturbations of one nonlinear template and one linear coefficient. For each candidate, the **same original Joshua binary and paceval library** recompute moves on the training FENs and separate deterministic holdout FENs. The reference Stockfish process grades both original and candidate moves with fixed nodes and cleared hash. An accepted candidate needs a changed decision, a better mean training loss and safe heldout results. A candidate failing to compile, parse or execute is rejected with a recorded error. A local gate remains provisional. After a successful trial, the controller atomically updates the TSV for subsequent games without changing source code.

## Strength comparison

Long-term summaries segregate model versions by Stockfish binary ID, node budget, skill setting and Joshua search depth/quiescence. They only compare color-paired results from identical preset openings. When at least eight *distinct* openings appear in both versions, a two-sided sign test may label an exploratory trend. Such tests assume more independence than similar chess openings guarantee; therefore every result remains *provisional*. Repeated deterministic games do not generate new independent samples. For a serious study, freeze both models, use independent opening books, compare matched colors and assess uncertainty under multiple opponent settings. Improvements from a changed evaluation graph may be overwhelmed by tactical horizon errors in the host search.

## Limits of evidence

- The real paceval library supplied by the user enabled actual tests of extended nonlinear graph execution and full catalog accounting.
- A real Stockfish opponent executable was not present in this environment. UCI protocol orchestration was validated with an explicitly simulated opponent while Joshua executed authentic paceval mathematics.
- User-provided V9 logs documented two Stockfish defeats but do not establish the effects of V10.
- V10 acceptance simulations test **software policy**, not proven general chess improvement.
- The 25 MB log archive quota excludes temporary active-game and ZIP creation overhead, and external files unrelated to the log manager.
