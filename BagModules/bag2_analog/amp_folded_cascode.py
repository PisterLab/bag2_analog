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
            in_type = 'n or p for NMOS or PMOS input pair',
            diffpair_params = 'Diffpair parameters',
            cascode_params = 'cascode_conn parameters',
            diff_out = 'True for single-ended output, False for differential',
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
        diffpair_params = params['diffpair_params']
        cascode_params = params['cascode_params']
        diff_out = params['diff_out']

        # Design differential pair
        if in_type == 'p':
            self.replace_instance_master(inst_name='XDIFFPAIR',
                                         lib_name='bag2_analog',
                                         cell_name='diffpair_p')
            diffpair_conn = dict(VINP='VINN',
                                 VINN='VINP',
                                 VOUTP='VNMIDA',
                                 VOUTN='VNMIDB',
                                 VGTAIL='VGTAIL',
                                 VDD='VDD')
            
            for pin, net in diffpair_conn.items():
                self.reconnect_instance_terminal('XDIFFPAIR', pin, net)

        self.instances['XDIFFPAIR'].design(**diffpair_params)

        # Design cascode
        p_stack = cascode_params['p_params']['stack']
        n_stack = cascode_params['n_params']['stack']

        assert p_stack == 2, f'Currently only supports P-stack of 2 transistors (currently {p_stack})'
        assert n_stack == 2, f'Currently only supports N-stack of 2 transistors (currently {n_stack})'

        self.instances['XCASCODE'].design(diff_out=diff_out, **cascode_params)

        # Single-ended vs. differential output
        if not diff_out:
            self.remove_pin('VOUTN')
            self.remove_pin('VOUTP')
            self.reconnect_instance_terminal('XCASCODE', 'DB', 'VOUT')
        else:
            self.remove_pin('VOUT')

        # Renaming gate pins as necessary
        vgp_pin = f'VGP<1:0>'
        vgn_pin = f'VGN<1:0>'

        self.reconnect_instance_terminal('XCASCODE', 'GP<1:0>', vgp_pin)
        self.reconnect_instance_terminal('XCASCODE', 'GN<1:0>', vgn_pin)

        # Cascode intermediate connections
        n_drain_conn = cascode_params['n_drain_conn']
        p_drain_conn = cascode_params['p_drain_conn']
        self.reconnect_instance_terminal('XCASCODE', 'DPB<0>', 'VPMIDB')
        self.reconnect_instance_terminal('XCASCODE', 'DNB<0>', 'VNMIDB')
        
        # Remove unconnected mid-connection pins
        if in_type == 'n' and n_drain_conn[0]:
            self.remove_pin('VNMIDA')
            self.reconnect_instance_terminal('XCASCODE', 'DPA<0>', 'VPMIDA')
        if in_type == 'p' and p_drain_conn[0]:
            self.remove_pin('VPMIDA')
            self.reconnect_instance_terminal('XCASCODE', 'DNA<0>', 'VNMIDA')
