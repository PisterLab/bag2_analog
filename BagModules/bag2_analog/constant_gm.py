# -*- coding: utf-8 -*-

from typing import Dict

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
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            res_side = '"n" or "p" to indicate on which side the the resistor is placed',
            res_params = 'Resistor parameters',
            mirr_n_params = 'NMOS device parameters',
            mirr_p_params = 'PMOS device parameters'
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
        n_params = params['mirr_n_params']
        p_params = params['mirr_p_params']
        res_params = params['res_params']
        res_side = params['res_side']

        num_src = len(n_params['seg_out_list']) - 1
        num_sink = len(p_params['seg_out_list']) - 1

        assert num_src == num_sink == 0, 'This constant gm is not meant to include any additional source/sink devices beyond the initial feedback loop.'

        # Designing instances
        self.instances['XN'].design(**n_params)
        self.instances['XP'].design(**p_params)
        self.instances['XRES'].parameters = res_params
        # self.instances['XRES'].parameters['res_val'] = res_params['res_val']
        # self.instances['XRES'].design(**res_params)

        # Arraying the resistor if necessary
        # if num_res > 1:
        #     plus_conn = ','.join(['VX'] + [f'r<{i}>' for i in range(num_res-1)])
        #     bot_conn = 'VDD' if res_side == 'p' else 'VSS'
        #     minus_conn = ','.join([f'r<{i}>' for i in range(num_res-1)] + [bot_conn])
        #     self.array_instance('XRES', [f'XRES<{num_res-1}:0>'], [dict(PLUS=plus_conn,
        #                                                               MINUS=minus_conn)])

        if res_side == 'p':
            self.reconnect_instance_terminal('XP', 's_out', 'VX')
            # if num_res == 1:
            self.reconnect_instance_terminal('XRES', 'MINUS', 'VDD')
        elif res_side == 'n':
            self.reconnect_instance_terminal('XN', 's_out', 'VX')
        else:
            raise ValueError(f"Resistor should be connected to either 'p' or 'n', not {res_side}")

