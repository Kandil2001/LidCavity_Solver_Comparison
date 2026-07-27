#!/usr/bin/env python3
from __future__ import annotations
import argparse


def default_steps(N: int, Re: int) -> tuple[int, int]:
    # Conservative defaults for a large full-study run. Increase from the shell for final publication runs.
    if N >= 128 and Re >= 1000:
        return 4000, 300
    if N >= 128:
        return 2500, 250
    if Re >= 1000:
        return 2000, 250
    return 1000, 200


def main() -> int:
    p = argparse.ArgumentParser(description='Generate full case lists for the LidCavity mega study.')
    p.add_argument('--domain', action='store_true', help='Print domain-solver case list: N:Re:scheme:steps:poisson_iters')
    p.add_argument('--original', action='store_true', help='Print original benchmark case table: id,N,Re,scheme,pressure')
    p.add_argument('--grids', default='32,64,128')
    p.add_argument('--reynolds', default='100,400,1000')
    p.add_argument('--schemes', default='upwind,central')
    p.add_argument('--pressures', default='RBGS,RBSOR')
    p.add_argument('--steps-scale', type=float, default=1.0, help='Multiply default time steps for domain solvers')
    p.add_argument('--poisson-scale', type=float, default=1.0, help='Multiply default Poisson iterations for domain solvers')
    args = p.parse_args()

    grids = [int(x) for x in args.grids.split(',') if x]
    reynolds = [int(x) for x in args.reynolds.split(',') if x]
    schemes = [x for x in args.schemes.split(',') if x]
    pressures = [x for x in args.pressures.split(',') if x]

    if args.original:
        cid = 0
        print('case_id,N,Re,scheme,pressure')
        for N in grids:
            for Re in reynolds:
                for scheme in schemes:
                    for pressure in pressures:
                        cid += 1
                        print(f'{cid},{N},{Re},{scheme},{pressure}')
        return 0

    # Default to domain list if neither option is specified.
    for N in grids:
        for Re in reynolds:
            for scheme in schemes:
                steps, piters = default_steps(N, Re)
                steps = max(1, int(round(steps * args.steps_scale)))
                piters = max(1, int(round(piters * args.poisson_scale)))
                print(f'{N}:{Re}:{scheme}:{steps}:{piters}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
