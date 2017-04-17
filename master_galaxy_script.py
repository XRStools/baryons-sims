import yt
import pyxsim
import soxs
import numpy as np

# Load up the dataset using yt
fn = "my_filename"
ds = yt.load(fn)

# Define a center.
center = "c" # this uses the center of the simulation domain
#center = "max" # this uses the location of the maximum density
#center = [0.1, 0.2, -0.3] # This uses a coordinate in the "natural" or "code" units of the dataset

# Define a radius. We can do this simply using a (value, unit) tuple.
radius = (1.0, "Mpc")

# Now use the dataset to set up the sphere using our center and
# radius.
sp = ds.sphere(center, radius)

# Optionally, make a cut region from the sphere where we remove particles with
# high density and/or low temperature. Note that for SPH you will need to make
# sure you use the density units which are correct for the dataset, e.g. 10^10 Msun/kpc**3
# or whatever they are, whereas for AMR datasets use CGS units below. 

cr = sp.cut_region(["obj['density'] < 1.0e-25", "obj['temperature'] > 1.0e5"]) # for AMR
# For SPH
#dens_code = ds.quan(1.0e-25, "g/cm**3").to("code_mass/code_length**3").v
#cr = sp.cut_region(["obj['PartType0', 'Density'] < %g" % dens_code, "obj['PartType0', 'Temperature'] > 1.0e5"])

# This next part sets up the APEC model for the spectrum
emin = 0.02 # minimum energy in keV
emax = 12.0 # maximum energy in keV
nchan = 12000 # should ideally result in spectral resolution that is better than the detector you are using
apec_model = pyxsim.TableApecModel(emin, emax, nchan, thermal_broad=True)

# The next part defines that the model for emission is a thermal source. 
# Because there are typically many, many more cells / particles than is 
# computationally feasible, we create a much smaller set of temperature bins
# and only create that many spectra. 

kT_min = 0.03 # minimum temperature in keV
kT_max = 10.0 # maximum temperature in keV
n_kT = 10000 # number of temperature bins

# This will be the name of the metallicity field. It will need to be different
# depending on whether or not you have a AMR or SPH dataset. 

metallicity_field = ("gas", "metallicity") # for AMR
#metallicity_field = ("PartType0", "Metallicity") # for SPH

# Now we set up the thermal model itself using the parameters we set up. 
thermal_model = pyxsim.ThermalSourceModel(apec_model, kT_min=kT_min, kT_max=kT_max,
                                          n_kT=n_kT, Zmet=metallicity_field)

# The next thing to do is to create a PhotonList, which will be a Monte-Carlo 
# source distribution of photons in 3D. To make it easy to decide how many 
# photons to generate, we will set it by giving an exposure time and an area,
# which should be larger than the values you intend to use for the instrument
# you simulate. We use the cut region defined above as our source region.

redshift = 0.03 # the redshift of the source
exp_time = 500000.0 # in seconds, this is 500 ksec
area = 35000.0 # flat area in cm**2, just for generating initial source. Must be 
               # larger than peak of ARF for the instrument you're simulating

photons = pyxsim.PhotonList.from_data_source(cr, redshift, area, exp_time, 
                                             thermal_model, center=center)

# Save the photons to the file for re-use. We use the original filename as a base
# for the name of this file. 
photons.write_h5_file("%s_photons.h5" % fn)

# The next step is to project the photons to the sky plane along an axis. 

sky_center = [30.0, 45.0] # in degrees

# "axis" can be either "x", "y", or "z", or a direction vector e.g. [1.0, -2.5, 0.3]
# for an off-axis observation. 
axis = "z"

# Set up foreground absorption model
nH = 0.02 # 10^20 atoms/cm**2
tbabs_model = pyxsim.TBabsModel(nH)

# Project the photons to a plane
events = photons.project_photons(axis, absorb_model=tbabs_model,
                                 sky_center=sky_center)

# Write the SIMPUT file. Use the original filename as the basename. 
events.write_simput_file(fn, clobber=True)

# Use SOXS to simulate the observation. Use a background file we have 
# previously generated.

simput_file = "%s_simput.fits" % fn # the source SIMPUT file
out_file = "evt.fits" # the name of the event file to be written
instrument = "hdxi" # The instrument to use
bkgnd_file = "bkgnd_hdxi_1Msec_evt.fits" # the background file to use. 

# NOTE: Because we are specifying a background file, the other background
# keywords are ignored regardless of their value!!

soxs.instrument_simulator(simput_file, out_file, exp_time, args.inst, 
                          sky_center, overwrite=True, bkgnd_file=bkgnd_file)
