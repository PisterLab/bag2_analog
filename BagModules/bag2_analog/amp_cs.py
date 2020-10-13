# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__amp_cs(Module):
    """Module for library bag2_analog cell amp_cs.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_cs.yaml'))


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
        pstack_params = params['pstack_params']
        nstack_params = params['nstack_params']

        # Designing instances
        self.instances['XP'].design(**pstack_params)
        self.instances['XN'].design(**nstack_params)

        # Changing pins
        num_n = nstack_params['stack']
        num_p = pstack_params['stack']
        if num_n > 1:
            self.rename_pin('VN', f'VN<{num_n-1}:0>')
            self.reconnect_instance_terminal('XN', f'G<{num_n-1}:0>', f'VN<{num_n-1}:0>')
        if num_p > 1:
            self.rename_pin('VP', f'VP<{num_p-1}:0>')
            self.reconnect_instance_terminal('XP', f'G<{num_p-1}:0>', f'VP<{num_n-1}:0>')