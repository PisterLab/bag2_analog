import argparse
from argparse import Namespace
from pathlib import Path
import sys, pdb, traceback
from pprint import pprint

from bag.io.file import Pickle, Yaml
from bag.core import BagProject

io_cls_dict = {
    'pickle': Pickle,
    'yaml': Yaml,
}


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('specs_fname', help='specs yaml file')
    parser.add_argument('--format', default='yaml',
                        help='format of spec file (yaml, json, pickle)')
    parser.add_argument('-dump', '--dump', default='',
                        help='If given will dump output of script into that '
                             'file according to the format specified')
    args = parser.parse_args()
    return args


def run_main(args: Namespace):
    specs_fname = Path(args.specs_fname)
    io_cls = io_cls_dict[args.format]
    specs_info = io_cls.load(str(specs_fname))

    # Import design module
    dsn_mod = __import__(specs_info['dsn_mod'], fromlist=[specs_info['dsn_cls']])
    dsn_cls = getattr(dsn_mod, specs_info['dsn_cls'])

    # Get spec
    dsn_module = dsn_cls()
    specs = specs_info['params']

    # Design
    print("Designing...")
    sch_params, best_op = dsn_module.design(**specs)

    if sch_params is not None and args.dump:
        out_tmp_file = Path(args.dump)
        print(f"Saving results to {out_tmp_file}")
        io_cls.save(sch_params, out_tmp_file)

if __name__ == '__main__':
    args = parse_args()
    local_dict = locals()
    try:
        run_main(args)
    except:
        extype, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
