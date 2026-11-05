"""Guard established commands/parameter choices; not numerical validation."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ScientificContractTests(unittest.TestCase):
    def test_qdnaseq_methods(self):
        script = (ROOT / 'bin/runQDNAseq.R').read_text()
        for expression in ['chromosomes = c("X", "Y")', 'residual = TRUE, blacklist = TRUE',
                           'estimateCorrection(readCountsFiltered)', 'correctBins(readCountsFiltered)',
                           'normalizeBins(copyNumbers)', 'smoothOutlierBins(copyNumbersNormalized)',
                           'segmentBins(copyNumbersSmooth, transformFun = "sqrt")',
                           'normalizeSegmentedBins(copyNumbersSegmented)',
                           'paste0(binsize, "_noXY_copyNumbersSegmented.rds")']:
            self.assertIn(expression, script)
        workflow = (ROOT / 'public_relatedness/modules/cohort.nf').read_text()
        self.assertIn('Rscript ${runner} 500kb', workflow)
        self.assertIn('500kb_noXY_copyNumbersSegmented.rds', workflow)
        self.assertNotIn('500kb_noXY_bins_rCN.rds', workflow)

    def test_cghcall_methods_and_strict_cohort_guard(self):
        script = (ROOT / 'bin/prepare_cghcall_cohort.R').read_text()
        self.assertIn('fixed_method <- "CGHcall"', script)
        self.assertIn('fixed_organism <- "other"', script)
        guard = (ROOT / 'public_relatedness/bin/assert_cohort.R').read_text()
        self.assertIn('identical(sampleNames(object), expected)', guard)
        self.assertIn('!"calls" %in%', guard)

    def test_alignment_methods_and_failures(self):
        align = (ROOT / 'modules/local/alignment/main.nf').read_text()
        self.assertIn('bwa-mem2 mem -M', align)
        self.assertIn('samtools sort', align)
        self.assertIn('samtools index', align)
        for name in ['trimmomatic', 'alignment', 'mark_duplicates']:
            self.assertIn('set -euo pipefail', (ROOT / f'modules/local/{name}/main.nf').read_text())
        self.assertIn('errorStrategy = \'terminate\'', (ROOT / 'public_relatedness/nextflow.config').read_text())
        self.assertNotIn('ignore', (ROOT / 'public_relatedness/nextflow.config').read_text())


if __name__ == '__main__':
    unittest.main()
