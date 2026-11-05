"""Resolve bundled scientific source and operator-supplied assets without launch-directory assumptions."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT / 'scientific_sources.json').read_text())['sources']
REFERENCES = json.loads((ROOT / 'references/manifest.json').read_text())['resources']
PARAMS = {'runner': 'pcc_llr_runner', 'preprocessing': 'breakpoint_preprocessing',
          'matching': 'breakpoint_matching', 'fraction_implementation': 'fraction_implementation'}


def resolve(params):
    out = dict(params)
    directory = out.get('resource_directory') or os.environ.get('SWGS_RESOURCE_DIR')
    directory = Path(directory).expanduser().resolve() if directory else None
    for key, param in PARAMS.items():
        if not out.get(param):
            out[param] = str(ROOT / SOURCES[key]['path'])
    if directory:
        for item in REFERENCES:
            param = item['config_param']
            if not item.get('suffix') and not out.get(param):
                out[param] = str(directory / item['filename'])
        if not out.get('llr_helper'):
            out['llr_helper'] = str(directory / SOURCES['helper']['filename'])
    # Cached host scoring stays available through explicit R executable selectors.
    cached_image = directory / 'containers/metrics.sif' if directory else None
    use_resource_cache = directory and (not out.get('called_rds') or
                                        (cached_image.is_file() and not out.get('metrics_rscript')))
    cache = out.get('image_directory') or (directory / 'containers' if use_resource_cache else None)
    if cache and not out.get('metrics_container'):
        out['metrics_container'] = str(Path(cache) / 'metrics.sif')
    if not out.get('metrics_rscript'):
        out['metrics_rscript'] = '/opt/swgs/bin/Rscript-llr' if out.get('metrics_container') else 'Rscript-llr'
    if not out.get('breakpoint_rscript'):
        out['breakpoint_rscript'] = '/opt/swgs/bin/Rscript-general' if out.get('metrics_container') else 'Rscript-general'
    return out


def missing_hint(label):
    # The reference validator reports inventory IDs; acquisition uses parameter names.
    label = next((item['config_param'] for item in REFERENCES if item['id'] == label), label)
    if label in {'pfreq', 'llr_helper', 'reference', 'pe150_bins'}:
        return (' Set resource_directory (or an explicit advanced path); run '
                'python public_relatedness/bin/prepare_resources.py --help for acquisition and verification. '
                'PE150 annotation and existing BWA-MEM2 sidecars must be supplied unchanged; '
                'see public_relatedness/references/README.md.')
    return ''
