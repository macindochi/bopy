#!/usr/bin/python

import os
import sys
import numpy as np
import bopy as bp

def print_config_example():
    print "ROOT = 20110909_G3_ref"
    print "SOURCES = 0"
    print "SLAB_SERIES_SUM = 5"
    print "WAVELENGTHS = 785"
    print "AMP_FILE_FORMAT_STRING = %s_s%d_wl%s_A_ro.gim"
    print "PHA_FILE_FORMAT_STRING = %s_s%d_wl%s_phi_ro.gim"
    print "FILE_FORMAT_ORDER = source_wavelength"
    print "PP_DATA_DIR = ."
    print "MASK_CUTOFF = 0.25"
    print "TOP_ROWS_MASK = 14"
    print "MEASUREMENT = ref"
    print "N_IN = 1.33"
    print "N_OUT = 1.0"
    print "SLABFIT_FUNCTION = CONTINI"
    print "OPTIMIZATION = l"
    print "SLAB_THICKNESS = 60.0"
    print "RF_FREQ_MHZ = 70"
    print "CALCULATED_MUA_785 = 0.0021429"
    print "CALCULATED_MUSP_785 = 0.8"
    print "PRINT_DIAGNOSTICS = True"

def set_values(pl):
    v = bp.utils.struct()
    v.root = pl.get_val('ROOT')
    v.srcs = np.array([int(val) for val in pl.get_val('SOURCES').split()])
    if len(v.srcs) <= 1:
        if v.srcs[0] == 0:
            v.srcs = np.arange(1, 210) 
    print v.srcs
    v.wls = [int(val) for val in pl.get_val('WAVELENGTHS').split()]
    v.seriessum = int(pl.get_val('SLAB_SERIES_SUM'))
    v.amp_filestring = pl.get_val('AMP_FILE_FORMAT_STRING')
    v.pha_filestring = pl.get_val('PHA_FILE_FORMAT_STRING')
    v.file_format_order = pl.get_val('FILE_FORMAT_ORDER')
    v.ppdata_dir = pl.get_val('PP_DATA_DIR')
    v.mask_cutoff = float(pl.get_val('MASK_CUTOFF'))
    v.toprowsmask = float(pl.get_val('TOP_ROWS_MASK'))
    v.ppdata_type = pl.get_val('MEASUREMENT')
    v.n_in = float(pl.get_val('N_IN'))
    v.n_out = float(pl.get_val('N_OUT'))
    v.slab_l = float(pl.get_val('SLAB_THICKNESS'))
    v.omega = float(pl.get_val('RF_FREQ_MHZ'))*1.0e6*2.0*np.pi
    v.diag = bool(pl.get_val('PRINT_DIAGNOSTICS'))
    v.func = pl.get_val('SLABFIT_FUNCTION')
    v.opt = pl.get_val('OPTIMIZATION')
    v.mua = {}
    v.musp = {}
    for w in v.wls:
        mua = pl.get_val('MUA_%s'%(w))
        if mua == None:
            mua = pl.get_val('CALCULATED_MUA_MM_%s'%(w))
        v.mua[w] = float(mua)
        #v.mua[w] = float(pl.get_val('MUA_%s'%(w))) 
        musp = pl.get_val('MUSP_%s'%(w))
        if musp == None:
            musp = pl.get_val('CALCULATED_MUSP_MM_%s'%(w))
        v.musp[w] = float(musp)
        #v.musp[w] = float(pl.get_val('MUSP_%s'%(w))) 

    return v

try:
    cfgfile = sys.argv[1]
except:
    print >>sys.stderr, "Usage:", os.path.basename(sys.argv[0]), "<cfgfile>"
    print 
    print_config_example()
    sys.exit()

pl = bp.utils.ParamList(cfgfile)
v = set_values(pl)

spos = np.loadtxt(os.path.join(v.ppdata_dir, 'sources.txt'))[:,3:6:2]
dets = np.loadtxt(os.path.join(v.ppdata_dir, 'detectors.txt'))
Xdet = dets[:,3]
Zdet = dets[:,5]

print v.amp_filestring
print v.pha_filestring
print v.root
print v.ppdata_type
print type(v.srcs)
print type(v.wls)

for s in v.srcs:
    #print >>sys.stderr, "source:", s 
    print >>sys.stderr, 'source:', '{0}\r'.format(s),
    for w in v.wls:
        if v.file_format_order == 'source_wavelength': 
            Apath = os.path.join(v.ppdata_dir, v.ppdata_type, v.amp_filestring%(v.root, v.ppdata_type, s, w))         
            Ppath = os.path.join(v.ppdata_dir, v.ppdata_type, v.pha_filestring%(v.root, v.ppdata_type, s, w))         
        else:
            Apath = os.path.join(v.ppdata_dir, v.ppdata_type, v.amp_filestring%(v.root, v.ppdata_type, w, s))         
            Ppath = os.path.join(v.ppdata_dir, v.ppdata_type, v.pha_filestring%(v.root, v.ppdata_type, w, s))         
        if v.opt == "l":
            infslab = bp.do.InfSlab(v.func, slab_d=v.slab_l, n_in=v.n_in, n_out=v.n_out, seriessum=v.seriessum)
            infslab.set_gen3data(Apath, Ppath, Xdet, Zdet, v.omega, mask_cutoff=v.mask_cutoff, toprowsmask=v.toprowsmask)
            ov = infslab.opt_l_run(mua=v.mua[w], musp=v.musp[w], src=spos[(s-1),:])
        elif v.opt == 'muamusp_withlsld':
            infslab = bp.do.InfSlab(v.func, slab_d=v.slab_l, n_in=v.n_in, n_out=v.n_out, seriessum=v.seriessum)
            infslab.set_gen3data(Apath, Ppath, Xdet, Zdet, v.omega, mask_cutoff=v.mask_cutoff, toprowsmask=v.toprowsmask)
            fname = 'results-{0}.txt'.format(w)
            sindex = s - 1
            d = np.loadtxt(fname)[sindex,:]
            S = d[5]
            src = np.array([d[8], d[9]])
            phi0 = d[10]
            fname = 'results-mean-lsld-{0}.txt'.format(w)
            dd = np.loadtxt(fname)
            #print dd
            ls = dd[1]
            ld = dd[2]
            ov = infslab.opt_muamusp_withlsld_run(v.mua[w], v.musp[w], src, ls, ld, S=S, phi0=phi0)
            S = ov['S']
            phi0 = ov['phi0']
            #infslab.print_A_phi_lsld(S, v.mua[w], v.musp[w], src[0], src[1], phi0, v.root, w, s)

        elif v.opt == 'lsld':
            infslab = bp.do.InfSlab(v.func, slab_d=v.slab_l, n_in=v.n_in, n_out=v.n_out, seriessum=v.seriessum)
            infslab.set_gen3data(Apath, Ppath, Xdet, Zdet, v.omega, mask_cutoff=v.mask_cutoff, toprowsmask=v.toprowsmask)
            fname = 'results-{0}.txt'.format(w)
            sindex = s - 1
            d = np.loadtxt(fname)[sindex,:]
            S = d[5]
            src = np.array([d[8], d[9]])
            phi0 = d[10]
            l = d[11]
            ov = infslab.opt_lsld_run(mua=v.mua[w], musp=v.musp[w], src=src, l=l, S=S, phi0=phi0)
            S = ov['S']
            phi0 = ov['phi0']
            infslab.print_A_phi_lsld(S, v.mua[w], v.musp[w], src[0], src[1], phi0, v.root, w, s)
        elif v.opt == 'onlylsld':
            infslab = bp.do.InfSlab(v.func, slab_d=v.slab_l, n_in=v.n_in, n_out=v.n_out, seriessum=v.seriessum)
            infslab.set_gen3data(Apath, Ppath, Xdet, Zdet, v.omega, mask_cutoff=v.mask_cutoff, toprowsmask=v.toprowsmask)
            fname = 'results-{0}.txt'.format(w)
            sindex = s - 1
            d = np.loadtxt(fname)[sindex,:]
            S = d[5]
            src = np.array([d[8], d[9]])
            phi0 = d[10]
            l = d[11]
            ov = infslab.opt_onlylsld_run(mua=v.mua[w], musp=v.musp[w], src=src, l=l, S=S, phi0=phi0)
            infslab.print_A_phi_lsld(S, v.mua[w], v.musp[w], src[0], src[1], phi0, v.root, w, s)
        elif v.opt == 'lSphi':
            infslab = bp.do.InfSlab(v.func, slab_d=v.slab_l, n_in=v.n_in, n_out=v.n_out, seriessum=v.seriessum)
            infslab.set_gen3data(Apath, Ppath, Xdet, Zdet, v.omega, mask_cutoff=v.mask_cutoff, toprowsmask=v.toprowsmask)
            fname = 'results-{0}.txt'.format(w)
            sindex = s - 1
            d = np.loadtxt(fname)[sindex,:]
            S = d[5]
            src = np.array([d[8], d[9]])
            phi0 = d[10]
            l = d[11]
            ov = infslab.opt_lSphi_run(mua=v.mua[w], musp=v.musp[w], src=src, l=l, phi0=phi0)
            infslab.print_A_phi_lsld(S, v.mua[w], v.musp[w], src[0], src[1], phi0, v.root, w, s)
        else:
            infslab = bp.do.InfSlab(v.func, slab_d=v.slab_l, n_in=v.n_in, n_out=v.n_out, seriessum=v.seriessum)
            infslab.set_gen3data(Apath, Ppath, Xdet, Zdet, v.omega, mask_cutoff=v.mask_cutoff, toprowsmask=v.toprowsmask)
            ov = infslab.opt_run(mua=v.mua[w], musp=v.musp[w], src=spos[(s-1),:])
        if v.opt == 'lsld' or v.opt == 'onlylsld':
            print s, w, ov['ier'], ov['ls'], ov['ld'], ov['S'], ov['phi0']
        elif v.opt == 'muamusp_withlsld':
            print s, w, ov['ier'], ov['mua'], ov['musp']
        else:
            print s, w, ov['ier'], ov['mua'], ov['musp'], ov['S'], spos[(s-1), 0], spos[(s-1), 1], ov['xsrc'], ov['zsrc'], ov['phi0'], ov['l']
        #if v.diag == True:
        #    infslab.print_A_phi(ov['S'], ov['mua'], ov['musp'], ov['xsrc'], ov['zsrc'], ov['phi0'], v.root, w, s)
