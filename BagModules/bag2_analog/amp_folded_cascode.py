# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__amp_folded_cascode(Module):
    """Module for library bag2_analog cell amp_folded_cascode.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_folded_cascode.yaml'))


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
            lch = 'Channel length (m)',
            w_dict = 'Transistor width dictionary.',
            th_dict = 'Transistor threshold dictionary',
            seg_dict = 'Transistor number of segments dictionary.',
            in_type = 'String describing the input pair. "n" or "p".',
            diff_out = 'True for a differential output, False for single-ended.',
            export_mid = 'True to export cascode intermediate nodes.',
            bias_dict = 'Dictionary with key:value of device designation: "mirr", "hs_mirr", "ext"' + \
                        'for mirror connected, high-swing mirror, or externally biased'
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
        lch = params['lch']
        w_dict = params['w_dict']
        th_dict = params['th_dict']
        seg_dict = params['seg_dict']
        in_type = params['in_type']
        diff_out = params['diff_out']
        export_mid = params['export_mid']
        bias_dict = params['bias_dict']

        ### Separating out parameters
        cascode_n_params = dict(lch=lch,
            w_dict={'outer': w_dict['outer_n'],
                    'inner': w_dict['inner_n']},
            seg_dict={'outer': seg_dict['outer_n'],
                    'inner': seg_dict['inner_n']},
            th_dict={'outer': th_dict['outer_n'],
                    'inner': th_dict['inner_n']})

        cascode_p_params = dict(lch=lch,
            w_dict={'outer': w_dict['outer_p'],
                    'inner': w_dict['inner_p']},
            seg_dict={'outer': seg_dict['outer_p'],
                    'inner': seg_dict['inner_p']},
            th_dict={'outer': th_dict['outer_p'],
                    'inner': th_dict['inner_p']})

        diffpair_params = dict(lch=lch,
            w_dict={'in': w_dict['in'],
                    'tail': w_dict['tail']},
            seg_dict={'in': seg_dict['in'],
                    'tail': seg_dict['tail']},
            th_dict={'in': th_dict['in'],
                    'tail': th_dict['tail']})

        ### Differential vs. single-ended output
        if diff_out:
            self.remove_pin('VOUT')
        else:
            self.remove_pin('VOUTP')
            self.remove_pin('VOUTN')
            self.reconnect_instance_terminal('XCASCODE', 'VOUTA', 'VOUT')
            self.reconnect_instance_terminal('XCASCODE', 'VOUTA', 'VOUT')

        ### Wiring up cascode biasing (only used for single-ended output)
        # Currently only supports wiring, no additional components
        g_pin_dict = dict(outer='VN<0>' if in_type=='n' else 'VP<0>',
            inner='VN<1>' if in_type=='n' else 'VP<1>')
        d_pin_dict = dict(outer='VNMIDB' if in_type=='n' else 'VPMIDB',
            inner='VOUTB')

        # Keep track of which pins aren't independent and shouldn't be pinned out
        mid_remove_pins = []
        if not diff_out:
            for device, bias_type in bias_dict.items():
                g_net = g_pin_dict[device]
                if bias_type == 'mirr':
                    bias_pin = d_pin_dict[device]
                    
                    if device == 'outer':
                        mid_remove_pins.append(bias_pin)
                elif bias_type == 'hs_mirror':
                    if 'inner' in device:
                        raise ValueError("Inner devices can't have high swing biasing.")
                    bias_pin = 'VOUTN'

                self.reconnect_instance_terminal('XCASCODE', bias_pin, g_net)
                mid_remove_pins.append(g_net)

        ### Export intermediate pins if necessary
        if not export_mid:
            mid_remove_pins = [f'V{np}MID{lr}' for np in ('N', 'P') for lr in ('A', 'B')]
        
        for p in mid_remove_pins:
            self.remove_pin(p)

        ### NMOS vs. PMOS input pair
        if in_type.lower() == 'p':
            # Replace the instance master
            self.replace_instance_master(inst_name='XDIFFPAIR',
                lib_name='bag2_analog',
                cell_name='diffpair_p')

            # Fix the wiring on the diff pair
            diffpair_conn = dict(VINP='VINP',
                VINN='VINN',
                VOUTP='VNMIDA',
                VOUTN='VNMIDB',
                VBTAIL='VBTAIL',
                VDD='VDD')

            for pin, net in diffpair_conn.items():
                self.reconnect_instance_terminal('XDIFFPAIR',
                    pin, net)

        ### Design instances
        self.instances['XDIFFPAIR'].design(**diffpair_params)
        self.instances['XCASCODE'].design(p_params=cascode_p_params, 
            n_params=cascode_n_params)