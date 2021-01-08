# -*- coding: utf-8 -*-

from typing import Dict, Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__constant_gm(Module):
    """Module for library bag2_analog cell constant_gm.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'constant_gm.yaml'))


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
            res_side = '"n" or "p" to indicate on which side the the resistor is placed',
            l_dict = 'Dictionary of channel and resistor lengths. Keys n, p, and res',
            w_dict = 'Dictionary of channel and resistor widhts',
            seg_dict = 'Dictionary of number of segments for transistors and resistors',
            th_dict = 'Dictionary of intent for ransistors and resistors',
            device_mult = 'Multiplier for device touching the resistor',
            bulk_conn = 'Bulk connection for the resistor'
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
        res_side = params['res_side']
        bulk_conn = params['bulk_conn']

        l_dict = params['l_dict']
        w_dict = params['w_dict']
        seg_dict = params['seg_dict']
        th_dict = params['th_dict']
        device_mult = params['device_mult']

        n_params = dict(seg_in=seg_dict['n'],
                        seg_out_list=[device_mult*seg_dict['n'] if res_side=='n' else seg_dict['n']],
                        device_params=dict(l=l_dict['n'],
                                           w=w_dict['n'],
                                           intent=th_dict['n']))
        p_params = dict(seg_in=seg_dict['p'],
                        seg_out_list=[device_mult*seg_dict['p'] if res_side=='p' else seg_dict['p']],
                        device_params=dict(l=l_dict['p'],
                                           w=w_dict['p'],
                                           intent=th_dict['p']))

        res_params = dict(w=w_dict['res'],
                          l=l_dict['res'],
                          intent=th_dict['res'],
                          num_unit=seg_dict['res'])

        assert bulk_conn in ('VSS', 'VDD'), f'Bulk connection should be to VSS or VDD (not {bulk_conn})'

        # Designing instances
        self.instances['XN'].design(**n_params)
        self.instances['XP'].design(**p_params)
        self.instances['XRES'].design(**res_params)

        if res_side == 'p':
            self.reconnect_instance_terminal('XP', 's_out', 'VX')
            self.reconnect_instance_terminal('XRES', 'MINUS', 'VDD')
        elif res_side == 'n':
            self.reconnect_instance_terminal('XN', 's_out', 'VX')
        else:
            raise ValueError(f"Resistor should be connected to either 'p' or 'n', not {res_side}")

        self.reconnect_instance_terminal('XRES', 'BULK', bulk_conn)