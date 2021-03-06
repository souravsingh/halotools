#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)

from unittest import TestCase
import warnings, os, shutil

from astropy.config.paths import _find_home 
from astropy.tests.helper import remote_data, pytest

try:
    import h5py 
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

import numpy as np 
from copy import copy, deepcopy 

from . import helper_functions

from astropy.table import Table

from .. import UserSuppliedHaloCatalog
from ..halo_table_cache import HaloTableCache

from ...custom_exceptions import HalotoolsError, InvalidCacheLogEntry

### Determine whether the machine is mine
# This will be used to select tests whose 
# returned values depend on the configuration 
# of my personal cache directory files
aph_home = u'/Users/aphearin'
detected_home = _find_home()
if aph_home == detected_home:
    APH_MACHINE = True
else:
    APH_MACHINE = False

__all__ = ('TestUserSuppliedHaloCatalog', )

class TestUserSuppliedHaloCatalog(TestCase):
    """ Class providing tests of the `~halotools.sim_manager.UserSuppliedHaloCatalog`. 
    """

    def setUp(self):
        """ Pre-load various arrays into memory for use by all tests. 
        """
        self.Nhalos = 1e2
        self.Lbox = 100
        self.redshift = 0.0
        self.halo_x = np.linspace(0, self.Lbox, self.Nhalos)
        self.halo_y = np.linspace(0, self.Lbox, self.Nhalos)
        self.halo_z = np.linspace(0, self.Lbox, self.Nhalos)
        self.halo_mass = np.logspace(10, 15, self.Nhalos)
        self.halo_id = np.arange(0, self.Nhalos, dtype = np.int)
        self.good_halocat_args = (
            {'halo_x': self.halo_x, 'halo_y': self.halo_y, 
            'halo_z': self.halo_z, 'halo_id': self.halo_id, 'halo_mass': self.halo_mass}
            )
        self.toy_list = [elt for elt in self.halo_x]

        self.num_ptcl = 1e4
        self.good_ptcl_table = Table(
            {'x': np.zeros(self.num_ptcl), 
            'y': np.zeros(self.num_ptcl), 
            'z': np.zeros(self.num_ptcl)}
            )


        self.dummy_cache_baseloc = helper_functions.dummy_cache_baseloc
        try:
            shutil.rmtree(self.dummy_cache_baseloc)
        except:
            pass
        os.makedirs(self.dummy_cache_baseloc)

    def test_particle_mass_requirement(self):

        with pytest.raises(HalotoolsError):
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                **self.good_halocat_args)

    def test_lbox_requirement(self):

        with pytest.raises(HalotoolsError):
            halocat = UserSuppliedHaloCatalog(particle_mass = 200, 
                **self.good_halocat_args)

    def test_halos_contained_inside_lbox(self):

        with pytest.raises(HalotoolsError):
            halocat = UserSuppliedHaloCatalog(Lbox = 20, particle_mass = 100, 
                **self.good_halocat_args)

    def test_redshift_is_float(self):

        with pytest.raises(HalotoolsError) as err:
            halocat = UserSuppliedHaloCatalog(
                Lbox = 200, particle_mass = 100, redshift = '1.0', 
                **self.good_halocat_args)
        substr = "The ``redshift`` metadata must be a float."
        assert substr in err.value.message


    def test_successful_load(self):

        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)
        assert hasattr(halocat, 'Lbox')
        assert halocat.Lbox == 200
        assert hasattr(halocat, 'particle_mass')
        assert halocat.particle_mass == 100

    def test_additional_metadata(self):

        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift,
            arnold_schwarzenegger = 'Stick around!', 
            **self.good_halocat_args)
        assert hasattr(halocat, 'arnold_schwarzenegger')
        assert halocat.arnold_schwarzenegger == 'Stick around!'

    def test_all_halo_columns_have_length_nhalos(self):

        # All halo catalog columns must have length-Nhalos
        bad_halocat_args = deepcopy(self.good_halocat_args)
        with pytest.raises(HalotoolsError):
            bad_halocat_args['halo_x'][0] = -1
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                particle_mass = 100, redshift = self.redshift,
                **bad_halocat_args)

    def test_positions_contained_inside_lbox_alt_test(self):
        # positions must be < Lbox
        bad_halocat_args = deepcopy(self.good_halocat_args)
        with pytest.raises(HalotoolsError):
            bad_halocat_args['halo_x'][0] = 10000
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                particle_mass = 100, redshift = self.redshift,
                **bad_halocat_args)

    def test_has_halo_x_column(self):
        # must have halo_x column 
        bad_halocat_args = deepcopy(self.good_halocat_args)
        with pytest.raises(HalotoolsError):
            del bad_halocat_args['halo_x']
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                particle_mass = 100, redshift = self.redshift,
                **bad_halocat_args)

    def test_has_halo_id_column(self):
        # Must have halo_id column 
        bad_halocat_args = deepcopy(self.good_halocat_args)
        with pytest.raises(HalotoolsError):
            del bad_halocat_args['halo_id']
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                particle_mass = 100, redshift = self.redshift,
                **bad_halocat_args)

    def test_has_halo_mass_column(self):
        # Must have some column storing a mass-like variable
        bad_halocat_args = deepcopy(self.good_halocat_args)
        with pytest.raises(HalotoolsError):
            del bad_halocat_args['halo_mass']
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                particle_mass = 100, redshift = self.redshift,
                **bad_halocat_args)

    def test_halo_prefix_warning(self):
        # Must raise warning if a length-Nhalos array is passed with 
        # a keyword argument that does not begin with 'halo_'
        bad_halocat_args = deepcopy(self.good_halocat_args)
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            bad_halocat_args['s'] = np.ones(self.Nhalos)
            halocat = UserSuppliedHaloCatalog(Lbox = 200, 
                particle_mass = 100, redshift = self.redshift,
                **bad_halocat_args)
            assert 'interpreted as metadata' in str(w[-1].message)

    def test_ptcl_table(self):
        """ Method performs various existence and consistency tests on the input ptcl_table.

        * Enforce that instances do *not* have ``ptcl_table`` attributes if none is passed. 

        * Enforce that instances *do* have ``ptcl_table`` attributes if a legitimate one is passed. 

        * Enforce that ptcl_table have ``x``, ``y`` and ``z`` columns. 

        * Enforce that ptcl_table input is an Astropy `~astropy.table.Table` object, not a Numpy recarray
        """

    def test_ptcl_table_dne(self):
        # Must not have a ptcl_table attribute when none is passed
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift,
            **self.good_halocat_args)
        assert not hasattr(halocat, 'ptcl_table')

    def test_ptcl_table_exists_when_given_goodargs(self):
   
        # Must have ptcl_table attribute when argument is legitimate
        halocat = UserSuppliedHaloCatalog(
            Lbox = 200, particle_mass = 100, redshift = self.redshift,
            ptcl_table = self.good_ptcl_table, **self.good_halocat_args)
        assert hasattr(halocat, 'ptcl_table')

    def test_min_numptcl_requirement(self):
        # Must have at least 1e4 particles
        num_ptcl2 = 1e3
        ptcl_table2 = Table(
            {'x': np.zeros(num_ptcl2), 
            'y': np.zeros(num_ptcl2), 
            'z': np.zeros(num_ptcl2)}
            )
        with pytest.raises(HalotoolsError):
            halocat = UserSuppliedHaloCatalog(
                Lbox = 200, particle_mass = 100, redshift = self.redshift,
                ptcl_table = ptcl_table2, **self.good_halocat_args)

    def test_ptcls_have_zposition(self):
        # Must have a 'z' column 
        num_ptcl2 = 1e4
        ptcl_table2 = Table(
            {'x': np.zeros(num_ptcl2), 
            'y': np.zeros(num_ptcl2)}
            )
        with pytest.raises(HalotoolsError):
            halocat = UserSuppliedHaloCatalog(
                Lbox = 200, particle_mass = 100, redshift = self.redshift,
                ptcl_table = ptcl_table2, **self.good_halocat_args)

    def test_ptcls_are_astropy_table(self):
        # Data structure must be an astropy table, not an ndarray
        ptcl_table2 = self.good_ptcl_table.as_array()
        with pytest.raises(HalotoolsError):
            halocat = UserSuppliedHaloCatalog(
                Lbox = 200, particle_mass = 100, redshift = self.redshift,
                ptcl_table = ptcl_table2, **self.good_halocat_args)

    @pytest.mark.skipif('not HAS_H5PY')
    def test_add_halocat_to_cache1(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)

        basename = 'abc'
        fname = os.path.join(self.dummy_cache_baseloc, basename)
        os.system('touch ' + fname)
        assert os.path.isfile(fname)

        dummy_string = '  '
        with pytest.raises(HalotoolsError) as err:
            halocat.add_halocat_to_cache(
                fname, dummy_string, dummy_string, dummy_string, dummy_string)
        substr = "Either choose a different fname or set ``overwrite`` to True"
        assert substr in err.value.message

        with pytest.raises(HalotoolsError) as err:
            halocat.add_halocat_to_cache(
                fname, dummy_string, dummy_string, dummy_string, dummy_string, 
                overwrite = True)
        assert substr not in err.value.message

    @pytest.mark.skipif('not HAS_H5PY')
    def test_add_halocat_to_cache2(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)

        basename = 'abc'

        dummy_string = '  '
        with pytest.raises(HalotoolsError) as err:
            halocat.add_halocat_to_cache(
                basename, dummy_string, dummy_string, dummy_string, dummy_string)
        substr = "The directory you are trying to store the file does not exist."
        assert substr in err.value.message

    @pytest.mark.skipif('not HAS_H5PY')
    def test_add_halocat_to_cache3(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)

        basename = 'abc'
        fname = os.path.join(self.dummy_cache_baseloc, basename)
        os.system('touch ' + fname)
        assert os.path.isfile(fname)

        dummy_string = '  '
        with pytest.raises(HalotoolsError) as err:
            halocat.add_halocat_to_cache(
                fname, dummy_string, dummy_string, dummy_string, dummy_string, 
                overwrite = True)
        substr = "The fname must end with an ``.hdf5`` extension."
        assert substr in err.value.message

    @pytest.mark.skipif('not HAS_H5PY')
    def test_add_halocat_to_cache4(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)

        basename = 'abc.hdf5'
        fname = os.path.join(self.dummy_cache_baseloc, basename)
        os.system('touch ' + fname)
        assert os.path.isfile(fname)

        dummy_string = '  '
        class Dummy(object):
            pass
            
            def __str__(self):
                raise TypeError
        not_representable_as_string = Dummy()

        with pytest.raises(HalotoolsError) as err:
            halocat.add_halocat_to_cache(
                fname, not_representable_as_string, dummy_string, dummy_string, dummy_string, 
                overwrite = True)
        substr = "must all be strings."
        assert substr in err.value.message

    @pytest.mark.skipif('not HAS_H5PY')
    def test_add_halocat_to_cache5(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)

        basename = 'abc.hdf5'
        fname = os.path.join(self.dummy_cache_baseloc, basename)
        os.system('touch ' + fname)
        assert os.path.isfile(fname)

        dummy_string = '  '
        class Dummy(object):
            pass
            
            def __str__(self):
                raise TypeError
        not_representable_as_string = Dummy()

        with pytest.raises(HalotoolsError) as err:
            halocat.add_halocat_to_cache(
                fname, dummy_string, dummy_string, dummy_string, dummy_string, 
                overwrite = True, some_more_metadata = not_representable_as_string)
        substr = "keyword is not representable as a string."
        assert substr in err.value.message


    @pytest.mark.skipif('not HAS_H5PY')
    def test_add_halocat_to_cache6(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)

        basename = 'abc.hdf5'
        fname = os.path.join(self.dummy_cache_baseloc, basename)

        simname = 'dummy_simname'
        halo_finder = 'dummy_halo_finder'
        version_name = 'dummy_version_name'
        processing_notes = 'dummy processing notes'

        halocat.add_halocat_to_cache(
            fname, simname, halo_finder, version_name, processing_notes, 
            overwrite = True, some_additional_metadata = processing_notes)

        cache = HaloTableCache()
        assert halocat.log_entry in cache.log

        cache.remove_entry_from_cache_log(
            halocat.log_entry.simname, 
            halocat.log_entry.halo_finder,
            halocat.log_entry.version_name,
            halocat.log_entry.redshift,
            halocat.log_entry.fname, 
            raise_non_existence_exception = True, 
            update_ascii = True,
            delete_corresponding_halo_catalog = True)

    @pytest.mark.skipif('not HAS_H5PY')
    @pytest.mark.xfail
    def test_add_ptcl_table_to_cache(self):
        halocat = UserSuppliedHaloCatalog(Lbox = 200, 
            particle_mass = 100, redshift = self.redshift, 
            **self.good_halocat_args)
        halocat.add_ptcl_table_to_cache()


    def tearDown(self):
        try:
            shutil.rmtree(self.dummy_cache_baseloc)
        except:
            pass









