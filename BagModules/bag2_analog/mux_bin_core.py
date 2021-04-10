# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__mux_bin_core(Module):
    """Module for library bag2_analog cell mux_bin_core.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'mux_bin_core.yaml'))


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
            num_bits = 'Number of bits',
            mos_type = '"n", "p", or "both" to indicate NMOS, PMOS, or tgate, respectively',
            unit_params = 'Unit binary mux parameters',
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
        unit_params = params['unit_params']
        mos_type = params['mos_type']
        num_bits = params['num_bits']

        num_in = 1 << num_bits
        num_units = num_in - 1

        if num_bits > 1:
            # Array instances going one layer at a time
            suffix = f'<{num_bits-1}:0>'
            inst_list = [f'XUNIT{i}<{(1<<(num_bits-i-1))-1}:0>' for i in range(num_bits)]
            conn_list = [{'VIN<1:0>' : f'VIN<{num_in-1}:0>' if i==0 else f'VMID{i-1}<{(1<<(num_bits-i))-1}:0>',
                          'S' : f'S<{i}>',
                          'Sb' : f'Sb<{i}>',
                          'VOUT' : f'VMID{i}<{(1<<(num_bits-i-1))-1}:0>' if i<(num_bits-1) else 'VOUT',
                          'VDD' : 'VDD',
                          'VSS' : 'VSS'} for i in range(num_bits)]
            self.array_instance('XUNIT', inst_list, conn_list)
            
            # Design instances
            for inst in self.instances['XUNIT']:
                inst.design(mos_type=mos_type, **unit_params)

            # Change pins as necessary
            self.rename_pin('S', f'S<{num_bits-1}:0>')
            self.rename_pin('Sb', f'Sb<{num_bits-1}:0>')
            self.rename_pin('VIN<1:0>', f'VIN<{num_in-1}:0>')

        else:
            # Design instance
            self.instances['XUNIT'].design(mos_type=mos_type, **unit_params)