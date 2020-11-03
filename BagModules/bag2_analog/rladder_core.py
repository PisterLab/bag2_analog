# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__rladder_core(Module):
    """Module for library bag2_analog cell rladder_core.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'rladder_core.yaml'))


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
            num_out = 'Number of outputs.',
            res_params = 'Resistor unit parameters.'
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
        num_out = params['num_out']
        res_params = params['res_params']

        assert num_out >= 1, f'Number of outputs {num_out} must be >= 1'

        # Design unit
        self.instances['XR'].parameters = res_params

        print("*** WARNING *** (rladder_core) Check generated ideal passive values")

        # Array instance
        suffix = f'<{num_out-1}:0>'
        suffix_short = f'<{num_out-1}:1>' if num_out > 2 else '<1>'
        minus_conn = f'out{suffix}'
        plus_conn = f'VDD,out{suffix_short}'
        self.array_instance('XR', [f'XR{suffix}'], [dict(MINUS=minus_conn,
                                                        PLUS=plus_conn)])
        self.rename_pin('out<0>', f'out{suffix}')