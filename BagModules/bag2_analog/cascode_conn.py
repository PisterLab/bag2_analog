# -*- coding: utf-8 -*-

from typing import Dict, Mapping, List

import os
import pkg_resources

from bag.design.module import Module

# noinspection PyPep8Naming
class bag2_analog__cascode_conn(Module):
    """Module for library bag2_analog cell cascode_conn.

    Fill in high level description here.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'cascode_conn.yaml'))


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
            p_params = 'pmos4_astack parameters',
            n_params = 'nmos4_astack parameters',
            res_params = 'Resistor parameters',
            n_drain_conn = 'List of drain connections for the NMOS of the A (left) side',
            p_drain_conn = 'List of drain connections for the PMOS of the A (left) side',
            res_conn = 'Dictionary (PLUS, MINUS, BULK) of drain connections. Leave empty to remove the resistor.',
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
        ### compensation--export mid nodes
        ### flag for needing both outputs
        p_params = params['p_params']
        n_params = params['n_params']
        res_params = params['res_params']

        n_drain_conn_list = params['n_drain_conn']
        p_drain_conn_list = params['p_drain_conn']
        res_conn_dict = params['res_conn']

        # Delete or design + connect resistor
        has_res = bool(res_conn_dict)
        if not has_res:
            self.delete_instance('XR')
        else:
            self.instances['XR'].design(**res_params)
            assert res_params['BULK'] in ('VDD', 'VSS'), f'Resistor bulk must be connected to VDD or VSS (currently {res_params["BULK"]})'
            for pin,net in res_conn.item():
                self.reconnect_instance_terminal('XR', pin, net)

        # Design cascode elements
        self.instances['XCOREA'].design(n_params=n_params, p_params=p_params)
        self.instances['XCOREB'].design(n_params=n_params, p_params=p_params)

        # Connect drains of elements to gates (or other things) on the A-side
        n_stack = n_params['stack']
        p_stack = p_params['stack']

        assert len(n_drain_conn_list)==n_stack, f'n_drain connection list should have {n_stack} items (has {len(n_drain_conn_list)})'
        assert len(p_drain_conn_list)==p_stack, f'p_drain connection list should have {p_stack} items (has {len(p_drain_conn_list)})'

        DNA_conn = ','.join(n_drain_conn_list[::-1])
        DPA_conn = ','.join(p_drain_conn_list[::-1])

        if DNA_conn[-1] != 'DA' and DPA_conn[-1] != 'DA':
            self.remove_pin('DA')

        self.reconnect_instance_terminal('XCOREA', f'DN<{n_stack-1}:0>', DNA_conn)
        self.reconnect_instance_terminal('XCOREA', f'DP<{p_stack-1}:0>', DPA_conn)

        # Pinning out drains on the A-side which are tied to themselves (i.e. DN<i> gets pinned out if it's tied to DNA<i>)
        DNA_idx_list = []
        for i,conn in enumerate(n_drain_conn_list):
            if conn == f'DNA<{i}>':
                DNA_idx_list.append(i)
            elif 'DNA' in conn:
                print(f'*** WARNING *** is n_drain_conn correct? Trying to connect DNA<{i}> to {conn}', flush=True)

        DNA_bus_list = bus_list(DNA_idx_list)
        assert len(DNA_bus_list)<2, f'Currently only supports drain connections where there is no interspersed self-biasing on the N-side'
        if bool(DNA_bus_list):
            self.rename_pin('DNA', f'DNA<{DNA_bus_list[0]}>')
        else:
            self.remove_pin('DNA')

        DPA_idx_list = []
        for i, conn in enumerate(p_drain_conn_list):
            if conn == f'DPA<{i}>':
                DPA_idx_list.append(i)
            elif 'DPA' in conn:
                print(f'*** WARNING *** is p_drain_conn correct? Trying to connect DPA<{i}> to {conn}')
        DPA_bus_list = bus_list(DPA_idx_list)
        assert len(DPA_bus_list)<2, f'Currently only supports drain connections where there is no interspersed self-biasing on the P-side'
        if bool(DPA_bus_list):
            self.rename_pin('DPA', f'DPA<{DPA_bus_list[0]}>')
        else:
            self.remove_pin('DPA')

        # Connecting the middlemost drain on the B-side
        DNB_conn = 'DB' 
        DPB_conn = 'DB'

        # Reconnecting the gate pins
        if n_stack > 1:
            suffix_gn = f'<{n_stack-1}:0>'
            self.rename_pin('GN<0>', f'GN{suffix_gn}')
            self.reconnect_instance_terminal('XCOREA', f'GN{suffix_gn}', f'GN{suffix_gn}')
            self.reconnect_instance_terminal('XCOREB', f'GN{suffix_gn}', f'GN{suffix_gn}')

            DNB_conn_add = f'DNB<0>' if n_stack==2 else f'DNB<{n_stack-2}:0>'
            DNB_conn = ','.join([DNB_conn, DNB_conn_add])

        if p_stack > 1:
            suffix_gp = f'<{p_stack-1}:0>'
            self.rename_pin('GP<0>', f'GP{suffix_gp}')
            self.reconnect_instance_terminal('XCOREA', f'GP{suffix_gp}', f'GP{suffix_gp}')
            self.reconnect_instance_terminal('XCOREB', f'GP{suffix_gp}', f'GP{suffix_gp}')

            DPB_conn_add = f'DPB<0>' if p_stack==2 else f'DPB<{p_stack-2}:0>'
            DPB_conn = ','.join([DPB_conn, DPB_conn_add])

        self.rename_pin('DNB', DNB_conn_add)
        self.rename_pin('DPB', DPB_conn_add)

        # Connecting the B-side drain
        self.reconnect_instance_terminal('XCOREB', f'DN<{n_stack-1}:0>', DNB_conn)
        self.reconnect_instance_terminal('XCOREB', f'DP<{n_stack-1}:0>', DPB_conn)

def bus_list(idx_list) -> List[str]:
    '''
    Inputs:
        idx_list: List of indices (not necessarily sorted nor contiguous)
    Returns:
        A list of strings for the indices in bus format
        For example:
            idx_list = [1, 2, 5, 6, 7, 9]
            bus_list(idx_list) -> ['9', '7:5', '2:1']
    '''
    indices = set(idx_list)
    indices = list(indices)
    indices.sort(reverse=True)

    bus_list = []
    if bool(idx_list):
        start = indices[0]
        stop = indices[0]
        prev = indices[0]
        for cur in indices[1::]:
            if cur != prev - 1:
                stop = prev
                if stop == start:
                    bus_list.append(f'{start}')
                else:
                    bus_list.append(f'{start}:{stop}')
                start = cur
            prev = cur
        if prev == start:
            bus_list.append(f'{start}')
        else:
            bus_list.append(f'{start}:{prev}')

    return bus_list