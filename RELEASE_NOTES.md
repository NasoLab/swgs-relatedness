# v0.1.0 — Development

Status: local release-preparation commit; no tag or public release created.
End-to-end validation remains pending. This is not a stable or clinically
validated release, and cross-host portability has not been established.

Included: manifest validation, fail-fast Nextflow orchestration, preserved
QDNAseq/CGHcall source, ordered metric adapters, precise sample/pair aggregation,
version/dependency metadata, reference checksums, container recipe candidates,
synthetic tests and public configuration templates. Temporary, work and output
storage are independently configurable.

Packaging changes: historical research files and all development ancestors are
excluded. The legacy PCC/LLR runner is now an explicit `pcc_llr_runner` parameter
and CLI `--runner` input, checked against its existing frozen SHA256. This avoids
redistributing unresolved inherited source. CGHcall's project-owned preparation
script is relocated to `bin/prepare_cghcall_cohort.R` with its contents unchanged.
No metric function, model, matching rule, seed, numerical tolerance or scientific
parameter is changed. Existing scientific guards remain in force.

Prior cached gates: PCC 66/66 (max absolute difference 4.996003610813204e-16),
LLR 62/62 (4.973799150320701e-14), fraction_shared 38/38 exact historical counts
and supplied fraction precision. The LLR loop remains seeded once at 1337 with
original pair order and sequential RNG consumption. These gates came from the
originating development/runtime checkpoint; lightweight snapshot checks are
recorded separately in [snapshot test evidence](verification/release_tests.json).
The preceding snapshot preparation included a fresh one-pair cached Nextflow run through this snapshot matched every metric
string, breakpoint count, rational, status and orientation exactly against the
previously validated cached output. It did not process FASTQs or rerun all
66/62/38 historical cases.

Known limits: own-project licensing is unresolved; QDNAseq.dev/helper/runner
permissions and source receipts remain incomplete; frozen PFREQ/PE150 assets
are external; new source-restoration Dockerfiles are unbuilt; no public raw or
CNV fixture is bundled. A retained Picard image's uutils date is incompatible
with Nextflow 24.10 resource tracing. The isolated execution example disables
optional trace/report/timeline monitoring without replacing software.

The original running pilot is independent of this worktree and is not modified,
restarted or used as a source of publishable patient-level test data. The independent release root and audited clean descendants exclude research
ancestry; it does not remediate old remote
branches, tags, caches or previously exposed files.

Final preparation adds the requested Huntsman group acknowledgement and preserves
all existing author/external-component notices. MIT is the intended license for
authorized project-owned code; its proposed text is not activated while the
four-file legacy grant remains unresolved. No package, scientific implementation,
reference or image is relicensed. Documentation distinguishes included-code
permission gates from external execution requirements and reproducibility limits.

The final documentation commit descends only from the audited clean root. The
release audit checks each reachable commit and its complete allowlist/checksums;
its independent history does not incorporate research commits. The recommended
destination is a new empty non-fork repository under the intended account, with
no publication action performed. Scientific R, workflow modules, scoring adapters,
parameters, models and reference manifests are unchanged from the clean root.

Final lightweight verification: 46 tests discovered, 45 passed and one optional
historical test skipped; all five Nextflow stub and eight release-audit guard
tests passed. The guards reject unknown roots, merged ancestry, changed blobs,
secret markers and a forbidden artifact present only in an older snapshot.
Twenty-four scientific/workflow/reference-manifest files, including all ten R
files, remain byte-identical to the clean root. Full historical numerical gates
were not rerun during these documentation/licensing changes. Relative links and
shell examples passed validation; external link results are recorded separately.
