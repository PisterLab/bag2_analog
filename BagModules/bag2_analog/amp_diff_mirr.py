# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__amp_diff_mirr(Module):
    """Module for library bag2_analog cell amp_diff_mirr.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_diff_mirr.yaml'))


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
            in_type = '"p" or "n" for NMOS or PMOS input pair',
            l_dict = 'Dictionary of channel lengths',
            w_dict = 'Dictionary of channel widths',
            seg_dict = 'Dictionary of number of fingers',
            th_dict = 'Dictionary of device intents'
            # mirr_params = 'Mirror parameters',
            # diffpair_params = 'Input differential pair and tail parameters.'
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
        l_dict = params['l_dict']
        w_dict = params['w_dict']
        seg_dict = params['seg_dict']
        th_dict = params['th_dict']
        diffpair_params = dict(lch_dict=l_dict,
                               w_dict=w_dict,
                               seg_dict=seg_dict,
                               th_dict=th_dict)
        mirror_params = dict(device_params=dict(l=l_dict['load'],
                                                w=w_dict['load'],
                                                intent=th_dict['load']),
                             seg_in=seg_dict['load'],
                             seg_out_list=[seg_dict['load']])

        # diffpair_params = params['diffpair_params']
        # mirror_params = params['mirr_params']

        assert len(mirror_params['seg_out_list'])==1, f'Mirror should have only 1 output device'

        # Adjusting masters and connections for input pair type (default n-type)
        if in_type == 'p':
            self.replace_instance_master(inst_name='XDIFFPAIR',
                                         lib_name='bag2_analog',
                                         cell_name='diffpair_p')
            self.replace_instance_master(inst_name='XLOAD',
                                         lib_name='bag2_analog',
                                         cell_name='mirror_n')

            diffpair_conn = dict(VINP='VINN',
                                 VINN='VINP',
                                 VOUTP='VOUTX',
                                 VOUTN='VOUT',
                                 VGTAIL='VGTAIL',
                                 VDD='VDD')

            mirror_conn = {'s_in': 'VSS',
                           's_out':'VSS',
                           'in':'VOUTX',
                           'out':'VOUT',
                           'VSS':'VSS'}

            for pin, net in diffpair_conn.items():
                self.reconnect_instance_terminal('XDIFFPAIR',
                                                  pin, net)
            for pin, net in mirror_conn.items():
                self.reconnect_instance_terminal('XLOAD',
                                                 pin, net)

        # Design instances
        self.instances['XDIFFPAIR'].design(**diffpair_params)
        self.instances['XLOAD'].design(**mirror_params)