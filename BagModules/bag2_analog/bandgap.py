# -*- coding: utf-8 -*-

from typing import Dict, Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__bandgap(Module):
    """Module for library bag2_analog cell bandgap.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'bandgap.yaml'))


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
            amp_params = 'Amplifier parameters',
            p_params = 'Feedback PMOS parameters',
            constgm_params = 'Constant gm parameters',
            res_params_dict = 'Keys are "fb" and "diff"',
            bulk_conn = 'Resistor bulk connection terminal',
            diode_mult = 'Diode multiplication factor'
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
        amp_params = params['amp_params']
        p_params = params['p_params']
        constgm_params = params['constgm_params']
        res_params_dict = params['res_params_dict']
        bulk_conn = params['bulk_conn']
        diode_mult = params['diode_mult']

        bias_type = amp_params['in_type']
        amp_in_type = amp_params['in_type']

        # Design instances
        self.instances['XOTA'].design(**amp_params)
        self.instances['XPN'].design(**p_params)
        self.instances['XPP'].design(**p_params)
        self.instances['XCONSTGM'].design(**constgm_params)

        res_map = dict(XRFBP='fb',
                       XRFBN='fb',
                       XRDIFF='diff')
        for inst, k in res_map.items():
            self.instances[inst].design(**(res_params_dict[k]))

        # Array diode if necessary
        # if diode_mult > 1:
        #     self.array_instance('DP',
        #                         [f'DP<{diode_mult-1}:0>'],
        #                         [dict(PLUS='VDP', MINUS='VSS')])

        # Reconnect amplifier biasing if necessary
        if amp_in_type == 'p':
            self.reconnect_instance_terminal('XOTA', 'VGTAIL', 'VP')

        # Connect resistor bulk terminal
        for inst in res_map.keys():
            self.reconnect_instance_terminal(inst, 'BULK', bulk_conn)

        if bulk_conn in ('VDD', 'VSS'):
            self.remove_pin('BULK')
        elif bulk_conn != 'BULK':
            self.rename_pin('BULK', bulk_conn)

