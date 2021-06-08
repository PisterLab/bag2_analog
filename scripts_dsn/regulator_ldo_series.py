# -*- coding: utf-8 -*-

from typing import Mapping, Tuple, Any, List

import os
import pkg_resources
import numpy as np
import warnings
from pprint import pprint

from bag.design.module import Module
from bag.core import BagProject
from span_ion_proj.scripts_dsn import DesignModule, get_mos_db, estimate_vth, parallel, verify_ratio, num_den_add, enable_print, disable_print
from bag.data.lti import LTICircuit, get_w_3db, get_stability_margins

# noinspection PyPep8Naming
class bag2_analog__regulator_ldo_series_dsn(DesignModule):
    """Module for library bag2_analog cell regulator_ldo_series
    Fill in high level description here.
    """

    @classmethod
    def get_op_info(cls) -> Mapping[str,str]:
        # type: () -> Dict[str, str]
        """Returns a dictionary from parameter names to descriptions.
        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        ans = super().get_op_info()
        ans.update(dict(
            specfile_dict = 'Transistor database spec file names for each device',
            ser_type = 'n or p for type of series device',
            th_dict = 'Transistor flavor dictionary.',
            l_dict = 'Transistor channel length dictionary',
            sim_env = 'Simulation environment',
            vdd = 'Supply voltage in volts.',
            vout = 'Reference voltage to regulate the output to',
            loadreg = 'Maximum absolute change in output voltage given change in output current',
            iload = 'Bias current of series device, in amperes.',
            iref = 'Reference current for amplifier biasing, in amperes',
            iamp_max = 'Maximum amplifier current, in amperes',
            cload = 'Load capacitance from the output of the LDO to ground',
            cdecap = 'Maximum additional capacitance added to circuit',
            rsource = 'Resistance from the power supply, in ohms',
            err = 'Maximum percent static error at output (as decimal)',
            psrr = 'Minimum power supply rejection ratio (dB, 20*log10(dVdd/dVout))',
            psrr_fbw = 'Minimum bandwidth for power supply rejection roll-off',
            pm = 'Minimum phase margin for the large feedback loop, in degrees',
            load_pole = 'True to ensure dominant pole is at theregulator output',
            v_res = 'Resolution of voltage bias point sweeps, in volts'
        ))
        return ans

    def resize_op(self, op, wm):
        op_new = dict()
        for key,value in op.items():
            if key[0] != 'v':
                op_new[key] = wm*value
            else:
                op_new[key] = value
        return op_new

    def dsn_fet(self, **params):
        specfile_dict = params['specfile_dict']
        ser_type = params['ser_type']
        th_dict = params['th_dict']
        sim_env = params['sim_env']

        db_dict = {k:get_mos_db(spec_file=specfile_dict[k],
                                intent=th_dict[k],
                                sim_env=sim_env) for k in specfile_dict.keys()}

        vdd = params['vdd']
        vout = params['vout']
        vg = params['vg']
        iload = params['iload']

        vs = vout if ser_type == 'n' else vdd
        vd = vdd if ser_type == 'n' else vout
        vb = 0 if ser_type == 'n' else vdd

        ser_op = db_dict['ser'].query(vgs=vg-vs, vds=vd-vs, vbs=vb-vs)
        nf = int(round(iload/ser_op['ibias']))
        m = iload/(2*ser_op['ibias'])
        wm = (m%1 + 1)
        nf = 2*int(m)
        ser_op = self.resize_op(ser_op,wm)
        return m > 1, dict(nf=nf, wm=wm, op=ser_op)

    def dsn_amp(self, **params):
        vdd = params['vdd']
        vincm = params['vout']
        voutcm = params['voutcm']
        iload = params['iload']
        iref = params['iref']
        iamp_max = params['iamp_max']
        cload = params['cload']
        cdecap_max = params['cdecap']
        rsource = params['rsource']
        err_max = params['err']
        psrr_min = params['psrr']
        psrr_fbw_min = params['psrr_fbw']
        pm_min = params['pm']
        loadreg_max = params['loadreg']
        load_pole = params['load_pole']
        v_res = params['v_res']
        ser_type = params['ser_type']
        ser_info = params['ser_info']
        db_dict = params['db_dict']
        amp_in = 'n'

        # Get amplifier load pair parameters
        op_load = db_dict['amp_load'].query(vgs=-(vdd-voutcm), vds=-(vdd-voutcm), vbs=0)
        Vstar_load = op_load['vstar']

        amp_dsn_info = dict()

        # Choose amp bias voltages
        Vstar_in_err = float('inf')
        vtail = 0
        op_in = dict()
        for vtail_i in np.arange(0,min(voutcm,vincm),v_res):
            op_in_i = db_dict['amp_in'].query(vgs=vincm-vtail_i, vds=voutcm-vtail_i, vbs=-vtail_i)
            Vstar_in_i = op_in_i['vstar']
            if Vstar_in_err > abs(Vstar_load-Vstar_in_i) and op_in_i['ibias'] > 0:
                Vstar_in_err = abs(Vstar_load-Vstar_in_i)
                vtail = vtail_i
                op_in = op_in_i
                Vstar_in = Vstar_in_i

        Vstar_tail_errsq = float('inf')
        vgtail = 0
        op_tail = dict()
        for vgtail_i in np.arange(0,vdd,v_res):
            op_tail_i = db_dict['amp_tail'].query(vgs=vgtail_i, vds=vtail, vbs=0)
            Vstar_tail_i = op_tail_i['vstar']
            if Vstar_tail_errsq > abs(Vstar_load-Vstar_tail_i)**2+abs(Vstar_in-Vstar_tail_i)**2 and op_tail_i['ibias'] > 0:
                Vstar_tail_errsq = abs(Vstar_load-Vstar_tail_i)**2+abs(Vstar_in-Vstar_tail_i)**2
                vgtail = vgtail_i
                op_tail = op_tail_i
                Vstar_tail = Vstar_tail_i

        # Size reference current mirror
        op_mir = db_dict['amp_mir'].query(vgs=vgtail, vds=vgtail, vbs=0)
        m_mir = iref/(2*op_mir['ibias'])
        wm_mir = (m_mir%1 + 1)
        nf_mir = 2*int(m_mir)
        if nf_mir == 0:
            return False, amp_dsn_info

        # Size amplifier devices and base current
        Id_tail = wm_mir*op_tail['ibias']
        wm_tail = wm_mir
        nf_tail = int(2*max(((2*op_load['ibias'])//Id_tail)+1,((2*op_in['ibias'])//Id_tail)+1))
        if Id_tail*nf_tail > iamp_max:
            return False, amp_dsn_info

        Id_load = Id_tail*nf_tail/2
        m_load = Id_load/op_load['ibias']
        wm_load = (m_load/2)%1 + 1
        nf_load = 2*int(m_load/2)

        m_in = Id_load/op_in['ibias']
        wm_in = (m_in/2)%1 + 1
        nf_in = 2*int(m_in/2)

        # Resize op and format parameters
        op_dict = {'amp_in' : self.resize_op(op_in, wm_in),
                   'amp_tail' : self.resize_op(op_tail, wm_tail),
                   'amp_load' : self.resize_op(op_load, wm_tail),
                   'amp_mir' : self.resize_op(op_mir, wm_mir),
                   'ser' : ser_info['op']}
        nf_dict = {'amp_in' : nf_in,
                   'amp_tail' : nf_tail,
                   'amp_load' : nf_load,
                   'amp_mir' : nf_mir,
                   'ser' : ser_info['nf']}
        wm_dict = {'amp_in' : wm_in,
                   'amp_tail' : wm_tail,
                   'amp_load' : wm_load,
                   'amp_mir' : wm_mir,
                   'ser' : ser_info['wm']}

        A = abs(self._get_loopgain_lti(op_dict, nf_dict, ser_type, amp_in, rsource))
        dc_err = 1/(A+1)
        loadreg = self._get_loadreg_lti(op_dict, nf_dict, ser_type, amp_in, cload, 0, rsource, vincm, iload)
        psrr, psrr_fbw = self._get_psrr_lti(op_dict, nf_dict, ser_type, amp_in, cload, 0, rsource)
        pm = self._get_stb_lti(op_dict, nf_dict, ser_type, amp_in, cload, 0, rsource)
        if pm > pm_min and psrr > psrr_min and psrr_fbw > psrr_fbw_min and loadreg < loadreg_max and dc_err < err_max and Id_tail*nf_tail < iamp_max and not load_pole:
            amp_dsn_info.update(dict(op_dict=op_dict,nf_dict=nf_dict,wm_dict=wm_dict))
            amp_dsn_info.update(cap_dict=dict(cdecap_amp=0, cdecap_load=0))
            amp_dsn_info.update(dict(loadreg=loadreg, psrr=psrr, psrr_fbw=psrr_fbw, pm=pm, err=dc_err, ibias=Id_tail*nf_tail))
            return True, amp_dsn_info
        if psrr_fbw > psrr_fbw_min and Id_tail*nf_tail < iamp_max and not load_pole:
            # Find minimum decap necessary with dominant amplifier pole
            cdecap_min = ser_info['op']['cgg']*ser_info['nf']
            for cdecap_amp in np.logspace(np.log10(cdecap_min),np.log10(cdecap_max),100):
                loadreg = self._get_loadreg_lti(op_dict, nf_dict, ser_type, amp_in, cload, cdecap_amp, rsource, vincm, iload)
                psrr, psrr_fbw = self._get_psrr_lti(op_dict, nf_dict, ser_type, amp_in, cload, 0, rsource)
                pm = self._get_stb_lti(op_dict, nf_dict, ser_type, amp_in, cload, cdecap_amp, rsource)
                if psrr_fbw < psrr_fbw_min:
                    break
                if pm > pm_min and psrr > psrr_min and psrr_fbw > psrr_fbw_min and loadreg < loadreg_max and dc_err < err_max:
                    amp_dsn_info.update(dict(op_dict=op_dict,nf_dict=nf_dict,wm_dict=wm_dict))
                    amp_dsn_info.update(cap_dict=dict(cdecap_amp=cdecap_amp, cdecap_load=0))
                    amp_dsn_info.update(dict(loadreg=loadreg, psrr=psrr, psrr_fbw=psrr_fbw, pm=pm, err=dc_err, ibias=Id_tail*nf_tail))
                    return True, amp_dsn_info
        if psrr > psrr_min and loadreg < loadreg_max:
            pm = 0
            psrr_fbw = 0
            while (pm < pm_min or psrr_fbw < psrr_fbw_min) and Id_tail*nf_tail < iamp_max:
                # Resize amp parameters
                Id_load = Id_tail*nf_tail/2

                m_load = Id_load/op_load['ibias']
                wm_load = (m_load/2)%1 + 1
                nf_load = 2*int(m_load/2)

                m_in = Id_load/op_in['ibias']
                wm_in = (m_in/2)%1 + 1
                nf_in = 2*int(m_in/2)

                op_dict.update({'amp_in' : self.resize_op(op_in, wm_in),
                                'amp_tail' : self.resize_op(op_tail, wm_tail),
                                'amp_load' : self.resize_op(op_load, wm_tail)})
                nf_dict.update({'amp_in' : nf_in,
                                'amp_tail' : nf_tail,
                                'amp_load' : nf_load})
                wm_dict.update({'amp_in' : wm_in,
                                'amp_tail' : wm_tail,
                                'amp_load' : wm_load})
                loadreg = self._get_loadreg_lti(op_dict, nf_dict, ser_type, amp_in, cload+cdecap_max, 0, rsource, vincm, iload)
                psrr, psrr_fbw = self._get_psrr_lti(op_dict, nf_dict, ser_type, amp_in, cload+cdecap_max, 0, rsource)
                pm = self._get_stb_lti(op_dict, nf_dict, ser_type, amp_in, cload+cdecap_max, 0, rsource)
                nf_tail += 2
            amp_dsn_info.update(dict(op_dict=op_dict,nf_dict=nf_dict,wm_dict=wm_dict))
            amp_dsn_info.update(cap_dict=dict(cdecap_amp=0, cdecap_load=cdecap_max))
            amp_dsn_info.update(dict(loadreg=loadreg, psrr=psrr, psrr_fbw=psrr_fbw, pm=pm, err=dc_err, ibias=Id_tail*nf_dict['amp_tail']))
            spec_met = pm > pm_min and psrr > psrr_min and psrr_fbw > psrr_fbw_min and loadreg < loadreg_max and dc_err < err_max and Id_tail*nf_dict['amp_tail'] < iamp_max
            return spec_met, amp_dsn_info
        else:
            return False, amp_dsn_info


    def meet_spec(self, **params) -> List[Mapping[str,Any]]:
        specfile_dict = params['specfile_dict']
        th_dict = params['th_dict']
        l_dict = params['l_dict']
        sim_env = params['sim_env']

        db_dict = {k:get_mos_db(spec_file=specfile_dict[k],
                                intent=th_dict[k],
                                sim_env=sim_env) for k in specfile_dict.keys()}
        params.update(dict(db_dict=db_dict))

        ser_type = params['ser_type']
        vdd = params['vdd']
        vout = params['vout']
        iload = params['iload']
        iref = params['iref']
        iamp_max = params['iamp_max']
        cload = params['cload']
        cdecap_max = params['cdecap']
        rsource = params['rsource']
        err_max = params['err']
        psrr_min = params['psrr']
        psrr_fbw_min = params['psrr_fbw']
        pm_min = params['pm']
        loadreg_max = params['loadreg']
        load_pole = params['load_pole']
        v_res = params['v_res']

        vth_ser = estimate_vth(db=db_dict['ser'],
                               is_nch=ser_type=='n',
                               lch=l_dict['ser'],
                               vgs=vdd-vout if ser_type=='n' else -vdd/2,
                               vbs=0-vout if ser_type=='n' else 0)

        # Keep track of best option
        best_op = dict(ibias=float('inf'),
                       err=float('inf'),
                       psrr=0,
                       psrr_fbw=0,
                       pm=0,
                       loadreg=float('inf'))

        type_dict = {'ser' : ser_type,
                     'amp_load' : 'p',
                     'amp_in' : 'n',
                     'amp_tail' : 'n',
                     'amp_mir' : 'n'}

        w_dict = {k:db.width_list[0] for k,db in db_dict.items()}

        self.other_params = dict(l_dict=l_dict,
                                 w_dict=w_dict,
                                 th_dict=th_dict,
                                 cload=cload,
                                 ser_type=ser_type)

        # Sweep gate bias voltage of the series device
        vg_min = vout+vth_ser
        vg_max = min(vdd+vth_ser, vdd)
        vg_vec = np.arange(vg_min, vg_max, v_res)

        for vg in vg_vec:
            print('Designing the series device...')
            # Size the series device
            match_ser, ser_info = self.dsn_fet(vg=vg, **params)
            if not match_ser:
                continue
            print('Done')

            # Design amplifier s.t. output bias = gate voltage
            # This is to maintain accuracy in the computational design proces
            print('Designing the amplifier...')

            params.update(dict(voutcm=vg,
                               iamp_max=iamp_max,
                               ser_info=ser_info))
            spec_met, amp_dsn_info = self.dsn_amp(**params)
            print('Done')

            if not spec_met:
                print('Amp specs not met.')
                continue
            else:
                print('AMP SPECS MET.')

            amp_dsn_info.update(dict(w_dict=w_dict, l_dict=l_dict, th_dict=th_dict, type_dict=type_dict))

            best_op.update(self.op_compare(best_op,amp_dsn_info))
            iamp_max = best_op['ibias']
        return [best_op]

    def _get_loopgain_lti(self, op_dict, nf_dict, ser_type, amp_in, rsource) -> float:
        '''
        Returns:
            A: DC loop gain
        '''
        ckt = LTICircuit()

        n_ser = ser_type == 'n'
        n_amp = amp_in == 'n'
        vdd = 'vdd' if rsource != 0 else 'gnd'
       
        # Series device
        ser_d = vdd if n_ser else 'reg'
        ser_s = 'reg' if n_ser else vdd
        ckt.add_transistor(op_dict['ser'], ser_d, 'out', ser_s, fg=nf_dict['ser'], neg_cap=True)

        # Passives
        if rsource != 0:
            ckt.add_res(rsource, 'gnd', 'vdd')

        # Amplifier
        tail_rail = 'gnd' if n_amp else vdd
        load_rail = vdd if n_amp else 'gnd'
        inp_conn = 'gnd' if n_ser else 'amp_in'
        inn_conn = 'gnd' if not n_ser else 'amp_in' 
        ckt.add_transistor(op_dict['amp_in'], 'outx', inp_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_in'], 'out', inn_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_tail'], 'tail', 'gnd', tail_rail, fg=nf_dict['amp_tail'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_load'], 'outx', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_load'], 'out', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)

        # Calculating stability margins
        num, den = ckt.get_num_den(in_name='amp_in', out_name='reg', in_type='v')
        A = num[-1]/den[-1]

        return A

    def _get_psrr_lti(self, op_dict, nf_dict, ser_type, amp_in, cload, cdecap_amp, rsource) -> float:
        '''
        Returns:
            psrr: PSRR (dB)
            fbw: Power supply -> output 3dB bandwidth (Hz)
        '''
        n_ser = ser_type == 'n'
        n_amp = amp_in == 'n'

        # Supply -> output gain
        ckt_sup = LTICircuit()
        ser_d = 'vdd' if n_ser else 'reg'
        ser_s = 'reg' if n_ser else 'vdd'
        inp_conn = 'gnd' if n_ser else 'reg'
        inn_conn = 'reg' if n_ser else 'gnd'
        tail_rail = 'gnd' if n_amp else 'vdd'
        load_rail = 'vdd' if n_amp else 'gnd'

        # Passives
        if rsource != 0:
            ckt_sup.add_res(rsource, 'vbat', 'vdd')
        ckt_sup.add_cap(cload, 'reg', 'gnd')
        ckt_sup.add_cap(cdecap_amp, 'out', 'reg')

        # Series device
        ckt_sup.add_transistor(op_dict['ser'], ser_d, 'out', ser_s, fg=nf_dict['ser'], neg_cap=False)

        # Amplifier
        ckt_sup.add_transistor(op_dict['amp_in'], 'outx', inp_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt_sup.add_transistor(op_dict['amp_in'], 'out', inn_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt_sup.add_transistor(op_dict['amp_tail'], 'tail', 'gnd', tail_rail, fg=nf_dict['amp_tail'], neg_cap=False)
        ckt_sup.add_transistor(op_dict['amp_load'], 'outx', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)
        ckt_sup.add_transistor(op_dict['amp_load'], 'out', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)

        if rsource == 0:
            num_sup, den_sup = ckt_sup.get_num_den(in_name='vdd', out_name='reg', in_type='v')
        else:
            num_sup, den_sup = ckt_sup.get_num_den(in_name='vbat', out_name='reg', in_type='v')
        gain_sup = num_sup[-1]/den_sup[-1]
        wbw_sup = get_w_3db(den_sup, num_sup)

        if gain_sup == 0:
            return float('inf')
        if wbw_sup == None:
            wbw_sup = 0
        fbw_sup = wbw_sup / (2*np.pi)

        psrr = 10*np.log10((1/gain_sup)**2)

        return psrr, fbw_sup

    def _get_stb_lti(self, op_dict, nf_dict, ser_type, amp_in, cload, cdecap_amp, rsource) -> float:
        '''
        Returns:
            pm: Phase margin (degrees)
        '''
        ckt = LTICircuit()

        n_ser = ser_type == 'n'
        n_amp = amp_in == 'n'
        vdd = 'vdd' if rsource != 0 else 'gnd'
       
        # Series device
        ser_d = vdd if n_ser else 'reg'
        ser_s = 'reg' if n_ser else vdd
        ckt.add_transistor(op_dict['ser'], ser_d, 'out', ser_s, fg=nf_dict['ser'], neg_cap=False)

        # Passives
        ckt.add_cap(cload, 'reg', 'gnd')
        ckt.add_cap(cdecap_amp, 'out', 'reg')
        if rsource != 0:
            ckt.add_res(rsource, 'gnd', 'vdd')

        # Amplifier
        tail_rail = 'gnd' if n_amp else vdd
        load_rail = vdd if n_amp else 'gnd'
        inp_conn = 'gnd' if n_ser else 'amp_in'
        inn_conn = 'gnd' if not n_ser else 'amp_in' 
        ckt.add_transistor(op_dict['amp_in'], 'outx', inp_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_in'], 'out', inn_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_tail'], 'tail', 'gnd', tail_rail, fg=nf_dict['amp_tail'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_load'], 'outx', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_load'], 'out', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)

        # Calculating stability margins
        num, den = ckt.get_num_den(in_name='amp_in', out_name='reg', in_type='v')
        pm, _ = get_stability_margins(np.convolve(num, [-1]), den)

        return pm

    def _get_loadreg_lti(self, op_dict, nf_dict, ser_type, amp_in, cload, cdecap_amp, rsource, vout, iout) -> float:
        '''
        Returns:
            loadreg: Load regulation for peak-to-peak load current variation of 20% (V/V)
        '''
        n_ser = ser_type == 'n'
        n_amp = amp_in == 'n'
        vdd = 'vdd' if rsource != 0 else 'gnd'

        # Supply -> output gain
        ckt = LTICircuit()
        ser_d = vdd if n_ser else 'reg'
        ser_s = 'reg' if n_ser else vdd
        inp_conn = 'gnd' if n_ser else 'reg'
        inn_conn = 'reg' if n_ser else 'gnd'
        tail_rail = 'gnd' if n_amp else vdd
        load_rail = vdd if n_amp else 'gnd'

        # Passives
        if rsource != 0:
            ckt.add_res(rsource, 'gnd', 'vdd')
        ckt.add_cap(cload, 'reg', 'gnd')
        ckt.add_cap(cdecap_amp, 'out', 'reg')

        # Series device
        ckt.add_transistor(op_dict['ser'], ser_d, 'out', ser_s, fg=nf_dict['ser'], neg_cap=False)

        # Amplifier
        ckt.add_transistor(op_dict['amp_in'], 'outx', inp_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_in'], 'out', inn_conn, 'tail', fg=nf_dict['amp_in'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_tail'], 'tail', 'gnd', tail_rail, fg=nf_dict['amp_tail'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_load'], 'outx', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)
        ckt.add_transistor(op_dict['amp_load'], 'out', 'outx', load_rail, fg=nf_dict['amp_load'], neg_cap=False)


        num, den = ckt.get_num_den(in_name='reg', out_name='reg', in_type='i')
        transimpedance = num[-1]/den[-1]

        loadreg = transimpedance*0.2*iout/vout

        return loadreg

    def op_compare(self, op1:Mapping[str,Any], op2:Mapping[str,Any]):
        return op1 if op1['ibias'] < op2['ibias'] else op2

    def get_sch_params(self, op):
        try:
            w_dict_new = dict()
            for key in op['w_dict'].keys():
                w_dict_new[key]=op['wm_dict'][key]*op['w_dict'][key]
            dsn_op = dict(w_dict=w_dict_new,
                          l_dict=op['l_dict'],
                          nf_dict=op['nf_dict'],
                          th_dict=op['th_dict'],
                          type_dict=op['type_dict'],
                          cap_dict=op['cap_dict'])
        except KeyError:
            dsn_op = 'No solution found within specs'
        return dsn_op
