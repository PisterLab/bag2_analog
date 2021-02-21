# -*- coding: utf-8 -*-

from typing import Dict, Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__res_trim_series(Module):
    """Module for library bag2_analog cell res_trim_series.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'res_trim_series.yaml'))


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
            res_params = 'Single multistrip resistor parameters',
            sw_params = 'Switch parameters. All switches are identical here.',
            res_groupings = 'List of number of consecutive units for each switch to wrap around. e.g. [1, 2, 3] = switch 0 wraps around 1 resistor, switch 1 wraps around 2 in series, etc.',
            bulk_conn = 'Net to connect to the resistor bulk terminal'
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
        res_params = params['res_params']
        base_num_unit = res_params['num_unit']
        sw_params = params['sw_params']
        res_groupings = params['res_groupings']

        bulk_conn = params['bulk_conn']

        num_res = sum(res_groupings)
        num_sw = len(res_groupings)

        ### Resistors
        self.instances['XRBASE'].design(**res_params)
        self.reconnect_instance_terminal('XRBASE', 'BULK', bulk_conn)

        # Arraying and connecting the resistors in a string
        conn_dict_list = []
        for i in range(num_sw):
            plus_conn = f'mid<{i}>'
            minus_conn = 'Z' if i==num_sw-1 else f'mid<{i+1}>'
            conn_dict_list.append(dict(PLUS=plus_conn, MINUS=minus_conn, BULK=bulk_conn))

        self.array_instance('XR', [f'XR<{i}>' for i in range(num_sw)], conn_dict_list)

        # Designing the multistrip resistors which will potentially be shorted out
        multistrip_params = res_params.copy()
        for i in range(num_sw):
            multistrip_params.update(num_unit=base_num_unit*res_groupings[i])
            self.instances['XR'][i].design(**multistrip_params)

        if bulk_conn in ('VDD', 'VSS'):
            self.remove_pin('BULK')
        elif bulk_conn != 'BULK':
            self.rename_pin('BULK', bulk_conn)

        ### Switches
        # Polarity vs. switches reversed because we want the resistance to increase with increasing code
        has_ctrlb = sw_params['mos_type'] != 'p'
        has_ctrl = sw_params['mos_type'] != 'n'

        if not has_ctrlb:
            self.remove_pin('CTRLb')
        
        if not has_ctrl:
            self.remove_pin('CTRL')

        # Arraying and wiring up the switches
        if num_sw > 1:
            self.array_instance('XSW', [f'XSW<{num_sw-1}:0>'], [dict(D=f'mid<{num_sw-1}:0>',
                                                                     S=f'Z,mid<{num_sw-1}:1>',
                                                                     BP='VDD',
                                                                     BN='VSS',
                                                                     CTRL=f'CTRLb<{num_sw-1}:0>',
                                                                     CTRLb=f'CTRL<{num_sw-1}:0>')])
            self.instances['XSW'][0].design(**sw_params)
            if has_ctrl:
                self.rename_pin('CTRL', f'CTRL<{num_sw-1}:0>')
            if has_ctrlb:
                self.rename_pin('CTRLb', f'CTRLb<{num_sw-1}:0>')
        elif num_sw == 1:
            self.instances['XSW'].design(**sw_params)
            self.reconnect_instance_terminal('XSW', 'D', 'mid<0>')

        if num_sw == 0:
            self.delete_instance('XSW')
            self.delete_instance('XR')
            self.reconnect_instance_terminal('XRBASE', 'MINUS', 'Z')
            self.remove_pin('CTRL')
            self.remove_pin('CTRLb')