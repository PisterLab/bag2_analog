# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__mux_bin_sel(Module):
    """Module for library bag2_analog cell mux_bin_sel.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'mux_bin_sel.yaml'))


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
            num_bits = 'Number of bits',
            unit_params = 'Unit binary mux parameters',
            mos_type = 'p=all PMOS, n=all NMOS, both=all tgate, split=upper half PMOS, lower half NMOS (if possible)'
        )

    def design(self, **params):
        """To be overridden by subclasses to design this module.

        This method should fill in values for all parameters in
        self.parameters.  To design instances of this module, you can
        call their design() method or any other ways you coded.

        To modify schematic structure, call:

        rename_pin()
        delete_instance()
        replace_instance_master()
        reconnect_instance_terminal()
        restore_instance()
        array_instance()
        """
        unit_params = params['unit_params']
        mos_type = params['mos_type']
        num_bits = params['num_bits']

        assert num_bits >= 1, f'Number of bits {num_bits} should be >= 1'

        num_in = 1 << num_bits
        num_units = num_in - 1
        msb = num_bits - 1

        # Design instances
        self.instances['XMUX_OUT'].design(mos_type='both', **unit_params)

        if num_bits > 1:
            mos_type_top = 'p' if mos_type in ['p', 'split'] else \
                            'n' if mos_type=='n' else 'both'
            mos_type_bot = 'n' if mos_type in ['n', 'split'] else \
                            'p' if mos_type=='p' else 'both'

            self.instances['XMUX_TOP'].design(num_bits=num_bits-1, mos_type=mos_type_top, unit_params=unit_params)
            self.instances['XMUX_BOT'].design(num_bits=num_bits-1, mos_type=mos_type_bot, unit_params=unit_params)
        else:
            self.delete_instance('XMUX_TOP')
            self.delete_instance('XMUX_BOT')

        # Reconnect instances
        if num_bits > 1:
            sel_pin_suffix = '' if num_bits == 2 else f'<{num_bits-2}:0>'
            sel_net_suffix = '<0>' if num_bits == 2 else f'<{num_bits-2}:0>'
            vin_top_suffix = f'<{num_in-1}:{num_in//2}>'
            vin_bot_suffix = f'<{num_in//2-1}:0>'

            top_reconn = {f'S{sel_pin_suffix}' : f'S{sel_net_suffix}',
                          f'Sb{sel_pin_suffix}' : f'Sb{sel_net_suffix}',
                          f'VIN{vin_bot_suffix}' : f'VIN{vin_top_suffix}'}
            bot_reconn = {f'S{sel_pin_suffix}' : f'S{sel_net_suffix}',
                          f'Sb{sel_pin_suffix}' : f'Sb{sel_net_suffix}',
                          f'VIN{vin_bot_suffix}' : f'VIN{vin_bot_suffix}'}
            out_reconn = {'S' : f'S<{msb}>',
                          'Sb' : f'Sb<{msb}>'}
            
            for pin, net in top_reconn.items():
                self.reconnect_instance_terminal('XMUX_TOP', pin, net)
            for pin, net in bot_reconn.items():
                self.reconnect_instance_terminal('XMUX_BOT', pin, net)
            for pin, net in out_reconn.items():
                self.reconnect_instance_terminal('XMUX_OUT', pin, net)
        else:
            out_reconn = {'S' : f'S',
                          'Sb' : f'Sb',
                          'VIN<1:0>' : 'VIN<1:0>'}
            for pin, net in out_reconn.items():
                self.reconnect_instance_terminal('XMUX_OUT', pin, net)

        # Rename pins
        if num_bits > 1:
            self.rename_pin('S', f'S<{num_bits-1}:0>')
            self.rename_pin('Sb', f'Sb<{num_bits-1}:0>')
            self.rename_pin('VIN<1:0>', f'VIN<{num_in-1}:0>')