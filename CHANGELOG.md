# Changelog

## 1.6.3 — Unreleased

### Added

- Add an optional per-experiment duration reminder and read-only duration advice to the existing session resource tool, separate from the standing automatic-approval ceiling.
- Read first-step timing receipts from the existing experiment owner, preserving completed training segments across resume while excluding engineering preparation.
- Refresh observed/effective CPU, RAM and GPU capacity in the same session table and report hardware inventory changes without changing the user's authorization.

### Fixed

- Serialize final process dispatch with workflow review/stop updates; keep structured deferrals pending without consuming retries, and resume the same frozen attempt after review.
- Preserve trainer exit codes through tee and require attempt-bound terminal evidence; missing screen sessions and partial outputs cannot complete a live job.
- Consume first-step timing receipts in the original execution observer, deduplicate runtime notices, and continue observation without treating unanswered notices as consent.
- Wait for cooperative checkpoint saves without an implicit forced-kill deadline; require a separate explicit force grant and verify save receipts. Protect Windows descendant reconciliation before releasing leases.
- Replace driver-memory idle heuristics with observed GPU occupants; align pilot, queue, analysis completion, optional notification and deployment guidance with their shared ownership and authorization boundaries.
- Check duration per independent experiment, separately from a comparison's reflection count or a serial queue's total. Keep concurrent resource peaks subject to the existing admission checks.
- Separate optional duration reminders from the session's existing automatic-approval ceiling. Within that authorization, send a nonblocking continue/stop notice and keep monitoring while unanswered; do not infer a new hard cutoff, record silence as a new approval or block the Goal for that notice.
- Add read-only duration advice for the existing execution owner, preserving actual user replies, original experiment timing, hard limits and checkpoint/stop ownership. Existing tables retain their selected ceilings.
- Keep routine replanning, healthy training waits and optional reminders with their current owners. Scope unresolved dependencies to affected steps and continue useful authorized work in Goal or allowed read-only Plan work.
- Remove conflicting per-heartbeat iteration counting from both research pipelines. Record completed investigations once, and interpret the legacy `pivot=human` signal as a request for attention rather than mandatory approval or a Goal stop.
- Scope analysis completion, search-batch timeouts, routing failures and actual review gates to their affected work. Resolve routine plan uncertainty within existing authorization instead of treating every ambiguous gate as a required human stop.
- Clarify requested read-only observation in Plan without claiming that Plan itself schedules another turn; retain the supported host continuation boundary.
- Distinguish physically impossible requests (`REPLAN_REQUIRED`) from temporarily occupied resources. Retain usable GPU telemetry when another device fails, and replace unsupported blanket launch gates with measured phase requirements.
- Let resource-bound queue jobs reach fresh admission without a separate near-idle GPU threshold; retain the queue's own device/concurrency constraints and the launcher's admitted UUIDs.
- Require an actual user confirmation for process interruption, or a specifically preauthorized automatic condition. Review stops hold new dispatch; unconfirmed timeouts and control errors produce notices while observation continues. Do not kill unknown screen occupants or retry a still-live process from partial output or an OOM log.

### Changed

- Verify native Goal state before relying on automatic continuation after a resumed task. Starting an authorized job does not itself reactivate a previously blocked Goal, and a background metrics observer does not replace the research decision loop. Use a supported host resume interface when available; otherwise report the missing capability and continue permitted work without pretending the Goal is active.

## 1.6.2 — 2026-10-25

### Added

- Add one user-selected resource table per session, shared through the existing research principles. First use initializes the table and offers maximum available, exclusive GPUs or custom limits; continuation and other skills reuse the selection.
- Check the table and fresh execution-host state before arranging experiments and again before launching. Cover GPU allowlists, per-device and total VRAM, sharing, CPU, host RAM, dataset growth, weights, checkpoint save peaks and disk headroom.
- Bind frozen executions and their governed queue to the same resource admission check, retaining a per-execution check receipt without copying the policy table.

### Fixed

- Treat in-scope resource allocations within the selected ceilings as standing authorization. The maximum-available profile automatically approves individual jobs up to 12 hours, including a 90-minute budget, without inventing a total Goal time window.
- Keep unlaunched jobs pending when capacity, first selection, estimates or a policy exception are unresolved; do not spend training retries or record these waits as failed experiments.
- Combine additional storage peaks on the same filesystem, check each GPU separately, and retain unknown telemetry as unknown capacity. Prevent GPU index/UUID aliases from allocating the same device twice.
- Preserve unrelated user restrictions when changing one custom ceiling, recheck concurrent policy revisions, and pass only admitted GPU UUIDs to the launched child.
- Initialize the session resource policy during ordinary writable experiment planning; reserve read-only behavior for actual host Plan mode or read-only restrictions, without initializing an experiment runtime.
- Separate per-job estimates from the user's standing session choice, and keep maximum available as the default first-use option.
- Rebase native Windows and portable retry output paths in both frozen snapshots and queue expectations without changing parent evidence or fixed inputs.
- Observe Windows process exit with non-signaling handles before releasing a queue lease; keep live and unknown processes protected.

### Changed

- Keep resource policy with the session table and planning, execution, accounting, reflection and scientific review with their existing owners. Existing finite budgets and stop requests remain in force; no new skill or scheduler is added.
- Include resource-table and governed-queue tests in both Windows shell CI gates. The corrected runtime passed full Linux/macOS CI and both native Windows shells. Separate actual Plan/Goal checks cover four-minute CPU monitoring and automatic Goal continuation; they do not establish GPU isolation or hour-long research behavior. See [1.6.2 validation](docs/VALIDATION_1_6_2.md).

## 1.6.1 — 2026-10-24

### Added

- Add progress-based reflection after N complete experimental blocks. A full comparison, including its planned methods, seeds and analysis, counts once; retries and preparation do not inflate the count.
- Support explicit null total wall/action caps for ongoing authorized research, while retaining declared resource ceilings, retry bounds and per-attempt timeouts.
- Add `inspect --read-only` to observe existing and due review without changing run state or the iteration ledger, for Plan monitoring and live observation.

### Fixed

- Block prepared execution at launch when reflection is pending or due, including a review that becomes due during environment verification. Preserve the prepared identity for launch after review.
- Keep healthy in-flight jobs running through ordinary reflection. Separate waiting for long training from completed zero-finding investigations and native Goal blocked/stalled status.
- Distinguish one-attempt cancellation, workflow STOP and host Goal pause. Preserve process ownership, actual exit verification and original accounting.
- Clarify observation-only Plan monitoring: report anomalies without launching, changing configurations, persisting research state or executing stop commands.
- Use native Windows shared/exclusive file locks so review writers can coexist with healthy training while exclusive migration stays blocked. Preserve nonblocking contention errors and release locks when an owner exits.
- Serialize Windows run-state transactions with the portable per-run lock instead of a no-op, preventing duplicate action claims and lost updates while independent runs can still proceed.

### Changed

- Keep status checks, ongoing monitoring, planning, execution and decision recording with their existing owners; add no new skill or scheduler.
- Add whole-comparison and monitoring regression coverage to both native Windows CI shell gates. Local tests do not establish native Goal continuation or native Windows/macOS acceptance; see [validation scope](docs/VALIDATION_1_6_1.md).

## 1.6.0 — 2026-10-21

### Added

- Add `problem-synthesis` to compare shared-cause hypotheses with keeping problems separate, using observations, counterevidence, joint predictions and discriminating checks.
- Add trajectory checkpoints at comparison blocks, tuning batches, large milestones and direction changes. Ordinary reviews need no invented second problem; fairness drift routes to the existing audit skill.
- Add gate-bound reflection records and an optional brake in the existing action controller, with revised-plan handoff and recovery commands. Short advice does not initialize runtime state.
- Add public synthetic trajectory fixtures and a three-wave CPU integration exercise using the existing study runner.
- Add opt-in review boundaries by settled action count or elapsed time in the existing controller. Boundaries request an evidence-based judgment and preserve the original clock, rather than selecting a verdict.
- Connect bound local execution to workflow STOP and snapshot/process-bound cancellation requests, with actual termination receipts and owned POSIX process-group cleanup. Ordinary reflection leaves healthy training running.

### Fixed

- Retain the brake for deferred/blocked decisions and while a changed frame awaits a plan handoff. Unrelated or older reflections cannot clear a later checkpoint.
- Recover an interrupted ledger-to-coordination update without duplicate reflection entries. Keep reflection payloads separate from stale-progress counters.
- Preserve the active revised-plan identity across later ordinary reflections; changed plans continue to require evidence reconciliation.
- Use the existing portable file-lock primitive for iteration-ledger writes and include reflection checks in both native Windows CI shell gates.
- Reconcile aged review state without deleting its identity, pending work or original limits. Preserve the mainline legacy Codex backend defaults, the documented MCP `prompt` argument and the external-timer boundary.
- Bound local execution by the smallest explicit timeout, experiment attempt limit and original remaining workflow dispatch time. Preserve cooperative zero-exit cancellations as stopped, exclude them from successful aggregation, and support explicit cancellation in independent termination recovery receipts.

### Changed

- Keep routing, decisions, planning, execution, queues and scientific review with their existing owners. Link shared checkpoint guidance from pipeline, planning, bridging, tuning and handoff skills without duplicating a scheduler or research database.
- Extend the Codex inventory to 89 and mainline inventory to 88. Use contract schema 4 for the new entrypoint while preserving schema 2/3 loading and frozen retained baselines.
- Share review-cycle and recovery instructions across the three review-loop entrypoints while retaining backend adapters and stricter gates. Forward the deprecated poster entrypoint's unchanged arguments to `paper-poster-html` and clarify adjacent skills' output ownership and artifact reuse.

See [1.6.0 local validation](docs/VALIDATION_1_6_0.md) for the latest 1,349 passing tests, preserved failed attempts and the earlier real one-hour CUDA engineering witness. A supplemental bounded observation used real native-model reviews to replan from paired results, stop an active owned CUDA job and verify full-state recovery. These constructed, guided local checks do not establish a product-default unified emergency watchdog or model-driven long-duration scientific discovery.

## 1.5.0 — 2026-10-19

### Added

- Add optional bounded continuation over existing run state: reserve resources before dispatch, reconcile interrupted work, deduplicate repeated claims and limit retries without changing scientific review gates.
- Preserve an original authorized task clock when attaching late, expose remaining dispatch time and reserve closeout inside the same wall budget. Add read-only handoff capture/check commands for the run and selected present or absent source files.
- Settle a pre-bound registered execution from verified terminal evidence, including after interruption, without relaunching or advancing review gates; keep scientific result-file formats independent from accounting records.
- Import explicitly selected Codex JSONL exports into compact, source-bound activity records. Preserve failures and unknown completion, support idempotent import and keep raw commands, prompts, outputs and credentials out of normalized events.
- Retrieve relevant decisions from existing Markdown and JSONL records, with source identities, supersession, evidence freshness and revisit conditions. Retrieval remains read-only and lexical matches remain candidates for inspection.
- Compare baseline and candidate behavior using frozen inputs, model settings, budgets, repeated tasks and held-out coverage. Report missing attempts and regressions; comparison results do not authorize toolkit changes.
- Add three actual synthetic CPU studies covering positive findings, negative findings and an evidence-driven pivot, plus six public native Codex development cases. Document optional Plan and Goal coordination.

### Fixed

- Allow CPU-only investigations when the GPU allowance is zero. Reject corrupted accounting, retain actual resource overruns and preserve unresolved reservations after a stop.
- Separate skill-path references from verified skill invocation or compliance, and completed turns from complete research workflows. Reject changed or truncated imported history.
- Validate and publish each event import as one atomic batch, avoiding repeated whole-source reads and log rewrites. Cooperating importers retain distinct observations once; failed replacement preserves the previous log.
- Correct the Codex self-optimization instructions to use the existing native behavior harness and stage proposed patches for the established landing review. Preserve human selection, backups, provenance and provisional review status.
- Bind candidate comparisons to actual request and fixture hashes, distinct run receipts and explicit assessments. Keep timeouts and failed executions in the planned denominator.
- Cover the bounded research modules and original run state in both native Windows shell gates for development and release CI.
- Retry temporary native Windows sharing violations when a monitoring reader blocks old-checkpoint deletion. Bound the wait, retain the deletion journal and latest recovery points, and propagate persistent or unrelated errors.

### Changed

- Guide sustained investigations toward the next decision-changing uncertainty, competing predictions, prior negative results and explicit stopping conditions. Keep small numerical questions and advice within their requested scope.
- Connect clearly authorized sustained tasks to their existing run's budget control before costly preparation. Reuse verified receipts and reviewed small-wave ranges, save incomplete review findings progressively and refresh recovery facts from current sources. Public local repair cases retain all incomplete and failed attempts.
- Shorten continuation guidance and entrypoint hooks, reuse existing runners and save useful findings early. Keep domain-specific protocols out of shared instructions and distinguish import readiness from formal environment freezing.
- Document scientific interfaces beside the code with meaningful parameters, shapes and returns; check changed routines before their first consumer or handoff and reuse that contract during implementation, ablations and code fixes. Checkpoint completed waves, bind review claims to observable receipts and assess time/tool limits through host-enforced records. Distinguish initial setup from unmeasured reuse performance.
- Size required reviews to the pending decision and remaining budget, reuse valid scoped receipts, and finish once required coverage is met. When splitting a review, retain cross-interface checks and uncovered requirements as pending; partial or timed-out prose cannot close a gate.
- Retain all 88 Codex entrypoints, 83 original workflow records and 450 protected-resource baselines; register targeted adaptations separately.

See [1.5.0 validation](docs/VALIDATION_1_5_0.md) for actual local use, source-specific checks, preserved failures and limitations. These observations do not establish general superiority over 1.4.0, unattended research over hours or days, or complete recursive self-improvement. Publication and local installation are recorded separately from implementation validation.

## 1.4.0 — 2026-10-17

### Added

- Add `scientific-brainstorming` and `research-manager`, bringing the inventory to 88 Codex and 87 mainline skills. Frame testable questions and preserve evidence-linked decisions within existing project records.
- Add offline literature identity/source/reading records and figure input/source/output identity receipts alongside existing fetchers and renderers.
- Add versioned framing for new idea-discovery runs, preserving old run contracts and scientific review gates.
- Add proactive case studies to substantive result analysis, with task-specific diagnosis for classification, regression, image generation and video understanding. Reuse existing sample outputs and record selection, paired evidence, regressions and missing coverage.

### Fixed

- Keep result analysis proportionate to the question: narrow numerical requests
  remain concise, substantive reports lead with the observed comparison, and
  repeated case findings are consolidated. Conditional reference loading reduces
  unnecessary routing work while preserving sample-level evidence, regressions,
  missing coverage and review gates. Correct runtime-relative links, pin loaded
  skill variants, and report noncanonical reads separately. Bound completion work
  after one verified report and record overload/reconnect failures without
  treating incomplete execution as a pass.
- Distinguish assessment of supplied records from formal execution certification. Local audits report supported findings, demonstrated defects and unknowns without forcing a full audit; required independent review still blocks acceptance when unavailable.
- Preserve supplied resource quantities in experiment plans and deliver a compact blocked-run tracker when the requested storage or execution plan is infeasible.
- Judge normalization against metric definitions, comparison protocols and claims. Legitimate precision/F1/IoU denominators and disclosed display transforms are not failures by themselves; display rescaling does not establish absolute accuracy, calibration or relative gains.
- Include the literature, research-decision, workflow-version and figure-evidence modules in both native Windows release gates. Add a regression that detects gaps between ordinary CI and publication coverage.
- Keep primary and material negative results visible through paper improvement; mark secondary reframing exploratory. Give generated Claude reviewers actual read-only artifact access.
- Complete mechanical framing against a nonempty fixed artifact so sessions resume at the next phase, without granting scientific acceptance.
- Reject figure path aliases and invalid geometry; preserve interrupted decision history, Unicode output and stable literature export ordering.
- Expose common principles from mainline and reviewer overlays; pin reachable installed variants and record noncanonical reads and infrastructure errors separately.
- Recognize the recorded historical namespace migration in optional original-baseline comparisons while continuing to reject unregistered content changes.

### Changed

- Separate observed ranking, effect size, uncertainty and practical value. Preserve gains and regressions, verify populations and denominators, and recheck challenges without automatic agreement or criticism.
- Judge reviews by evidence and issue closure; stopped, unavailable and incomplete reviews grant no acceptance. Keep depth proportional to the requested decision.
- Choose relevant available literature sources with `sources: auto`; retain legacy explicit `all` and user source constraints. Distinguish metadata, abstracts and inspected sections, including contrary evidence and identity conflicts.
- Plan compact sample-level evidence before analysis, reuse its selection record in figure panels and paper outlines, and audit qualitative claims against the actual pool. Narrow numerical requests remain narrow; missing outputs do not trigger automatic inference.

See `docs/VALIDATION_1_4_0.md` for source-specific results, preserved failed attempts, human acceptance of J05, runtime deviations and review limitations. The implementation passed 1,150 local tests and all four native CI jobs; the final v1.4.0 tag also passed both full suites and both Windows gates before publication. Public archives and clean-source installation were verified separately. Optional external adapters are not advertised as validated integrations.

## 1.3.0 — 2026-10-14

### Added

- Share comparative-experiment guidance across eight existing skills: controlled contributions, equal resource budgets and tuned-system performance, with data/split integrity, baseline quality, search cost, validation selection, seed coverage and uncertainty.
- Add a file-backed comparison evidence index and validator, binding every declared run and recorded attempt to configurations, raw results or failure logs and the comparison summary.
- Add opt-in project/global research routing with scoped managed instructions, override handling, preview/check/removal, idempotent updates and preservation of unrelated content.

### Fixed

- Require complete bound evidence before comparison weight consolidation; reject omitted runs/retries, changed references, mismatched winners and evidence inside disposable checkpoint artifacts.
- Recheck the archived winner and bound evidence before interrupted cleanup resumes. Keep legacy comparison receipts readable and require evidence binding before further deletion; preserve dependency pins.
- Preserve standalone checkpoint trainers by loading the evidence helper only for comparison archival. Represent unstarted slots with cancellation records and allow permanently stopped, evaluated winners with validated weights.
- Verify new supporting resources are present in release source packages and include portable comparison/routing tests in both Windows shell gates.
- Flush checkpoint files using a non-truncating writable handle on Windows. Preserve previous recovery points when a file flush fails, and run the checkpoint-retention suite in both native Windows shell gates.
- Retry temporary native Windows sharing/access errors during checkpoint-manifest reads and atomic replacement for at most one second per operation; handle CRT read errors, preserve the old manifest and propagate persistent or unrelated errors and corruption.
- Keep the final exception and test identity inside bounded public CI annotations, with UTF-8-safe excerpts and actual JUnit counts.

### Corrected

- Qualify comparison fairness by the question rather than requiring universally identical training recipes. Treat the three-seed default as a starting estimate and expose failures, missing slots and protocol deviations.
- Qualify relative gains for zero or unsuitable metric scales, distinguish variability from effect uncertainty, and require genuine pairing units rather than equal seed integers.
- Separate file coverage/integrity from scientific review and record current validation independently of historical release results.

Retain 86 Codex entrypoints and all 83 original workflow bodies. The optional checkpoint helper deliberately adds the comparison evidence gate; single-run completion retains its existing behaviour. See RELEASE_NOTES.md and docs/VALIDATION_1_3_0.md for capabilities, upgrade instructions and actual verification scope.

## 1.2.0 — 2026-10-13

Promote the validated 1.1.0-beta.2 runtime to stable. Changes below are compared with the previous stable release, 1.0.0.

### Added

- Add project-governance and environment-maintenance, bringing the Codex inventory to 86 entrypoints. Track fixed project/report references, independent environment candidates, queued bindings, leases and reproduction pins.
- Freeze source/config/data/evaluator/environment/launch inputs and preserve distinct failed, retry and restored execution identities with predeclared aggregation.
- Add source/interface/documentation freshness checks, a deployment filesystem doctor and native Windows project-to-report acceptance.

### Fixed

- Count method coverage only from successful consumers-layer receipts. Bind inspection, validation and launch to one validated interpreter across cwd/PATH changes, preserving the virtual environment.
- Separate import logs from the machine fingerprint; preserve Unicode CLI/execution output and diagnostics. Handle built-in/extension modules and record namespace locations and interpreter prefixes.
- Decode Python source according to encoding declarations/BOM while hashing original bytes. Reject Junction traversal, reserved names, ambiguous Windows references and case-colliding consumer bindings.

### Corrected

- Compare canonical directory identities in installer assertions, including macOS aliases, and honor Windows executable path case without dereferencing venv entrypoints.
- Preserve actual Unicode failure annotations and original failed receipts. Correct stable installation links, release labels and the provenance of validation results.

All 83 original workflow bodies, historical frozen records, scientific review gates and checkpoint helper bytes are preserved. Stable publication requires Linux/macOS full suites and both native Windows PowerShell gates, and provides checksums plus a fixed-commit manifest. See RELEASE_NOTES.md for bilingual capabilities, benefits and installation guidance.

## 1.1.0-beta.2 — 2026-10-13

- Count required consumer coverage only from successful consumers-layer receipts; preserve rejected candidates and prior frozen bindings.
- Pin validated interpreter entries across working-directory and PATH changes while preserving virtual-environment prefixes and dependencies. Verify historical fingerprint records without rewriting them.
- Separate import logs from a framed machine fingerprint; expose captured stdout/stderr and exit status with inspect --diagnostics. Fingerprint version 2 records module kinds, origins, namespace locations and interpreter prefixes.
- Parse Python source according to its encoding cookie or BOM while continuing to hash original source bytes.
- Reject symlink/Junction traversal, reserved file components and ambiguous Windows references in governance state and evidence. Protect consumer IDs from case collisions on case-insensitive filesystems; keep installer-managed skill links supported.
- Add real venv, noisy-import, namespace-drift, source-encoding and directory-alias regressions, plus native NTFS Junction and case-collision acceptance in both Windows PowerShell CI gates. Preserve all 83 original workflow bodies and checkpoint helper bytes.

## 1.1.0-beta.1 — 2026-10-13

- Add project-governance and environment-maintenance entrypoints, with versioned identities, fixed evidence references, guarded .ei state resolution and recoverable local publication/migration.
- Add independent environment candidates, real validation receipts, immutable recipe inputs, consumer bindings, leases and reproduction pins; preserve queued/running environment revisions.
- Add frozen source/config execution snapshots, distinct failed/retry/resume identities, predeclared aggregation and a source/doc freshness map. Retain existing workflow/review/checkpoint controls.
- Add a deployment filesystem doctor, native install/rollback receipts, real GPU restoration and isolated dependency-conflict pilots, and focused natural-request/Windows acceptance.
- Handle canonical repository aliases in macOS installation checks and built-in module origins in Windows environment acceptance; expose actual failed validation receipts in CI.
- Pin recorded model/provider/effort settings for every behavior-evaluation session so changes to user defaults cannot silently mix evaluation configurations.
- Replace active .aris defaults through reviewed namespace adaptations. Legacy state requires explicit read or an approved, journaled migration; no live project is automatically migrated.


## 1.0.0 — 2026-10-12

- Publish the first stable Codex research toolkit with 84 skill entrypoints spanning literature, research design, theory, experiments, evidence review, papers, presentations, proposals, and patents.
- Include research-guide for project continuation, natural-request routing, and coordination within the user's authorized scope.
- Integrate storage budgets, bounded training recovery, validated weight exports, and validation-winner archiving while preserving results and planned model dependencies.
- Preserve all 83 existing workflow bodies and the frozen runtime/reference contract; expose focused steps and complete pipelines through the same plugin.
- Replace the incremental beta release description with bilingual capability, benefit, installation, and validation guidance.
- Support stable and prerelease publication through the Linux/macOS regression gate, with version-specific source assets, checksums, and a committed-source manifest.

## 1.0.0-beta.5 — candidate

- Bound experiment artifacts with a storage peak budget, latest/fallback recovery points, validation-selected best models, and explicit dependency protection.
- Add a local checkpoint publication/retention helper with caller-supplied writer and loader validation, atomic manifests, cooperative locking, hash-based inspection, and preview-first cleanup.
- Release unused recovery states after completed or explicitly ended training and verified weight exports; consolidate finished comparison groups to their validation-selected winner while preserving planned dependencies and all results.
- Connect storage planning, actual trainer configuration, launch checks, batch budgets, monitoring, and persistent backend outputs through 15 scoped Codex extension hooks.
- Separate ordinary result interpretation and follow-up planning from formal claim adjudication, while retaining required review gates.
- Write shared experiment settings once and reserve time for final verification and delivery of planning artifacts.
- Add independent storage/recovery behavior cases and deterministic capacity, interruption, ownership, and CPU training-continuation tests; preserve the original 24-case evaluation manifest and all 83 retained workflow bodies.

## 1.0.0-beta.4 — candidate

- Add research-guide for project continuation and evidence-based next-step coordination; keep all 83 existing entrypoints.
- Refine each Codex description for natural request selection, reducing the total from 23,910 to 13,229 characters across 84 entries.
- Reuse shared guidance within a session and connect authorized continuation to evidence, resource limits, review states, and stopping conditions.
- Add an optional research-project AGENTS.md snippet and bilingual usage examples.
- Protect retained workflow bodies, non-description metadata, and runtime files with a frozen beta.3 contract and destructive-change regression checks.
- Add 24 bilingual offline behavior cases, isolated Codex execution, and trace-based assessment; validation status is recorded in BETA_VALIDATION.md.

## 1.0.0-beta.3 — 2026-10-11

- Remove upstream promotional material, community showcases, redundant client guides, and unused generated tutorials.
- Consolidate public documentation around installation, skill capabilities, workflow controls, recovery, compatibility, and maintenance.
- Point all 83 catalog entries at the installed Codex implementations.
- Preserve skill bodies, runtime helpers, reviewer resources, and required tutorial exemplars.
- Add an explicit publication policy that rejects retired materials and detects missing workflow references.

## 1.0.0-beta.2 — 2026-10-11

- Introduce the toolkit through its research capabilities and practical usage examples.
- Replace both public READMEs with aligned installation, workflow, and contribution guidance.
- Use EvoInquiry as the documented checkout directory.
- Update public plugin descriptions to describe research tasks.
- Preserve the 83 research skill entrypoints and their workflow contracts.

## 1.0.0-beta.1 — 2026-10-11

First public beta of EvoInquiry, a Codex research-workflow edition of ARIS.

- Preserve 83 Codex skill entrypoints and their inherited workflow bodies.
- Add six shared research principles: Independent Judgment, Grounded Inquiry,
  Explanatory Simplicity, Discriminating Research, Honest Conclusions,
  and Reflective Progress.
- Apply relevant principles to nested research tasks and reviewer briefs.
- Correct Codex backend setup guidance for generic/MiniMax review examples
  and identify the image2 renderer as an experimental optional backend.
- Keep the retired paper-poster redirect for compatibility; use paper-poster-html.
- Document the full inventory and a proposed 45-core / 38-optional profile.
  This beta still installs all 83 entrypoints.
- Add portable installation docs and packaging/compatibility checks.

Validation and beta limits are documented in docs/BETA_VALIDATION.md.
External providers, broad discipline coverage, and all operating systems have
not been validated end to end.
