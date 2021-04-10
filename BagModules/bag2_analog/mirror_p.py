# -*- coding: utf-8 -*-

from typing import Mapping, Any

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__mirror_p(Module):
    """Module for library bag2_analog cell mirror_p.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'mirror_p.yaml'))


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
            device_params = 'Transistor parameters except for number of segments. For matching, all transistors are identical save for number of segments.',
            seg_in = 'Number of segments of input device.',
            seg_out_list = 'List of number of segments for output devices.'
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
        seg_out_list = params['seg_out_list']
        num_out = len(seg_out_list)
        assert num_out >= 1, f'Number of output devices {num_out} must be >= 1'

        device_params = params['device_params']
        in_params = device_params.copy()

        self.instances['XIN'].design(nf=params['seg_in'], **in_params)

        if num_out > 1:
            self.array_instance('XOUT', [f'XOUT<{i}>' for i in range(num_out)],
                                [dict(D=f'out<{i}>', S=f's_out<{i}>') for i in range(num_out)])
            self.rename_pin('out', f'out<{num_out-1}:0>')
            self.rename_pin('s_out', f's_out<{num_out-1}:0>')
            
            for i in range(num_out):
                out_params = device_params.copy()
                out_params['nf'] = seg_out_list[i]
                self.instances['XOUT'][i].design(**out_params)
        else:
            out_params = device_params.copy()
            out_params['nf'] = seg_out_list[0]
            self.instances['XOUT'].design(**out_params)