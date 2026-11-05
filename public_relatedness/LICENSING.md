# Project license and external redistribution scope — 2026-11-05

This inventory distinguishes bundled source from operator-supplied execution
assets. The project PCC/LLR runner, historical breakpoint preprocessing and Python
all-overlap core are bundled under project MIT. The recovered BreakClone matcher
is bundled with its upstream MIT notice. The inherited clonality helper,
installed packages and reference payloads remain external. No package archive,
compiled software or container image is included. The four retained Huntsman
pipeline files are identified below.
The project MIT license covers the included project code and retained internal
Huntsman research-pipeline components, as instructed by the maintainer. It does
not license external assets or the originating repository's research payloads.

| Component | Evidence at the relevant source/version | Required action and scope |
| --- | --- | --- |
| Project code / public adapters / retained internal Huntsman components | MIT applied in root LICENSE following the maintainer's project licensing instruction; original contributor attribution retained | Included in the project MIT scope; no individual-contributor permission or separate approval-reference gate |
| PCC/LLR runner | Richard Corbett's project cohort-reporting implementation, commits `cd42a6c/ac33f3c`; frozen source identity in scientific_sources.json | Bundled byte-for-byte under project MIT; automatically located |
| Historical preprocessing | Branden Lynch's internal Huntsman `test_relatedness_cohort_qc_pass.R`, revision `39a918d2a38a30cc78a90a51a314b7ef83a7813d` | Four validated expressions bundled under project MIT; automatically located; unrelated research driver excluded |
| Recovered breakpoint matching | `argymeg/breakclone`, revision `712eb202303119588ca10889ca92a721afd0c396`; exact-revision LICENSE confirms MIT, copyright 2022 The Authors | Exact source is now bundled with upstream copyright 2022 The Authors and full MIT notice; only the historical matching functions are evaluated |
| QDNAseq.dev 0.1 | Both installed DESCRIPTIONs literally say `What license is it under?`; no RemoteSha. Located source checkout at `8714202a7ca90124adba3ecb0d666cadc23f3d11`, with an indentation-only DESCRIPTION fix, has no license file | **Blocks distribution of that package/images, not this source-only snapshot:** obtain an explicit grant before bundling. Operators need lawful acquisition/use; a placeholder is not a grant |
| UTANOS 0.1.0.9000 | Installed DESCRIPTION: `MIT + file LICENSE`, RemoteSha `ae8edc6464ab7bac0939a886dd7f8beae7a7410b`; exact-revision DESCRIPTION and LICENSE confirm the declaration and 2024 utanos authors notice | Retain applicable MIT notices; check data and transitive dependencies separately before distributing packages/images |
| Inherited clonality helper | `tgac-vumc/CNA_clonality` revision `bbffb4a15a425ce032537cf95b2d68dbc1d87f15`; no root license located in that revision; helper provenance involves Clonality (installed package declares GPL-3) | Clarify authorship, derivative-code provenance and applicable license; do not infer permission for the helper from another package's license |
| Frozen PFREQ | Same CNA_clonality revision; frozen TCGA LUSC aggregate reference; no explicit dataset license/training receipt recovered | Obtain model redistribution permission and document TCGA accessions, processing, acknowledgment and applicable terms; do not retrain the model |
| PE150 annotation | Exact approved hash in reference manifest; mappability/blacklist/control-data provenance only partly recovered | Obtain annotation-owner permission and exact upstream input/accession/license records. Do not infer annotation rights from QDNAseq's software license |
| hg38 FASTA and BWA-MEM2 sidecars | NCBI accession/file identity and local hashes recorded; original download/index build receipts missing | Confirm upstream terms/attribution and index provenance before distributing payloads; user supplies files for now |
| R/Bioconductor and native dependencies | Exact declared licenses in the R and Conda inventories; QDNAseq declares GPL, CGHcall GPL, Clonality GPL-3 | Review applicable versions' license text, notices/source-distribution obligations and all image/transitive components; metadata alone is not a clearance |

Exact-revision [UTANOS notice](https://github.com/Huntsmanlab/utanos/blob/ae8edc6464ab7bac0939a886dd7f8beae7a7410b/LICENSE) and
[breakclone MIT license](https://github.com/argymeg/breakclone/blob/712eb202303119588ca10889ca92a721afd0c396/LICENSE)
were checked during snapshot preparation. The [QDNAseq.dev source repository](https://github.com/tgac-vumc/QDNAseq.dev)
and [CNA_clonality repository](https://github.com/tgac-vumc/CNA_clonality) are
provenance pointers, not implicit grants to redistribute their contents.

NCBI places no additional restrictions on molecular-data distribution itself,
but notes that submitters may retain rights that NCBI cannot transfer.
See [NCBI molecular-data policy](https://www.ncbi.nlm.nih.gov/home/about/policies/).
TCGA-derived resources require checking applicable source-data terms; GDC
policies distinguish open and controlled access and require acknowledgment and
protection of participant identities. See [GDC access policies](https://gdc.cancer.gov/access-data/data-access-policies).
Neither policy independently licenses this particular frozen PFREQ file or
this project's derived bin annotation. The exact 1000 Genomes control inputs
and their applicable terms remain unverified here.

## Retained internal Huntsman components

The maintainer confirms that these components were developed within the Huntsman
research group as part of its internal research pipeline. They are included in
the project MIT license. The following records source/contributor provenance,
not a designation of copyright ownership.

| Included file | Recorded project source and contributors | Release license |
| --- | --- | --- |
| `bin/runQDNAseq.R` | Huntsman `scripts/runQDNAseq.R`, introduced at `b9ed823`, relocated at `9578c5d`; Maxwell Douglas, Ding Ma, Sheila Nicholson | Project MIT |
| `modules/local/trimmomatic/main.nf` | Huntsman refactor `9578c5d`; Nicholson/Corbett, with Douglas/Ma/Lynch predecessor contributions | Project MIT |
| `modules/local/alignment/main.nf` | Huntsman refactor `9578c5d`; Nicholson/Corbett, with Ma/Lynch predecessor contributions | Project MIT |
| `modules/local/mark_duplicates/main.nf` | Huntsman refactor `9578c5d`; Nicholson/Corbett, with Douglas/Ma/Lynch predecessor contributions | Project MIT |

The standard MIT terms are applied without adding an unestablished copyright-holder
name. Original notices and contributor credits remain intact. No individual
permission or separate approval reference is requested or fabricated.

## Source release readiness

The selected destination is NasoLab/swgs-relatedness, a non-fork repository
containing the published v0.1.0 release. The history/content checks and applied
project license are source-readiness requirements. A passing readiness check is not an instruction
to push, create a tag or publish a GitHub release; preparation stops before those
actions as requested by the maintainer.

External QDNAseq.dev, the modified clonality helper, installed R/native packages,
PFREQ, PE150 and hg38/index resources remain operator-supplied under their own
terms. The project MIT grant does not change those terms. Do not redistribute
external assets or images containing them without satisfying their applicable
conditions. The exact-revision BreakClone MIT notice accompanies the bundled
matcher. UTANOS package/source/data are not bundled; its notice remains relevant
to any future package or image distribution.

Missing reference-generation receipts, unbuilt source-restoration images and
pending end-to-end/cross-host validation remain documented reproducibility limits.
No scientific replacement, dependency upgrade, reference regeneration or new
sequencing test dataset is introduced by the licensing update.

## Phase 5 source packaging

The runner is Richard Corbett's cohort-reporting implementation (cd42a6c/ac33f3c).
Internal preprocessing is Branden Lynch's test_relatedness_cohort_qc_pass.R at
39a918d; only four previously evaluated expressions are included. The Python
all-overlap core is a project-local regression reconstruction with no separate
Git author record; no individual author is invented. These project components
use MIT. Original full-file hashes and extracted-file identities are recorded
separately, with AST/numerical equivalence checks.

The upstream matcher source is byte-identical and MIT-licensed at 712eb202;
its exact notice accompanies the file. The helper is byte-identical to
CNA_clonality scripts/clonality_analysis_PFREQ_MOD.R at bbffb4a, introduced under
jurriaanjanssen at 579148f. Read-only comparison found 11/12 functions identical
to GPL-3 Clonality 1.47.0; calc.freq differs. No root grant covering the modification
was located. It remains externally acquired and checksum locked, rather than
being relabelled MIT or replaced with an unvalidated package implementation.

Direct upstream acquisition is opt-in under upstream terms and does not publish
those assets with this project. PFREQ and the PE150 annotation remain unbundled;
checksums are identities, not redistribution grants. Source-restoration images
require their own archive/license/source review, particularly QDNAseq.dev.
