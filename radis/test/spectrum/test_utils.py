# -*- coding: utf-8 -*-
"""
Created on Tue Jul 27 02:04:14 2021

@author: erwan
"""


def test_perf_profile(*args, **kwargs):
    """Test visual/interactive performance profile

    Examples
    --------
    ::
        s = calc_spectrum(...)
        s.generate_perf_profile()

    See output in https://github.com/radis/radis/pull/324

    """
    from radis.lbl.calc import calc_spectrum
    from radis.test.utils import setup_test_line_databases

    setup_test_line_databases()

    s = calc_spectrum(
        2000,
        2300,
        molecule="CO",
        Tgas=3000,
        databank="HITRAN-CO-TEST",
        verbose=3,
    )
    s.generate_perf_profile()


if __name__ == "__main__":
    test_perf_profile()
