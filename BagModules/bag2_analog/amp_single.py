# -*- coding: utf-8 -*-

from typing import Dict, Mapping

import os
import pkg_resources

from bag.design.module import Module
from scripts_char.misc import *


# noinspection PyPep8Naming
class bag2_analog__amp_single(Module):
    """Module for library bag2_analog cell amp_single.
    This is intended to be the core for single-transistor amplifiers.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'amp_single.yaml'))


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
            p_params = 'P-side parameters of the stack (see pmos4_astack)',
            n_params = 'N-side parameters of the stack (see nmos4_astack)',
            in_conn = 'Net to connect to the input. This will be renamed to VINP/N. DN<0> and GN<0> are the drain and gate of the bottom NMOS. DP<0> and GP<0> are the drain and gate of the top PMOS',
            out_conn = 'Net to connect to the output. This will be renamed to VOUT. DN<0> is the drain of the bottom NMOS. DP<0> is the drain of the top PMOS',
            inv_out = 'True if the output is inverted wrt the input (entirely for superficial purposes)',
            export_mid = 'True to export all intermediate drain nodes, false to export only those which are tied to the input or output'
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
        p_params = params['p_params']
        n_params = params['n_params']

        n_stack = n_params['stack']
        p_stack = p_params['stack']

        assert (n_stack > 0) or (p_stack > 0), f'nstack {n_stack} or pstack {p_stack} have at least one device'

        inv_out = params['inv_out']
        vin_pin = 'VINN' if inv_out else 'VINP'
        if inv_out:
            self.rename_pin('VINP', vin_pin)

        in_conn = params['in_conn']
        out_conn = params['out_conn']
        export_mid = params['export_mid']

        # Assumes that the NMOS and PMOS middlemost drains are shorted
        if in_conn in (f'DP<{p_stack-1}>', f'DN<{n_stack-1}>'):
            in_conn = 'DMID'
            self.remove_pin('DMID')


        if out_conn in (f'DP<{p_stack-1}>', f'DN<{n_stack-1}>'):
            out_conn = 'DMID'
            self.remove_pin('DMID')

        ### NMOS
        if n_stack > 0:
            # Design instance
            self.instances['XN'].design(**n_params, export_mid=True)

            # Connect gate
            gn_conn_list = [f'GN<{i}>' for i in range(n_stack)]
            for i, gn_conn in enumerate(gn_conn_list):
                if gn_conn == in_conn:
                    gn_conn_list[i] = vin_pin
            gn_net = ','.join(gn_conn_list[::-1])
            gn_suffix = f'<{n_stack-1}:0>' if n_stack > 1 else '<0>'
            self.reconnect_instance_terminal('XN', f'G{gn_suffix}', gn_net)

            # Adjust cell's gate pins
            gn_idx_list = [i for i, gn_conn in enumerate(gn_conn_list) if gn_conn==f'GN<{i}>']
            gn_pin = bus_net(gn_idx_list, 'GN')
            self.rename_pin('GN<0>', gn_pin)

            # Connect intermediate drains
            if n_stack > 1:
                mn_conn_list = [f'DN<{i}>' for i in range(n_stack-1)]
                for i, mn_conn in enumerate(mn_conn_list):
                    if mn_conn == in_conn:
                        mn_conn_list[i] = vin_pin
                    if mn_conn == out_conn:
                        mn_conn_list[i] = 'VOUT'
                mn_net = ','.join(mn_conn_list[::-1])
                mn_suffix = f'<{n_stack-2}:0>' if n_stack > 2 else '<0>'
                self.reconnect_instance_terminal('XN', f'm{mn_suffix}', mn_net)

                # Adjust cell's intermediate drain pins
                mn_idx_list = [i for i, mn_conn in enumerate(mn_conn_list) if mn_conn==f'DN<{i}>']
                dn_pin = bus_net(mn_idx_list, 'DN')
                if len(mn_idx_list) > 0:
                    self.rename_pin('DN<0>', dn_pin)
                else:
                    self.remove_pin('DN<0>')
            else:
                self.remove_pin('DN<0>')

            # Connect final drain
            dn_conn = 'VDD' if p_stack == 0 else f'DMID'
            if dn_conn == in_conn:
                dn_conn = vin_pin
            if dn_conn == out_conn:
                dn_conn = 'VOUT'
            self.reconnect_instance_terminal('XN', 'D', dn_conn)

        else:
            # Remove if it isn't necessary
            self.delete_instance('XN')
            self.remove_pin('GN<0>')
            self.remove_pin('DN<0>')
            self.reconnect_instance_terminal('XP', 'D', 'VSS')
            assert in_conn != 'DMID', "Deleted NMOS stack, input is shorted to ground"
            assert out_conn != 'DMID', "Deleted NMOS stack, output is shorted to ground"
        
        ### PMOS
        if p_stack > 0:
            # Design instance
            self.instances['XP'].design(**p_params, export_mid=True)

            # Connect gate
            gp_conn_list = [f'GP<{i}>' for i in range(p_stack)]
            for i, gp_conn in enumerate(gp_conn_list):
                if gp_conn == in_conn:
                    gp_conn_list[i] = vin_pin
            gp_net = ','.join(gp_conn_list[::-1])
            gp_suffix = f'<{p_stack-1}:0>' if p_stack > 1 else '<0>'
            self.reconnect_instance_terminal('XP', f'G{gp_suffix}', gp_net)

            # Adjust cell's gate pins
            gp_idx_list = [i for i, gp_conn in enumerate(gp_conn_list) if gp_conn==f'GP<{i}>']
            gp_pin = bus_net(gp_idx_list, 'GP')
            self.rename_pin('GP<0>', gp_pin)

            # Connect intermediate drains
            if p_stack > 1:
                mp_conn_list = [f'DP<{i}>' for i in range(p_stack-1)]
                for i, mp_conn in enumerate(mp_conn_list):
                    if mp_conn == in_conn:
                        mp_conn_list[i] = vin_pin
                    if mp_conn == out_conn:
                        mp_conn_list[i] = 'VOUT'
                mp_net = ','.join(mp_conn_list[::-1])
                mp_suffix = f'<{p_stack-2}:0>' if p_stack > 2 else '<0>'
                self.reconnect_instance_terminal('XP', f'm{mp_suffix}', mp_net)

                # Adjust cell's intermediate drain pins
                mp_idx_list = [i for i, mp_conn in enumerate(mp_conn_list) if mp_conn==f'DP<{i}>']
                dp_pin = bus_net(mp_idx_list, 'DP')
                if len(mp_idx_list) > 0:
                    self.rename_pin('DP<0>', dp_pin)
                else:
                    self.remove_pin('DP<0>')
            else:
                self.remove_pin('DP<0>')

            # Connect final drain
            dp_conn = 'VSS' if n_stack == 0 else f'DMID'
            if dp_conn == in_conn:
                dp_conn = vin_pin
            if dp_conn == out_conn:
                dp_conn = 'VOUT'
            self.reconnect_instance_terminal('XP', 'D', dp_conn)
        else:
            self.delete_instance('XP')
            self.remove_pin('GP<0>')
            self.remove_pin('DP<0>')
            self.reconnect_instance_terminal('XN', 'D', 'VDD')
            assert in_conn != 'DMID', "Deleted PMOS stack, input is shorted to supply"
            assert out_conn != 'DMID', "Deleted PMOS stack, output is shorted to supply"