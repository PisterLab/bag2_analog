# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__mux_onehot_sel(Module):
    """Module for library bag2_analog cell mux_onehot_sel.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'mux_onehot_sel.yaml'))


    def __init__(self, database, parent=None, prj=None, **kwargs):
        Module.__init__(self, database, self.yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls) -> Mapping[str,str]:
        # type: () -> Dict[str, str]
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            num_in = 'Number of inputs to the mux',
            mos_type = 'p=all PMOS, n=all NMOS, both=all tgate, split=upper portion PMOS, lower portion NMOS (if possible)',
            split_code = 'The first PMOS code if mos_type is split',
            mos_params_dict = 'Dictionary of transistor parameters (keys n, p)'
        )

    def design(self, **params):
        """To be overridden by subclasses to design this module.
        """
        num_in = params['num_in']
        mos_type = params['mos_type']
        mos_params_dict = params['mos_params_dict']

        assert num_in > 1, f'Number of inputs {num_in} should be > 1'

        suffix_all = f'<{num_in-1}:0>'

        # Arraying for a split
        if mos_type == 'split':
            split_code = params['split_code']

            # Determine if user has functionally asked for all NMOS or all PMOS
            if split_code in (0, num_in-1):
                mos_type = 'p' if split_code == 0 else 'p'
            else:
                suffix_lower = f'<{split_code-1}:0>' if split_code > 1 else '<0>' 
                suffix_upper = f'<{num_in-1}:{split_code}>' if split_code < num_in-2 else f'<{split_code}>'
                self.array_instance('XSW', [f'XSW_LOWER{suffix_lower}', f'XSW_UPPER{suffix_upper}'],
                                    [dict(CTRL=f'S{suffix_lower}',
                                          CTRLb=f'Sb{suffix_lower}',
                                          D=f'VIN{suffix_lower}',
                                          S='VOUT',
                                          BP='VDD',
                                          BN='VSS'),
                                     dict(CTRL=f'S{suffix_upper}',
                                          CTRLb=f'Sb{suffix_upper}',
                                          D=f'VIN{suffix_upper}',
                                          S='VOUT',
                                          BP='VDD',
                                          BN='VSS')])
                self.instances['XSW'][0].design(mos_type='n', mos_params_dict=mos_params_dict)
                self.instances['XSW'][1].design(mos_type='p', mos_params_dict=mos_params_dict)
                sel_pin = f'S{suffix_lower}'
                selb_pin = f'Sb{suffix_upper}'

        # Arraying for a non-split mux
        if mos_type != 'split':
            self.array_instance('XSW', [f'XSW{suffix_all}'], [dict(CTRL=f'S{suffix_all}',
                                                                   CTRLb=f'Sb{suffix_all}',
                                                                   D=f'VIN{suffix_all}',
                                                                   S='VOUT',
                                                                   BP='VDD',
                                                                   BN='VSS')])
            self.instances['XSW'][0].design(mos_type=mos_type, mos_params_dict=mos_params_dict)
            sel_pin = f'S{suffix_all}' if mos_type in ('n', 'both') else ''
            selb_pin = f'Sb{suffix_all}' if mos_type in ('p', 'both') else ''

        # Renaming and/or deleting pins as necessary
        if sel_pin:
            self.rename_pin('S', sel_pin)
        else:
            self.delete_pin('S')

        if selb_pin:
            self.rename_pin('Sb', selb_pin)
        else:
            self.delete_pin('Sb')

        self.rename_pin('VIN', f'VIN{suffix_all}')