# Implementation plan: knowledge-graph integration and expert reference expansion

**Status:** Historical plan, implemented for the current 12-target release. The graph is read-only source context, not scoring thresholds; see [CURRENT_SYSTEM_STATUS.md](docs/CURRENT_SYSTEM_STATUS.md).
**Goal:** Make the curated `knowledge-graph/` directory the read-only source of selectable Baybáyin targets, then expand the developer reference workflow from the `ba`/`ka` pilot to expert-approved templates for the 12 selected targets.
**Method:** Test-driven development. For every step, write a failing test first, make the smallest implementation that passes it, then run the relevant suite.

## 1. Starting point

The application already has a Next.js capture interface, a FastAPI structural sample checker, and a developer-only local reference library. The reference library currently limits records and specifications to `ba` and `ka`. It distinguishes `candidate` recordings from `approved` recordings and prevents approval without an approved character specification.

The root [knowledge graph](../knowledge-graph/README.md) now provides source-traceable character, kudlit, orthography, and Grid-Baybáyin facts from Lopez (2025). It contains 24 base graphemes, six optional extension symbols, and five phonetic extensions.

The graph does **not** provide learner pass/fail thresholds, normalized stroke paths, or approved handwriting variations. Those remain dependent on expert-reviewed reference templates.

## 2. Scope

This phase delivers:

1. A FastAPI read-only knowledge-graph loader and API.
2. Validation that prevents malformed, incomplete, or inconsistent graph data from being served.
3. A Next.js target selector driven by the graph rather than manually typed labels.
4. Expansion of the developer reference library from its hard-coded `ba`/`ka` pilot to graph-defined core targets.
5. A reference-readiness view showing whether each target is unavailable, awaiting a candidate, awaiting expert approval, or ready for later scoring.
6. Documentation for the expert recording and approval handoff.

This phase does not deliver learner correctness scoring, automatic image recognition, authentication, a database, public uploads, or approval of any reference recording without a qualified reviewer.

## 3. Architecture decisions

### Graph ownership and loading

- Keep `knowledge-graph/` at the repository root as the curated, version-controlled source. Do not copy its JSON into the frontend or developer data directory.
- FastAPI loads the graph from disk at startup and exposes a deliberate read-only API. A restart is required after a graph edit during normal development.
- The backend validates all graph JSON before it becomes available. If a required file is missing, contains invalid JSON, has duplicate IDs, or has broken references, startup must fail with a useful developer error.
- The browser receives only the fields needed for selection and explanation: target ID, label/romanization, class, phoneme where applicable, availability, and source references. It must never receive private reviewer notes or local reference recordings through the graph API.

### Target groups and release order

- **Release 1:** A, E, I, O, U, ba, be, bi, bo, bu, b, and b_. These are the first targets eligible for expert template collection.
- **Release 2:** six optional extension symbols, after the team explicitly chooses their research need and obtains templates.
- **Release 3:** five phonetic extensions, after the team confirms their inclusion criteria and obtains templates.
- Keep `proposed_not_accepted` rules excluded from all target-selection and validation paths.

### Readiness model

Compute readiness from the graph and approved-reference manifest; do not duplicate it as editable frontend state.

| State | Meaning | Learner scoring |
|---|---|---|
| `not_in_current_release` | Extension or otherwise not selected for the current collection release | Disabled |
| `awaiting_candidate` | Core target has no saved candidate recording | Disabled |
| `awaiting_expert_approval` | Candidate exists but no approved reference/specification pair exists | Disabled |
| `reference_ready` | An approved specification and at least one approved reference record are linked to the target | Still disabled in this phase; eligible for a later scoring implementation |

A target becoming `reference_ready` means evidence exists. It does not mean the app is already able to score a drawing.

## 4. API contract

Add the following read-only endpoints under the existing local API root:

- `GET /api/knowledge-graph/catalog` returns the current release’s target catalog, source identifier, and graph version.
- `GET /api/knowledge-graph/targets/{targetId}` returns one target’s semantic data, related diacritic/rule references when applicable, source references, and computed readiness.
- `GET /api/knowledge-graph/readiness` returns every current-release target and its derived readiness state.

Keep existing sample-check and reference-library endpoints compatible. Do not expose an API that edits the source graph. Graph changes remain reviewed repository changes.

For the library, replace the `Literal['ba', 'ka']` restriction with a backend check that the requested target is a current-release graph target. Existing `ba` and `ka` records and specifications must remain valid.

## 5. TDD work sequence

### Step 1 — Define the loader contract

1. Add backend test fixtures containing a minimal valid graph, malformed JSON, duplicate grapheme IDs, missing required fields, unknown edge endpoints, and a source reference with an invalid format.
2. Write failing tests for a loader that returns a typed catalog and preserves source references.
3. Implement a small `knowledge_graph` module that reads the root graph files and produces typed internal records.
4. Write tests that the full committed graph loads successfully and has 12 current-release targets, while retaining the 24 base graphemes, six optional extensions, and five phonetic extensions in the source inventory.

**Done when:** Invalid graph data cannot be served, and the committed graph is loaded from one controlled backend boundary.

### Step 2 — Serve a read-only catalog

1. Write FastAPI endpoint tests for the catalog, single target, unknown target, and readiness endpoints.
2. Implement the endpoints with stable response shapes and no mutation routes.
3. Add tests that source references are included and that private local-library data is absent from catalog responses.
4. Document the endpoint shapes in the app README.

**Done when:** A local client can retrieve source-traceable target information without direct filesystem access to the graph.

### Step 3 — Derive reference readiness

1. Write repository/API tests for each readiness state, including: no record; candidate only; rejected record; approved record with missing specification; matching approved specification and record; and an extension outside the current release.
2. Implement one backend readiness service that combines graph target eligibility with the existing reference manifest/specifications.
3. Test that target readiness changes only as a consequence of saved review state, not browser input.
4. Test that a `reference_ready` target remains explicitly marked as `scoringAvailable: false`.

**Done when:** The team can see exactly what evidence is missing for every core target, without confusing evidence readiness with learner validation.

### Step 4 — Replace free-text target entry in the capture flow

1. Write frontend tests for catalog loading, loading and unavailable-backend states, target selection, disabled unavailable targets, and preservation of a drawing in progress when the catalog request fails.
2. Implement a target picker that shows the selected target’s label, phoneme, class, and source-backed status. Keep the target ID in exported sample metadata.
3. Do not show a correctness score or an “approved handwriting” claim anywhere in the capture flow.
4. Keep import/replay behavior compatible with existing version 1 exports. Define a version-2 export only if the new target ID cannot be added compatibly; write migration/compatibility tests before changing the schema.

**Done when:** Developers select an authoritative graph target rather than typing an arbitrary label, while older saved samples can still be reviewed.

### Step 5 — Expand the developer reference library safely

1. Write backend tests replacing the pilot target restriction with current-release graph membership. Test that unknown IDs, optional extensions, phonetic extensions, and proposed rules are rejected or accepted according to release policy.
2. Write frontend tests for filtering records by target and for presenting source references and readiness clearly.
3. Update the developer-library target field to use the same catalog. A record retains the selected target ID, graph/source version, and source page references at the time of import.
4. Preserve the existing candidate, approved, rejected, and superseded transitions. Approval still requires a matching, expert-approved specification.

**Done when:** The library can collect expert references for each core target without relaxing its evidence and approval safeguards.

### Step 6 — Add expert-template capture fields

1. Write tests for a versioned template attachment that requires: target ID, approved reviewer code, decision date, source type, ordered strokes, normalized points, start/end regions, and permitted scale/rotation ranges.
2. Implement storage for this metadata alongside an approved reference record, not inside the root knowledge graph.
3. Reject incomplete templates and templates that refer to a different target or an unapproved specification.
4. Document the distinction between a captured recording, a candidate, an approved reference, and a reusable stroke template.

**Done when:** The system can preserve the expert’s concrete stroke template without yet calculating a similarity score.

### Step 7 — Verify and document

1. Run backend tests, frontend tests, and the Next.js production build.
2. In a browser, select `ba`, capture/export/import it, save it as a candidate, add an approved `ba` specification, approve the reference, and verify that readiness changes to `reference_ready` while scoring remains unavailable.
3. Check invalid graph data, unknown target IDs, a backend outage, malformed sample JSON, duplicate reference imports, and attempted approval without a specification. Confirm existing work remains intact.
4. Update `app/README.md` with startup instructions, graph API use, developer workflow, local-data handling, and the current limitation that this is not learner validation.

**Done when:** The path from curated source data to an auditable expert template is verified end to end.

## 6. Acceptance criteria

- FastAPI loads and validates the root knowledge graph and serves it read-only.
- The committed graph’s 35 source-defined characters are represented accurately, while only the 24 base graphemes are eligible in the first collection release.
- Developers select graph IDs, not arbitrary typed labels, for new recordings.
- Existing `ba` and `ka` data continues to work.
- Readiness is derived from the graph plus approved local evidence and cannot be changed by the browser alone.
- No candidate recording is treated as ground truth, and no `reference_ready` target is presented as scoreable until the later scoring phase.
- All new behavior is covered by tests written before implementation, and the browser-to-API workflow passes end to end.

## 7. Dependencies and remaining blocker

Development through Steps 1–5 can begin now. Step 6 can be scaffolded and tested with synthetic data now, but real templates require a qualified Baybayin expert’s recording and approval.

The next phase after this plan is stroke-comparison research and implementation. It begins only after the team has at least one approved specification and one approved template for a target, preferably `ba` and `ka` first.
