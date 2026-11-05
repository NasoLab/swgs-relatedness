# Licensing and redistribution audit — 2026-11-05

This is an evidence/permissions inventory. No new third-party source, package
archive, model, image or reference payload is copied into public-release
folders. The four retained Huntsman pipeline files are identified below. External
inherited scientific implementations are not bundled. The scientific
runner, preprocessing, helper, matcher and references are external inputs.
This audit does not authorize publishing them or the originating repository's
ancestors; the snapshot is not yet cleared for publication.

| Component | Evidence at the relevant source/version | Required action and scope |
| --- | --- | --- |
| Original project / public adapters | Originating project had no LICENSE or COPYING; multiple authors are credited. Snapshot LICENSE explicitly records the pending grant | MIT is selected for authorized project code; confirm ownership and the four-file legacy grant below. This blocks publication of included files |
| Historical preprocessing | `Huntsmanlab/squamous-cell-clonality`, revision `39a918d2a38a30cc78a90a51a314b7ef83a7813d`; no root license found in that revision | Obtain explicit permission/license for the selected expressions; continue runtime loading from user-supplied source meanwhile |
| Recovered breakpoint matching | `argymeg/breakclone`, revision `712eb202303119588ca10889ca92a721afd0c396`; exact-revision LICENSE confirms MIT, copyright 2022 The Authors | Retain the exact copyright and full MIT notice if source is later copied; current runtime input remains external |
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

## Included legacy files: authorization required

| Included file | Source and recorded contributors | Existing grant | Essential / alternative |
| --- | --- | --- | --- |
| `bin/runQDNAseq.R` | Huntsman `scripts/runQDNAseq.R`, introduced at `b9ed823`, relocated at `9578c5d`; Maxwell Douglas, Ding Ma, Sheila Nicholson | No file-level grant located | Required for full execution; an authorized external copy could be called without bundling it |
| `modules/local/trimmomatic/main.nf` | Huntsman refactor `9578c5d`; Nicholson/Corbett, with Douglas/Ma/Lynch predecessor contributions | No grant located | Required trimming wrapper; externalize or independently replace and validate |
| `modules/local/alignment/main.nf` | Huntsman refactor `9578c5d`; Nicholson/Corbett, with Ma/Lynch predecessor contributions | No grant located | Required BWA-MEM2/samtools wrapper; externalize or independently replace and validate |
| `modules/local/mark_duplicates/main.nf` | Huntsman refactor `9578c5d`; Nicholson/Corbett, with Douglas/Ma/Lynch predecessor contributions | No grant located | Required Picard wrapper; externalize or independently replace and validate |

This is the smallest additional legacy-file permission scope. Other included
code and release materials are recorded under Corbett's contributions; Git does
not establish legal ownership. Confirm authority over those contributions too.
A confirmed institution/rightsholder may authorize the relevant scope together;
five separate individual grants are not automatically necessary. PI approval is
sufficient only where the PI has the relevant rights or delegated authority.
Acknowledgement is preserved and does not resolve the missing grant.

## Gates for this development source release

1. Record ownership and MIT distribution authorization for the included project
   scope, specifically the four files above. Apply the approved text and accurate
   copyright notices only after that approval; LICENSE.MIT.proposed is not active.
2. Obtain explicit publication approval and choose an empty non-fork destination,
   or an explicitly approved plan for the existing fork's historical data.
3. Update release metadata/checksums and audit every clean release commit.

External QDNAseq.dev, inherited runner/helper/preprocessing, PFREQ and PE150
resources remain user-supplied. Their absent redistribution grants do not alone
prevent publication of independently owned source wrappers; operators still need
authorized acquisition/use. Do not distribute those assets or containing images
without separate rights review. Verified breakclone/UTANOS MIT evidence remains
above; preserve notices if they are distributed later.

Missing reference-generation receipts, unbuilt source-restoration images and
pending end-to-end/cross-host validation are documented reproducibility limits.
They do not independently prohibit this explicitly limited development source
release. Public test data can be added later with its own authorization.
No scientific replacement, dependency upgrade or permission request is made here.
