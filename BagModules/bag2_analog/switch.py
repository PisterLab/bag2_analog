# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__switch(Module):
    """Module for library bag2_analog cell switch.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'switch.yaml'))


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
            mos_type = '"n", "p", or "both" to indicate NMOS, PMOS, or tgate, respectively',
            mos_params_dict = 'Dictionary of transistor parameters (keys n, p)'
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
        mos_type = params['mos_type']
        mos_params = params['mos_params_dict']

        # Design instances
        if mos_type != 'n':
            pch_params = mos_params['p']
            self.instances['XP'].design(**pch_params)
        if mos_type != 'p':
            nch_params = mos_params['n']
            self.instances['XN'].design(**nch_params)

        # Remove unnecessary instances
        remove_pins = []
        if mos_type == 'n':
            self.delete_instance('XP')
            remove_pins = ['BP', 'CTRLb']
        if mos_type == 'p':
            self.delete_instance('XN')
            remove_pins = ['BN', 'CTRL']

        # Remove unnecessary pins
        for p in remove_pins:
            self.remove_pin(p)