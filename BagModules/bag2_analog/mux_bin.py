# -*- coding: utf-8 -*-

from typing import Mapping

import os
import pkg_resources

from bag.design.module import Module


# noinspection PyPep8Naming
class bag2_analog__mux_bin(Module):
    """Module for library bag2_analog cell mux_bin.

    Binary mux tree with no decoding required. Note that the number of mux elements
    increases exponentially vs. bit.

    Note that the LSB connects to the most unit muxes; size your buffers
    accordingly.
    """
    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'mux_bin.yaml'))


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
            num_bits = 'Number of select bits',
            buf_params_list = 'List of inverter chain parameters (ordering matches bit, i.e. LSB is buffered with index 0)',
            mux_params = 'Standalone mux mux_bin_sel (with no buffer) parameters, sans num_bits'
        )

    def design(self, **params) -> None:
        """To be overridden by subclasses to design this module.

        This method should fill in values for all parameters in
        self.parameters.  To design instances of this module, you can
        call their design() method or any other ways you coded.
        """
        num_bits = params['num_bits']
        buf_params_list = params['buf_params_list']
        mux_params = params['mux_params']

        num_in = 1 << num_bits
        buf_len_list = [len(p['inv_param_list']) for p in buf_params_list]

        assert len(buf_params_list) == num_bits, f'Number of select bit buffers ({len(buf_params_list)}) ' \
                                                'should match the number of bits {num_bits}'
        assert all(buf_len > 1 for buf_len in buf_len_list), 'All buffer chains should have at least 2 inverters'

        # Design instances
        self.instances['XMUX'].design(num_bits=num_bits, **mux_params)

        if num_bits > 1:
            inst_list = [f'XBUF<{i}>' for i in range(num_bits)]
            conn_list = [{'in' : f'S<{i}>',
                          'out' : f'sel_buf<{i}>',
                          'outb' : f'selb_buf<{i}>',
                          'VDD' : 'VDD',
                          'VSS' : 'VSS'} for i in range(num_bits)]

            self.array_instance('XBUF', inst_list, conn_list)

            for i in range(num_bits):
                self.instances['XBUF'][i].design(dual_output=True, **(buf_params_list[i]))

        if num_bits > 1:
            # Rewiring up the mux
            sel_pin = f'S<{num_bits-1}:0>'
            selb_pin = f'Sb<{num_bits-1}:0>'
            selb_net = f'selb_buf<{num_bits-1}:0>'
            sel_net = f'sel_buf<{num_bits-1}:0>'
            in_pin_net = f'VIN<{num_in-1}:0>'

            self.reconnect_instance_terminal('XMUX', sel_pin, sel_net)
            self.reconnect_instance_terminal('XMUX', selb_pin, selb_net)
            self.reconnect_instance_terminal('XMUX', in_pin_net, in_pin_net)

            # Adjusting pin names
            self.rename_pin('S', f'S<{num_bits-1}:0>')
            self.rename_pin('VIN<1:0>', f'VIN<{num_in-1}:0>')