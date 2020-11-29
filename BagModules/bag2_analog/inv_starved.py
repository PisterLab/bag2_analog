# -*- coding: utf-8 -*-

from typing import Dict, Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__inv_starved(Module):
    """Module for library bag2_analog cell inv_starved.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'inv_starved.yaml'))


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
            ctrl_groups_p = 'List of bit groupings for PMOS control, i.e. [1, 2, 3] has bit0=1 device, bit1=2 devices, bit2=3 devices',
            ctrl_groups_n = 'List of bit groupings for NMOS control',
            lch_dict = 'Dictionary of channel lengths',
            wch_dict = 'Dictionary of channel widths',
            seg_dict = 'Dictionary of device segments',
            th_dict = 'Dictionary of device flavors'
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
        ctrl_groups_p = params['ctrl_groups_p']
        ctrl_groups_n = params['ctrl_groups_n']
        lch_dict = params['lch_dict']
        wch_dict = params['wch_dict']
        seg_dict = params['seg_dict']
        th_dict = params['th_dict']

        num_bits_p = len(ctrl_groups_p)
        num_bits_n = len(ctrl_groups_n)
        num_devices_p = sum(ctrl_groups_p)
        num_devices_n = sum(ctrl_groups_n)

        # Design instances
        dev_map = dict(p_inner = 'XP_INNER',
                       n_inner = 'XN_INNER')
        for key,name in dev_map.items():
            device_params = dict(l=lch_dict[key],
                                 w=wch_dict[key],
                                 nf=seg_dict[key],
                                 intent=th_dict[key])
            self.instances[name].design(**device_params)

        # Array instances as necessary
        p_outer_key = 'p_outer'
        n_outer_key = 'n_outer'

        p_outer_params = dict(l=lch_dict[p_outer_key],
                              w=wch_dict[p_outer_key],
                              nf=seg_dict[p_outer_key],
                              intent=th_dict[p_outer_key])
        n_outer_params = dict(l=lch_dict[n_outer_key],
                              w=wch_dict[n_outer_key],
                              nf=seg_dict[n_outer_key],
                              intent=th_dict[n_outer_key])
        if num_bits_p > 1:
            vgp_conn = ','.join([f'<*{ctrl_groups_p[i]}>bpb<{i}>' for i in range(num_bits_p)])
            self.array_instance('XP_OUTER', [f'XP_OUTER<{num_devices_p-1}:0>'],
                                [dict(G=vgp_conn)])
            self.rename_pin('bpb', f'bpb<{num_bits_p-1}:0>')
            self.instances['XP_OUTER'][0].design(**p_outer_params)
        else:
            self.instances['XP_OUTER'].design(**p_outer_params)

        if num_bits_n > 1:
            vgn_conn = ','.join([f'<*{ctrl_groups_n[i]}>bn<{i}>' for i in range(num_bits_n)])
            self.array_instance('XN_OUTER', [f'XN_OUTER<{num_devices_n-1}:0>'],
                                [dict(G=vgn_conn)])
            self.rename_pin('bn', f'bn<{num_bits_n-1}:0>')
            self.instances['XN_OUTER'][0].design(**n_outer_params)
        else:
            self.instances['XN_OUTER'].design(**n_outer_params)