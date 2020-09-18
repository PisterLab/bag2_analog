# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__cascode_n(Module):
    """Module for library bag2_analog cell cascode_n.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'cascode_n.yaml'))


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
            lch = 'Channel length',
            w_dict = 'Dictionary of device widths',
            seg_dict = 'Dictionary of segments per device',
            th_dict = 'Dictionary of threshold flavors'
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
        name_mapping = {'XN<0>':'outer', 'XN<1>':'inner'}

        lch = params['lch']

        for device_name, dict_key in name_mapping.items():
            w = params['w_dict'][dict_key]
            seg = params['seg_dict'][dict_key]
            intent = params['th_dict'][dict_key]
            self.instances[device_name].design(w=w, l=lch, nf=seg, intent=intent)