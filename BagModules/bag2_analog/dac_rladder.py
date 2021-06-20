# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__dac_rladder(Module):
    """Module for library bag2_analog cell dac_rladder.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'dac_rladder.yaml'))


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
            is_full = 'True to extend the mux from the bottom to the top-1 of the ladder',
            num_bits = 'Number of bits in the mux',
            code_min = 'If the mux does not extend from the bottom to the top-1 of the ladder,' \
                        'the index at which the mux does start',
            mux_params = 'mux_bin parameters',
            rladder_params = 'rladder_core parameters'
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
        is_full = params['is_full']
        rladder_params = params['rladder_params']
        num_bits = params['num_bits']
        mux_params = params['mux_params']

        num_res = (1 << num_bits) if is_full else rladder_params['num_out']
        num_mux_in = 1 << num_bits
        code_min = 0 if is_full else params['code_min']
        code_max = code_min + num_mux_in - 1

        assert code_max < num_res, f'Mux max connection point ({code_max}) exceeds height of the resistive ladder {num_res-1}'

        # Design instances
        rladder_params['num_out'] = num_res
        self.instances['XMUX'].design(num_bits=num_bits, **mux_params)
        self.instances['XRLADDER'].design(**rladder_params)

        # Rewire mux
        suffix_mux = f'<{num_mux_in-1}:0>'

        mid_mux_net = f'mid<{code_max}:{code_min}>' if code_min != code_max else f'mid<{code_min}>'
        self.reconnect_instance_terminal('XMUX', f'VIN{suffix_mux}', mid_mux_net)

        if num_bits > 1:
            sel_pin_net = f'S<{num_bits-1}:0>'
            self.reconnect_instance_terminal('XMUX', sel_pin_net, sel_pin_net)
            self.rename_pin('S', sel_pin_net)

        # Rewire resistive ladder
        suffix_mid_res = f'<{num_res-1}:0>'
        mid_net = f'mid{suffix_mid_res}'
        self.reconnect_instance_terminal('XRLADDER', f'out{suffix_mid_res}', mid_net)

        # Remove noConns if they aren't used, rewire as necessary
        if code_min == 0:
            self.delete_instance('XNOCONN_LOWER')
        elif code_min > 1:
            self.array_instance('XNOCONN_LOWER', [f'XNOCONN_LOWER<{code_min-1}:0>'],
                                [dict(noConn=f'mid<{code_min-1}:0>')])
        else:
            self.reconnect_instance_terminal('XNOCONN_LOWER', 'noConn', f'mid<0>')

        if code_max == num_res - 1:
            self.delete_instance('XNOCONN_UPPER')
        elif code_max < num_res - 2:
            num_unused_upper = num_res - 1 - code_max
            self.array_instance('XNOCONN_UPPER', [f'XNOCONN_UPPER<{num_res-1}:{num_res-num_unused_upper}>'],
                                [dict(noConn=f'mid<{num_res-1}:{num_res-num_unused_upper}>')])
        else:
            self.reconnect_instance_terminal('XNOCONN_UPPER', 'noConn', f'mid<{num_res-1}>')