# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__dac_r2r(Module):
    """Module for library bag2_analog cell dac_r2r.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'dac_r2r.yaml'))


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
            res_params = 'Parameters for a single resistor unit. 2R units are series units.',
            num_bits = 'Number of bits.'
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
        num_bits = params['num_bits']
        res_params = params['res_params']

        assert num_bits > 0, f'Number of bits {num_bits} must be > 0'

        # Design instances
        inst_suffixes = ['2_TOP', '2_BOT', '2_XTOP', '2_XBOT', '1']
        for inst in [f'XR{s}' for s in inst_suffixes]:
            self.instances[inst].parameters = res_params

        print('*** WARNING *** (dac_r2r) Check that ideal passive values are correct in generated schematic')

        # Array and/or delete instances as necessary
        suffix = f'<{num_bits-1}:0>'
        if num_bits == 1:
            xr2_mid_conn = 'VOUT'
            self.delete_instance('XR1')
            self.reconnect_instance_terminal('XR2_BOT', 'MINUS', xr2_mid_conn)
            self.reconnect_instance_terminal('XR2_XTOP', 'PLUS', xr2_mid_conn)
        else:
            num_mid = num_bits - 1
            if num_mid > 1:
                xr1_top_conn = f'm<{num_mid-1}:0>'
                xr1_bot_conn = f'VOUT,m<{num_mid-1}:1>' if num_mid > 2 else 'VOUT,m<1>'
                xr2_mid_conn = f'VOUT,m<{num_mid-1}:0>'
            else:
                xr1_top_conn = 'm<0>'
                xr1_bot_conn = 'VOUT'
                xr2_mid_conn = 'VOUT,m<0>'

            xr2_top_conn = f'B<{num_bits-1}:0>'
            
            self.array_instance('XR1', [f'XR1<{num_bits-2}:0>'], 
                                [dict(PLUS=xr1_top_conn,
                                     MINUS=xr1_bot_conn)])
            self.array_instance('XR2_TOP', [f'XR2_TOP<{num_bits-1}:0>'],
                                [dict(PLUS=xr2_top_conn,
                                     MINUS=f'r<{num_bits-1}:0>')])
            self.array_instance('XR2_BOT', [f'XR2_BOT<{num_bits-1}:0>'],
                                [dict(PLUS=f'r<{num_bits-1}:0>',
                                     MINUS=xr2_mid_conn)])
            self.reconnect_instance_terminal('XR2_XTOP', 'PLUS', 'm<0>')

            self.rename_pin('B', f'B<{num_bits-1}:0>')