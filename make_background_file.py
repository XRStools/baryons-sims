import soxs

out_file = 'bkgnd_hdxi_1Msec_evt.fits' # Name of the event file to write
exp_time = 1000000.0 # 1 Msec
instrument = "hdxi" # Default HDXI configuration
sky_center = [24., 12.] # sky center of pointing in degrees, 
                        # but actually doesn't matter because 
                        # it will be reprojected to the correct
                        # coordinates when it is used
                        # to add background to a source

# For this background file, we will be turning the point source backgrounds
# off but leaving the instrumental background and Galactic foreground on
soxs.make_background_file(out_file, exp_time, instrument, sky_center,
                          overwrite=True, foreground=True, instr_bkgnd=True,
                          ptsrc_bkgnd=False)
