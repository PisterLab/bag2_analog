# -*- coding: utf-8 -*-

from typing import Mapping, Any

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__nmos4_astack(Module):
    """Module for library bag2_analog cell nmos4_astack.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'nmos4_astack.yaml'))


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
            lch_list = 'Channel length in resolution units. Outside-in ordering.',
            w_list = 'Channel width in resolution units. Outside in ordering.',
            stack = 'Number of stacked devices',
            intent_list = 'Threshold flavor. Ordering is outside in.',
            seg_list = 'Number of segments per device. Ordering is outside in.',
            export_mid = 'True to export intermediate nodes',
        )

    def design(self, **params) -> None:
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
        lch_list = params['lch_list']
        w_list = params['w_list']
        stack = params['stack']
        intent_list = params['intent_list']
        seg_list = params['seg_list']
        export_mid = params['export_mid']

        assert len(lch_list) == len(w_list) == len(intent_list) == len(seg_list) == stack, f'Lists length must be equal to number of devices in stack.'

        # Array instances
        if stack > 1:
            device_names = []
            device_conns = []
            for i in range(stack):
                device_names = device_names + [f'XN<{i}>']
                device_conns = device_conns + [dict(G=f'G<{i}>',
                                                   S='S' if i==0 else f'm<{i-1}>',
                                                   D='D' if i==stack-1 else f'm<{i}>',
                                                   B='B')]
            self.array_instance('XN', device_names, device_conns)

        # Designing instances
        if stack > 1:
            for i in range(stack):
                w = w_list[i]
                lch = lch_list[i]
                intent = intent_list[i]
                seg = seg_list[i]
                self.instances['XN'][i].design(w=w, l=lch, nf=seg, intent=intent)
        else:
            w = w_list[0]
            lch = lch_list[0]
            intent = intent_list[0]
            seg = seg_list[0]
            self.instances['XN'].design(w=w, l=lch, nf=seg, intent=intent)

        # Renaming and exporting pins
        if stack > 1:
            self.rename_pin('G', f'G<{stack-1}:0>')

            if export_mid:
                suffix_mid = f'<0>' if stack == 2 else f'<{stack-2}:0>'
                self.add_pin(f'm{suffix_mid}', 'inputOutput')