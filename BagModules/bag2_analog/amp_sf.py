# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__amp_sf(Module):
    """Module for library bag2_analog cell amp_sf.

    Source follower. Input device is the device closest to the 'middle'
    (northernmost NMOS, southernmost PMOS)
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_sf.yaml'))


    def __init__(self, database, parent=None, prj=None, **kwargs):
        Module.__init__(self, database, self.yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            out_side = '"n" or "p"',
            pstack_params = 'pmos4_astack parameters',
            nstack_params = 'nmos4_astack_parameters'
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
        out_side = params['out_side']
        pstack_params = params['pstack_params']
        nstack_params = params['nstack_params']

        # Remove unused devices
        stack_p = pstack_params['stack']
        stack_n = nstack_params['stack']

        has_n = out_side == 'n' or stack_n > 0
        has_p = out_side == 'p' or stack_p > 0

        if not has_n:
            self.delete_instance('XN')
            self.remove_pin('VN')
            self.reconnect_instance_terminal('XP', 'D', 'VSS')

        if not has_p:
            self.delete_instance('XP')
            self.remove_pin('VP')
            self.reconnect_instance_terminal('XN', 'D', 'VDD')

        # Design still-present devices
        if has_n:
            self.instances['XN'].design(export_mid=True, **nstack_params)
            if stack_n > 1:
                self.reconnect_instance_terminal('XN', f'G<{stack_n-1}:0>', f'VN<{stack_n-1}:0>')
                self.rename_pin('VN', f'VN<{stack_n-1}:0>')

        if has_p:
            self.instances['XP'].design(export_mid=True, **pstack_params)
            if stack_p > 1:
                self.reconnect_instance_terminal('XP', f'G<{stack_p-1}:0>', f'VP<{stack_p-1}:0>')
                self.rename_pin('VP', f'VP<{stack_p-1}:0>')

        # Connecting the output
        out_inst = 'XN' if out_side == 'n' else 'XP'
        out_inst_pin = f'm<{stack_n-2}:0>' if out_side == 'n' else f'm<{stack_p-2}:0>'
        out_mid_idx = stack_n - 2 if out_side == 'n' else stack_p - 2
        out_inst_conn = ','.join(['VOUT'] + [f'm<{i}>' for i in range(out_mid_idx-1, -1, -1)])

        self.reconnect_instance_terminal(out_inst, out_inst_pin, out_inst_conn)