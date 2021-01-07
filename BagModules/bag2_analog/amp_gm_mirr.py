# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__amp_gm_mirr(Module):
    """Module for library bag2_analog cell amp_gm_mirr.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_gm_mirr.yaml'))


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
            in_type = '"p" or "n" for NMOS or PMOS input pair',
            mirr_params_dict = 'The output-facing load is key "load_out", the non-output-facing load is "load", and the flipped mirror is key "flip_out"',
            diffpair_params = 'Input differential pair and tail parameters'
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
        in_type = params['in_type']
        mirr_params_dict = params['mirr_params_dict']
        diffpair_params = params['diffpair_params']

        for mirr_params in mirr_params_dict.values():
            assert len(mirr_params['seg_out_list'])==1, f'Mirrors should have only 1 output device'

        # Change input pair type as necessary
        if in_type.lower() == 'p':
            self.replace_instance_master(inst_name='XDIFFPAIR',
                                         lib_name='bag2_analog',
                                         cell_name='diffpair_p')
            self.replace_instance_master(inst_name='XMIRR_LOADOUT',
                                         lib_name='bag2_analog',
                                         cell_name='mirror_n')
            self.replace_instance_master(inst_name='XMIRR_LOAD',
                                         lib_name='bag2_analog',
                                         cell_name='mirror_n')
            self.replace_instance_master(inst_name='XMIRR_FLIPOUT',
                                         lib_name='bag2_analog',
                                         cell_name='mirror_p')

            diffpair_conn = dict(VINP='VINP',
                                 VINN='VINN',
                                 VOUTP='VOUT1A',
                                 VOUTN='VOUT1B',
                                 VGTAIL='VGTAIL',
                                 VDD='VDD')

            loadout_conn = {'s_in': 'VSS',
                            's_out': 'VSS',
                            'in': 'VOUT1B',
                            'out': 'VOUT',
                            'VSS': 'VSS'}
            load_conn = {'s_in': 'VSS',
                            's_out': 'VSS',
                            'in': 'VOUT1A',
                            'out': 'VOUT2A',
                            'VSS': 'VSS'}
            flipout_conn = {'s_in': 'VDD',
                            's_out': 'VDD',
                            'in': 'VOUT2A',
                            'out': 'VOUT',
                            'VDD': 'VDD'}

            for pin, net in diffpair_conn.items():
                self.reconnect_instance_terminal('XDIFFPAIR', pin, net)

            for pin, net in loadout_conn.items():
                self.reconnect_instance_terminal('XMIRR_LOADOUT', pin, net)

            for pin, net in load_conn.items():
                self.reconnect_instance_terminal('XMIRR_LOAD', pin, net)

            for pin, net in flipout_conn.items():
                self.reconnect_instance_terminal('XMIRR_FLIPOUT', pin, net)
        elif in_type.lower() != 'n':
            raise ValueError(f"in_type {in_type} should be 'p' or 'n'")

        # Design instances
        self.instances['XDIFFPAIR'].design(**diffpair_params)
        self.instances['XMIRR_LOADOUT'].design(**(mirr_params_dict['load_out']))
        self.instances['XMIRR_LOAD'].design(**(mirr_params_dict['load']))
        self.instances['XMIRR_FLIPOUT'].design(**(mirr_params_dict['flip_out']))