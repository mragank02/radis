# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 09:59:55 2017

@author: erwan

Examples
--------

Run all tests::

    pytest       (in command line, in project folder)

Run only fast tests (i.e: tests that have a 'fast' label)::

    pytest -m fast
    
------------------------------------------------------------------------

"""

from __future__ import unicode_literals, print_function, absolute_import, division
import radis
from radis.lbl import SpectrumFactory
from radis.misc.printer import printm
from radis.misc.utils import DatabankNotFound
from radis.test.utils import IgnoreMissingDatabase, setup_test_line_databases
from radis.spectrum import Spectrum
import numpy as np
import matplotlib.pyplot as plt
from os.path import basename
import pytest

fig_prefix = basename(__file__)+': '

# %% ======================================================================
# TEST
# ---------------------


@pytest.mark.needs_config_file
@pytest.mark.needs_db_CDSD_HITEMP
def test_spec_generation(plot=True, verbose=2, warnings=True, *args, **kwargs):
    ''' Test spectrum generation
    Can be used as a base to generate spectra in your codes

    Non-regression test: compare with past version (see conditions below)

    Compare results from a reference case to results calculated on 30/12/2017
    This is not a validation case (30/12/2017 results are not a physically validated
    case), but it makes sure results dont change over time

    Conditions (30/12/2017)::

        Physical Conditions
        ----------------------------------------
           Tgas                 300 K
           Trot                 300 K
           Tvib                 300 K
           pressure             1.01325 bar
           isotope              1,2
           mole_fraction        1
           molecule             CO2
           path_length          1 cm
           wavelength_max       4400.0 nm
           wavelength_min       4150.0 nm
           wavenum_max          2409.6385542168673 cm-1
           wavenum_min          2272.7272727272725 cm-1
        Computation Parameters
        ----------------------------------------
           Tref                 296 K
           broadening_max_width  10 cm-1
           cutoff               1e-25 cm-1/(#.cm-2)
           db_assumed_sorted    True
           db_use_cached        True
           dbformat             cdsd
           dbpath               # USER-DEPENDANT: CDSD-HITEMP
           fillmissinglevelswithzero  False
           levelsfmt            cdsd
           levelspath           # USER-DEPENDANT: CDSD-4000
           medium               vacuum
           parfuncfmt           cdsd
           parfuncpath          # USER-DEPENDANT: CDSD-4000
           rot_distribution     boltzmann
           self_absorption      True
           vib_distribution     boltzmann
           wavenum_max_calc     2414.6385542168673 cm-1
           wavenum_min_calc     2267.7272727272725 cm-1
           waveunit             cm-1
           wstep                0.01 cm-1
        ----------------------------------------

    Notes
    -----

    Performance test. How long it tooks to calculate this Spectrum?
    Test with cutoff 1e-25, broadening_max_width=10 

    - 0.9.15: >>> 33s

    - 0.9.16*: (replaced groupby().apply() with iteration over indexes) >>> 32s  
            [but large impact expected on big files]

    - 0.9.16*: (upgraded cache files to h5) >>> 25s 

    - 0.9.16*: (also added h5 cache file for levels) >>> 21s

    - 0.9.16*: (with Whiting slit voigt function) >>> 5.8s

    Test with cutoff 1e-27, broadening_max_width=50 :  
    ("Spectrum calculated in ... ", including database loading time)

    - 0.9.16*: (same code as last) >>> 12.5s including 7.6s of broadening

    - 0.9.16**: (with pseudo_continuum_threshold=0.01) >>> 7.8s including 2.3s of broadening

    - 0.9.18 (normal code, no pseudo continuum). >>> ?
    
    - 0.9.21 (normal code) >>> 13.7s, including 8.7s of broadening
             (with pseudo_continuum_threshold=0.01) >>> 4.3s, including 2.6s of broadening

    - 0.9.21*              >>> 14.0s  (added the manual lineshape normalization instead of
                                       Whitings's polynomial)
    
    - 0.9.22 (normal code) >>> 11.3s   (without energy level lookup, for eq. calculations)
             (with pseudo_continuum_threshold=0.01) >>> 5.9s

    - 0.9.23 (normal code) >>> 7.2s   (added jit in Voigt broadening)
                           >>> 7.1s   (chunksize = None)  (and much faster for more lines)
             (with pseudo_continuum_threshold=0.01) >>> 4.9s
             
    RADIS:
        
    - 0.9.19 (normal code) >>> 6.3 s
    
    - 0.9.20 (normal code) >>> 6.3 s
             (with pseudo_continuum_threshold=0.01) >>> ???
             (with DLM) >>> 2.3 s
    
    '''

    if plot:  # Make sure matplotlib is interactive so that test are not stuck in pytest
        plt.ion()

    try:
        from time import time
        t0 = time()
        if verbose:
            printm('>>> _test_spec_generation')

         # This is how you get a spectrum (see calc.py for front-end functions
        # that do just that)
        sf = SpectrumFactory(wavelength_min=4150, wavelength_max=4400,
                             parallel=False, bplot=False, cutoff=1e-27,
                             isotope='1,2', db_use_cached=True,
                             broadening_max_width=50,
#                             chunksize='DLM',
#                             pseudo_continuum_threshold=0.01,
                             medium='vacuum',
                             verbose=verbose)
        sf.warnings['MissingSelfBroadeningWarning'] = 'ignore'
        sf.warnings['NegativeEnergiesWarning'] = 'ignore'
        sf.load_databank('HITEMP-CO2-DUNHAM',
                         load_energies=False,  # no need to load energies at equilibrium
                         )
        s = sf.eq_spectrum(Tgas=300)
        if verbose:
            printm('>>> _test_spec_generation: Spectrum calculated in {0:.2f}s'.format(time()-t0))
            
        if plot:
            plt.figure(fig_prefix+'Reference spectrum CDSD-HITEMP (radiance)')
            # Iunit is arbitrary. Use whatever makes sense
            s.plot('radiance_noslit', Iunit='µW/cm2/sr/nm', nfig='same')
        s.rescale_path_length(0.01)

        # Here we get some extra informations:
        if plot:
            sf.plot_broadening(i=0)          # show broadening of one line
            plt.xlim((2267.20, 2268.30))

        # Compare with harcoded results
        # ... code previously used to export hardcoded results:
        # ... and header contains all input conditions:
#        np.savetxt('output.txt', np.vstack(s.get('abscoeff', wunit='nm', medium='air')).T[::10])
#        print(s)
        # ................
        from radis.test.utils import getTestFile
        wref, Iref = np.loadtxt(getTestFile(
            'CO2abscoeff_300K_4150_4400nm.txt')).T
        match_reference = np.allclose(
            s.get('abscoeff', wunit='nm', medium='air')[1][::10], Iref)
        if not match_reference:
            # give some more information before raising error
            printm('Error: {0:.2f}%'.format(np.mean(abs(s.get('abscoeff', wunit='nm',
                                                              medium='air')[1][::10]/Iref-1))*100))
            # Store the faulty spectrum
            s.store('test_factory_failed_{0}.spec'.format(radis.get_version()),
                    if_exists_then='replace')

        # Plot comparison
        if plot:
            plt.figure(fig_prefix+'Reference spectrum (abscoeff)')
            # , show_points=True)  # show_points to have an
            s.plot('abscoeff', wunit='nm', medium='air',
                   nfig='same', lw=3, label='RADIS, this version')
            # idea of the resolution
            plt.plot(wref, Iref, 'or', ms=3,
                     label='version NEQ 0.9.20 (12/05/18)')
            plt.legend()
            plt.title('All close: {0}'.format(match_reference))
            plt.tight_layout()

        # Another example, at higher temperature.
        # Removed because no test is associated with it and it takes time for
        # nothing
#        s2 = sf.non_eq_spectrum(Tvib=1000, Trot=300)
#        if plot: s2.plot('abscoeff', wunit='nm')

        if verbose:
            printm('Spectrum calculation (no database loading) took {0:.1f}s\n'.format(
                s.conditions['calculation_time']))
            printm(
                '_test_spec_generation finished in {0:.1f}s\n'.format(time()-t0))

        assert match_reference

    except DatabankNotFound as err:
        assert IgnoreMissingDatabase(err, __file__, warnings)

# Test power integral


@pytest.mark.fast
def test_power_integral(verbose=True, warnings=True, *args, **kwargs):
    ''' Test direct calculation of power integral from Einstein coefficients
    matches integration of broadened spectrum in the optically thin case

    We compare:

    - direct calculation of power integral with equilibrium code
        :meth:`~radis.lbl.SpectrumFactory.optically_thin_power` (T)
    - direct calculation of power integral with non equilibrium code  
        :meth:`~radis.lbl.SpectrumFactory.optically_thin_power` (T,T)
    - numerical integration of non equilibrium spectrum under optically thin conditions: 
        :meth:`~radis.spectrum.spectrum.Spectrum.get_power`

    Test passes if error < 0.5%

    '''

    try:
        if verbose:
            printm('>>> _test_power_integral')

        setup_test_line_databases()  # add HITRAN-CO-TEST in ~/.radis if not there

        sf = SpectrumFactory(wavelength_min=4300, wavelength_max=4666,
                             wstep=0.001,
                             parallel=False, bplot=False, cutoff=1e-30,
                             path_length=10, mole_fraction=400e-6,
                             isotope=[1], db_use_cached=True,
                             broadening_max_width=10,
                             verbose=verbose)
        sf.warnings.update({'MissingSelfBroadeningWarning':'ignore',
                            'OutOfRangeLinesWarning':'ignore',
                            'HighTemperatureWarning':'ignore',})
        sf.load_databank('HITRAN-CO-TEST')
        unit = 'µW/sr/cm2'
        T = 600

        # Calculate:

        # ... direct calculation of power integral with equilibrium code
        Peq = sf.optically_thin_power(Tgas=T, unit=unit)

        # ... direct calculation of power integral with non equilibrium code
        Pneq = sf.optically_thin_power(Tvib=T, Trot=T, unit=unit)

        # ... numerical integration of non equilibrium spectrum under optically thin
        # ... conditions
        sf.input.self_absorption = False
        s = sf.non_eq_spectrum(T, T)

        assert s.conditions['self_absorption'] == False

        # Compare
        err = abs(Peq-s.get_power(unit=unit))/Peq
        if verbose:
            printm('Emission integral:\t{0:.4g}'.format(Peq), unit)
            printm('Emission (noneq code):\t{0:.4g}'.format(Pneq), unit)
            printm('Integrated spectrum:\t{0:.4g}'.format(
                s.get_power(unit=unit)), unit)
            printm('Error: {0:.2f}%'.format(err*100))

        assert err < 0.005

    except DatabankNotFound as err:
        assert IgnoreMissingDatabase(err, __file__, warnings)


@pytest.mark.fast
def test_media_line_shift(plot=False, verbose=True, warnings=True, *args, **kwargs):
    ''' See wavelength difference in air and vacuum '''

    if plot:  # Make sure matplotlib is interactive so that test are not stuck in pytest
        plt.ion()

    try:
        if verbose:
            printm('>>> _test_media_line_shift')

        setup_test_line_databases()  # add HITRAN-CO-TEST in ~/.radis if not there

        sf = SpectrumFactory(wavelength_min=4500, wavelength_max=4600,
                             wstep=0.001,
                             parallel=False, bplot=False, cutoff=1e-30,
                             path_length=0.1, mole_fraction=400e-6,
                             isotope=[1], db_use_cached=True,
                             medium='vacuum',
                             broadening_max_width=10,
                             verbose=verbose)
        sf.warnings['MissingSelfBroadeningWarning'] = 'ignore'
        sf.warnings['GaussianBroadeningWarning'] = 'ignore'
        sf.load_databank('HITRAN-CO-TEST')

        # Calculate in Vacuum
        sv = sf.eq_spectrum(2000)
        assert sv.conditions['medium'] == 'vacuum'

        # Calculate in Air
        # change input (not recommended to access this directly!)
        sf.input.medium = 'air'
        sa = sf.eq_spectrum(2000)
        assert sa.conditions['medium'] == 'air'

        # Compare
        if plot:
            fig = plt.figure(fig_prefix+'Propagating media line shift')
            sv.plot('radiance_noslit', nfig=fig.number, lw=2, label='Vacuum')
            plt.title('CO spectrum (2000 K)')
            sa.plot('radiance_noslit', nfig=fig.number,
                    lw=2, color='r', label='Air')

        # ... there should be about ~1.25 nm shift at 4.5 µm:
        assert np.isclose(sv.get('radiance_noslit', wunit='nm')[0][0] -
                          sa.get('radiance_noslit', wunit='nm')[0][0],
                          1.2540436086346745)

    except DatabankNotFound as err:
        assert IgnoreMissingDatabase(err, __file__, warnings)


def _run_testcases(plot=True, verbose=True, *args, **kwargs):
#
    # Test power density
    test_power_integral(verbose=verbose, *args, **kwargs)

#    # Show media line_shift
    test_media_line_shift(plot=plot, verbose=verbose, *args, **kwargs)

    # Test spectrum generation
    test_spec_generation(plot=plot, verbose=2*True, *args, **kwargs)

    return True


# --------------------------
if __name__ == '__main__':
    
    printm('Testing factory:', _run_testcases(verbose=True))
