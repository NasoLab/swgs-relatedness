"""Opt-in local Nextflow stub orchestration. Empty artifacts are NOT scientific fixtures."""
import csv
import hashlib
import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('PUBLIC_NEXTFLOW'), 'Set PUBLIC_NEXTFLOW to a Nextflow command for stub tests')
class NextflowTests(unittest.TestCase):
    def run_stub(self, with_pairs=True, fail_process=None, custom_temp=False):
        tmp = tempfile.TemporaryDirectory(prefix='public-relatedness-stub-')
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        inputs = root / "inputs with spaces'and-quote"
        inputs.mkdir()
        rows = []
        for sid in ['sampleC', 'sampleA', 'sampleB']:
            folder = inputs / sid
            folder.mkdir()
            # Same basename for both mates exercises collision-free staging.
            mates = []
            for mate in ['one', 'two']:
                directory = folder / mate
                directory.mkdir()
                path = directory / "reads with 'quote'.fq.gz"
                path.write_text('stub staging marker only\n')
                mates.append(str(path))
            rows.append([sid, *mates])
        samples = inputs / 'samples.tsv'
        with samples.open('w', newline='') as handle:
            writer = csv.writer(handle, delimiter='\t')
            writer.writerow(['sample_id', 'fastq_1', 'fastq_2'])
            writer.writerows(rows)
        pairs = inputs / 'pairs.tsv'
        pairs.write_text('pair_id\tsample1\tsample2\ncomparison2\tsampleC\tsampleB\ncomparison1\tsampleC\tsampleA\n')
        ref = root / 'reference' / 'GCA_000001405.15_GRCh38_no_alt_analysis_set.fna'
        ref.parent.mkdir()
        for suffix in ['', '.0123', '.amb', '.ann', '.bwt.2bit.64', '.pac']:
            Path(str(ref) + suffix).touch()
        bins = root / 'hg38_PE150_500kb.rds'
        bins.write_text('stub reference marker only\n')
        config = root / 'stub.config'
        config.write_text("process { cpus = 1; memory = '256 MB' }\n" +
            (f"process {{ withName: '{fail_process}' {{ beforeScript = 'exit 42' }} }}\n" if fail_process else ''))
        if custom_temp:
            volume = root / 'large_volume_tmp'
            volume.mkdir()
            # Real task shells must create files and scratch directories on the
            # selected volume. No sequencing command is executed by these stubs.
            probe = ('import os,tempfile; f=tempfile.NamedTemporaryFile(mode="w",'
                     'prefix="temp-proof-",dir=os.environ["TMPDIR"],delete=False); '
                     'f.write(os.getcwd()); f.close()')
            with config.open('a') as handle:
                handle.write("process.afterScript = '''python3 -c " + shlex.quote(probe) + "'''\n")
        env = dict(os.environ, NXF_OFFLINE='true', NXF_HOME=str(root / 'nxf_home'))
        cmd = shlex.split(os.environ['PUBLIC_NEXTFLOW']) + [
            '-C', f'{ROOT / "nextflow.config"},{config}', 'run', str(ROOT / 'main.nf'),
            '-stub-run', '-ansi-log', 'false', '-work-dir', str(root / 'work'),
            '--samples', str(samples), '--reference', str(ref), '--pe150_bins', str(bins),
            '--pe150_bins_sha256', hashlib.sha256(bins.read_bytes()).hexdigest(), '--outdir', str(root / 'out')]
        runner = root / 'runner.stub'
        runner.write_text('STUB ONLY: no scientific implementation\n')
        cmd += ['--pcc_llr_runner', str(runner)]
        if custom_temp:
            cmd += ['--temp_directory', str(volume)]
        if with_pairs:
            cmd += ['--pairs', str(pairs)]
            for key in ['pfreq', 'llr_helper', 'breakpoint_preprocessing', 'breakpoint_matching', 'fraction_implementation']:
                asset = root / (key + '.stub')
                asset.write_text('STUB ONLY: not a scientific resource\n')
                cmd += ['--' + key, str(asset)]
        result = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=120)
        if result.returncode and (root / '.nextflow.log').exists():
            log = (root / '.nextflow.log').read_text()
            at = log.find('Cannot invoke')
            result.stderr += '\n' + log[max(0, at-500):at+5500]
        return root, result

    def test_complete_cohort_and_staging(self):
        root, result = self.run_stub()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((root / 'out/relative_cn/qdnaseq/pe/500kb/500kb_noXY_copyNumbersSegmented.rds').exists())
        self.assertTrue((root / 'out/cghcall/cohort_500kb_noXY_CGHcall.rds').exists())
        self.assertEqual((root / 'out/manifest/expected_samples.txt').read_text(), 'sampleC\nsampleA\nsampleB\n')
        with (root / 'out/manifest/pairs.csv').open() as handle:
            self.assertEqual([r['pair_id'] for r in csv.DictReader(handle)], ['comparison2', 'comparison1'])
        qdna_tasks = [p for p in (root / 'work').glob('*/*/bam_inputs')]
        self.assertEqual(len(qdna_tasks), 1)
        self.assertEqual(len(list(qdna_tasks[0].glob('*.bam'))), 3)
        staged = (qdna_tasks[0].parent / 'staged_bams.txt').read_text().splitlines()
        self.assertEqual([Path(p).name.split('.')[0] for p in staged], ['sampleC', 'sampleA', 'sampleB'])
        with (root / 'out/pair_results.tsv').open() as handle:
            scored = list(csv.DictReader(handle, delimiter='\t'))
        self.assertEqual([(r['pair_id'], r['sample1'], r['sample2']) for r in scored],
                         [('comparison2', 'sampleC', 'sampleB'), ('comparison1', 'sampleC', 'sampleA')])
        self.assertTrue(all(r['processing_status'] == 'stub_not_computed' and r['pcc'] == 'NA' for r in scored))

    def test_optional_pairs(self):
        root, result = self.run_stub(with_pairs=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((root / 'out/cghcall/cohort_500kb_noXY_CGHcall.rds').exists())
        with (root / 'out/pair_results.tsv').open() as handle:
            self.assertEqual(list(csv.DictReader(handle, delimiter='\t')), [])

    def test_temporary_volume_used_by_tasks_and_upstream_scratch(self):
        root, result = self.run_stub(custom_temp=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        volume = root / 'large_volume_tmp'
        proofs = list(volume.glob('temp-proof-*'))
        self.assertEqual(len(proofs), 13)
        self.assertEqual(sum(Path(p.read_text()).is_relative_to(volume) for p in proofs), 9)

    def test_duplicate_marking_failure_terminates(self):
        root, result = self.run_stub(fail_process='MARK_DUPLICATES')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exit status (42)', result.stdout + result.stderr)
        self.assertIn("Error executing process > 'MARK_DUPLICATES", result.stdout + result.stderr)
        self.assertFalse((root / 'out/cghcall/cohort_500kb_noXY_CGHcall.rds').exists())

    def test_alignment_failure_terminates(self):
        root, result = self.run_stub(fail_process='ALIGNMENT')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exit status (42)', result.stdout + result.stderr)
        self.assertIn("Error executing process > 'ALIGNMENT", result.stdout + result.stderr)
        self.assertFalse((root / 'out/cghcall/cohort_500kb_noXY_CGHcall.rds').exists())


if __name__ == '__main__':
    unittest.main()
