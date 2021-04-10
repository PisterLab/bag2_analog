# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__dac_r2r(Module):
    """Module for library bag2_analog cell dac_r2r.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'dac_r2r.yaml'))


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
            r2r_params = 'Parameters for a R2R resistor core.',
            buf_params_list = 'List of inverter chain parameters (ordering matches bit, i.e. LSB is buffered with index 0)',
            num_bits = 'Number of bits.'
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
        num_bits = params['num_bits']
        r2r_params = params['r2r_params']
        buf_params_list = params['buf_params_list']

        assert num_bits > 0, f'Number of bits {num_bits} must be > 0'

        # Design instances and change pin names as necessary
        self.instances['XRES'].design(num_bits=num_bits, **r2r_params)

        if num_bits > 1:
            self.rename_pin('B', f'B<{num_bits-1}:0>')
            buf_insts = [f'XBUF<{i}>' for i in range(num_bits)]
            buf_conns = [{'in': f'B<{i}>',
                          'out' : f'B_buf<{i}>',
                          'VDD' : 'VDD',
                          'VSS' : 'VSS'} for i in range(num_bits)]
            self.array_instance('XBUF', buf_insts, buf_conns)
            for i in range(num_bits):
                self.instances['XBUF'][i].design(dual_output=False, **(buf_params_list[i]))
            self.reconnect_instance_terminal('XRES', f'B<{num_bits-1}:0>', f'B_buf<{num_bits-1}:0>')
        else:
            self.instances['XBUF'].design(dual_output=False, **(buf_params_list[0]))
            self.reconnect_instance_terminal('XRES', 'B', 'B_buf')