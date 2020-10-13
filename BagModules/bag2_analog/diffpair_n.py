# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__diffpair_n(Module):
    """Module for library bag2_analog cell diffpair_n.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'diffpair_n.yaml'))


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
            lch_dict = 'Dictionray of device channel lengths',
            w_dict = 'Dictionary of device widths',
            seg_dict = 'Dictionary of segments per device',
            th_dict = 'Dictionary of threshold flavors'
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
        device_map = dict(
            XINA='in',
            XINB='in',
            XTAIL='tail')

        for device_name, key_name in device_map.items():
            w = params['w_dict'][key_name]
            seg = params['seg_dict'][key_name]
            intent = params['th_dict'][key_name]
            lch = params['lch_dict'][key_name]

            self.instances[device_name].design(w=w, l=lch, nf=seg, intent=intent)