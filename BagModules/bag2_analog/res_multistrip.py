# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__res_multistrip(Module):
    """Module for library bag2_analog cell res_multistrip.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'res_multistrip.yaml'))


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
            num_unit = 'Number of units in the string',
            w = 'Primitive resistor width',
            l = 'Primitive resistor length',
            intent = 'Primitive resistor intent'
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
        w = params['w']
        l = params['l']
        intent = params['intent']
        num_unit = params['num_unit']

        if num_unit > 1:
            suffix = f'<{num_unit-1}:0>'
            suffix_short = f'<{num_unit-2}:0>' if num_unit > 2 else '<0>'
            minus_conn = f'mid{suffix_short},MINUS'
            plus_conn = f'PLUS,mid{suffix_short}'
            self.array_instance('XR', [f'XR{suffix}'], [dict(MINUS=minus_conn,
                                                            PLUS=plus_conn,
                                                            BULK='BULK')])
            # Design instances
            for i in range(num_unit):
                self.instances['XR'][0].design(w=w, l=l, intent=intent)
        else:
            self.instances['XR'].design(w=w, l=l, intent=intent)