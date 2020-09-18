# -*- coding: utf-8 -*-

from typing import Mapping, Any

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__amp_inv(Module):
    """Module for library bag2_analog cell amp_inv.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_inv.yaml'))


    def __init__(self, database, parent=None, prj=None, **kwargs):
        Module.__init__(self, database, self.yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls) -> Mapping[str,str]:
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            lch = 'Channel length (m)',
            w_dict = 'Transistor width dictionary.',
            th_dict = 'Transistor threshold dictionary',
            seg_dict = 'Transistor number of segments dictionary.',
        )

    @classmethod
    def get_default_params_info(cls) -> Mapping[str,Any]:
        return dict(
                seg_dict = dict(p=1, n=1)
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
        tran_info_list = [('XP', 'p'), ('XN', 'n')]
        for inst_name, inst_type in tran_info_list:
            w = params['w_dict'][inst_type]
            th = params['th_dict'][inst_type]
            seg = params['seg_dict'][inst_type]
            lch = params['lch']
            self.instances[inst_name].design(w=w, l=lch, nf=seg, intent=th)