# -*- coding: utf-8 -*-

from typing import Dict, Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__cascode_core(Module):
    """Module for library bag2_analog cell cascode_core.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'cascode_core.yaml'))


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
            p_params = 'P-side parameters of the stack (see pmos4_astack)',
            n_params = 'N-side parameters of the stack (see nmos4_astack)'
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
        p_params = params['p_params']
        n_params = params['n_params']

        n_stack = n_params['stack']
        p_stack = p_params['stack']

        suffix_gn = f'<0>' if n_stack==1 else f'<{n_stack-1}:0>'
        suffix_gp = f'<0>' if p_stack==1 else f'<{p_stack-1}:0>'

        # Design instances
        self.instances['XN'].design(**n_params, export_mid=True)
        self.instances['XP'].design(**p_params, export_mid=True)

        # Reconnect pins
        if n_stack > 1:
            suffix_mn = f'<0>' if n_stack==2 else f'<{n_stack-2}:0>'
            self.reconnect_instance_terminal('XN', f'G{suffix_gn}', f'GN{suffix_gn}')
            self.reconnect_instance_terminal('XN', f'm{suffix_mn}', f'DN{suffix_mn}')
            self.reconnect_instance_terminal('XN', f'D', f'DN<{n_stack-1}>')
            self.rename_pin('GN<0>', f'GN{suffix_gn}')
            self.rename_pin('DN<0>', f'DN{suffix_gn}')

        if p_stack > 1:
            suffix_mp = f'<0>' if p_stack==2 else f'<{p_stack-2}:0>'
            self.reconnect_instance_terminal('XP', f'G{suffix_gp}', f'GP{suffix_gp}')
            self.reconnect_instance_terminal('XP', f'm{suffix_mp}', f'DP{suffix_mp}')
            self.reconnect_instance_terminal('XP', f'D', f'DP<{p_stack-1}>')
            self.rename_pin('GP<0>', f'GP{suffix_gp}')
            self.rename_pin('DP<0>', f'DP{suffix_gp}')