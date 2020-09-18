# -*- coding: utf-8 -*-

from typing import Mapping, Any

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__cascode_dual(Module):
    """Module for library bag2_analog cell cascode_dual.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'cascode_dual.yaml'))


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
            p_params = 'Parameters for the cascode_p',
            n_params = 'Parameters for the cascode_n'
        )

    def design(self, **params) -> None:
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
        p_params: Mapping[str, Any] = params['p_params']
        n_params: Mapping[str, Any] = params['n_params']

        self.instances['XPA'].design(**p_params)
        self.instances['XPB'].design(**p_params)
        self.instances['XNA'].design(**n_params)
        self.instances['XNB'].design(**n_params)