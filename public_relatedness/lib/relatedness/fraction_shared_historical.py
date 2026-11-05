# Production core extracted verbatim from the validated historical regression module.
# The cohort-specific CLI and its historical filesystem inputs are not executed.
import argparse

import csv

import hashlib

import importlib.util

import json

import statistics

from collections import Counter, defaultdict

from decimal import Decimal, localcontext

from fractions import Fraction

from pathlib import Path

MAXGAP = 2_500_000

def read(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t" if path.suffix == ".tsv" else ","))

def integer(value):
    d = Decimal(value)
    assert d == d.to_integral_value()
    return int(d)

def group_observations(rows):
    groups = defaultdict(lambda: defaultdict(list))
    for r in rows:
        groups[r["SampleID"]][(r["Chr"], r["SVType"], r["boundary_type"])].append(integer(r["coordinate"]))
    assert all(len(values) == len(set(values)) for sample in groups.values() for values in sample.values())
    return groups

def historical_matches(groups, a, b):
    """Every eligible overlap is counted; no one-to-one constraint or deduplication.

    This reproduces the getHit() queryHits multiset in recovered source, plus
    the subtraction rules verified against all supplied historical count rows.
    """
    matches = []
    for key in sorted(groups[a].keys() & groups[b].keys()):
        for x in sorted(groups[a][key]):
            for y in sorted(groups[b][key]):
                if abs(x - y) <= MAXGAP:
                    matches.append((*key, x, y, abs(x - y)))
    return matches

def counts(groups, a, b):
    matches = historical_matches(groups, a, b)
    n_a = sum(map(len, groups[a].values()))
    n_b = sum(map(len, groups[b].values()))
    h = len(matches)
    return (h, n_a - h, n_b - h), matches

def precise_fraction(counts_):
    total = sum(counts_)
    return Fraction(counts_[0], total) if total else None

def fraction_comparison(value, supplied):
    with localcontext() as context:
        context.prec = 60
        exact_decimal = Decimal(value.numerator) / value.denominator
        original = Decimal(supplied)
        quantum = Decimal(1).scaleb(original.as_tuple().exponent)
        return str(exact_decimal), str(abs(exact_decimal - original)), exact_decimal.quantize(quantum) == original
