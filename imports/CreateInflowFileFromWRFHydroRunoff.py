'''-------------------------------------------------------------------------------
 Source Name: CreateInflowFileFromWRFHydroRunoff.py
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Alan D. Snow, US Army ERDC
 Description: Creates RAPID inflow file based on the WRF_Hydro land model output
              and the weight table previously created.
 History:     Initial coding - 10/17/2014, version 1.0
 Updated:     Version 2.0, 06/10/2015
              Version 3.0, 02/16/2016, Stripped ArcMap specific code and modified for spt_lsm_autorapid_process
-------------------------------------------------------------------------------'''
import os
import netCDF4 as NET
import numpy as NUM
import csv


class CreateInflowFileFromWRFHydroRunoff(object):
    def __init__(self, lat_dim="south_north",
                 lon_dim="west_east",
                 lat_var="XLAT",
                 lon_var="XLONG",
                 surface_runoff_var="SFROFF",
                 subsurface_runoff_var="UDROFF",
                 time_step_seconds=1*3600):
        """Define the tool (tool name is the name of the class)."""
        self.header_wt = ['StreamID', 'area_sqm', 'west_east', 'south_north',
                          'npoints']
        # According to David Gochis, underground runoff is "a major fraction of total river flow in most places"
        self.vars_oi = [lat_var, lon_var, surface_runoff_var, subsurface_runoff_var]
        self.dims_oi = ['Time', lat_dim, lon_dim]
        self.errorMessages = ["Incorrect number of columns in the weight table",
                              "No or incorrect header in the weight table",
                              "Incorrect sequence of rows in the weight table",
                              "Missing variable: {0} in the input WRF-Hydro runoff file",
                              "Incorrect dimensions of variable {0} in the input WRF-Hydro runoff file"]

    def dataValidation(self, in_nc):
        """Check the necessary dimensions and variables in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)
        for dim in self.dims_oi:
            if dim not in data_nc.dimensions.keys():
                data_nc.close()
                raise Exception("Invalid NetCDF dimensions ...")

        for var in self.vars_oi:
            if var not in data_nc.variables.keys():
                print var
                data_nc.close()
                raise Exception("Invalid NetCDF variables ...")
        
        data_nc.close()
        return

    def readInWeightTable(self, in_weight_table):
        """
        Read in weight table
        """
        
        print "Reading the weight table..."
        self.dict_list = {self.header_wt[0]:[], self.header_wt[1]:[], self.header_wt[2]:[],
                          self.header_wt[3]:[], self.header_wt[4]:[]}
                     
        with open(in_weight_table, "rb") as csvfile:
            reader = csv.reader(csvfile)
            self.count = 0
            for row in reader:
                if self.count == 0:
                    #check number of columns in the weight table
                    if len(row) < len(self.header_wt):
                        raise Exception(self.errorMessages[4])
                    #check header
                    if row[1:len(self.header_wt)] != self.header_wt[1:]:
                        raise Exception(self.errorMessages[5])
                    self.count += 1
                else:
                    for i in xrange(len(self.header_wt)):
                       self.dict_list[self.header_wt[i]].append(row[i])
                    self.count += 1

        self.size_streamID = len(set(self.dict_list[self.header_wt[0]]))

    def generateOutputInflowFile(self, out_nc, in_weight_table, tot_size_time):
        """
        Generate inflow file for RAPID
        """

        self.readInWeightTable(in_weight_table)
        # Create output inflow netcdf data
        print "Generating inflow file"
        data_out_nc = NET.Dataset(out_nc, "w", format = "NETCDF3_CLASSIC")
        dim_Time = data_out_nc.createDimension('Time', tot_size_time)
        dim_RiverID = data_out_nc.createDimension('rivid', self.size_streamID)
        var_m3_riv = data_out_nc.createVariable('m3_riv', 'f4', 
                                                ('Time', 'rivid'),
                                                fill_value=0)
        data_out_nc.close()
        #empty list to be read in later
        self.dict_list = {}
        
    def execute(self, nc_file_list, index_list, in_weight_table, 
                out_nc, grid_type):
        """The source code of the tool."""

        """The source code of the tool."""
        if not os.path.exists(out_nc):
            print "ERROR: Outfile has not been created. You need to run: generateOutputInflowFile function ..."
            raise Exception("ERROR: Outfile has not been created. You need to run: generateOutputInflowFile function ...")
            
        if len(nc_file_list) != len(index_list):
            print "ERROR: Number of runoff files not equal to number of indices ..."
            raise Exception("ERROR: Number of runoff files not equal to number of indices ...")
        
        self.readInWeightTable(in_weight_table)
        
        #get time size
        data_in_nc = NET.Dataset(nc_file_list[0])
        size_time = len(data_in_nc.dimensions['Time'])
        data_in_nc.close()

        #get indices of subset of data
        we_ind_all = [long(i) for i in self.dict_list[self.header_wt[2]]]
        sn_ind_all = [long(j) for j in self.dict_list[self.header_wt[3]]]

        # Obtain a subset of  runoff data based on the indices in the weight table
        min_we_ind_all = min(we_ind_all)
        max_we_ind_all = max(we_ind_all)
        min_sn_ind_all = min(sn_ind_all)
        max_sn_ind_all = max(sn_ind_all)
        
        index_new = []
        conversion_factor = None
        
        # start compute inflow
        data_out_nc = NET.Dataset(out_nc, "a", format = "NETCDF3_CLASSIC")
        
        #combine inflow data
        for nc_file_array_index, nc_file_array in enumerate(nc_file_list):

            index = index_list[nc_file_array_index]
            
            if not isinstance(nc_file_array, list): 
                nc_file_array = [nc_file_array]
            else:
                nc_file_array = nc_file_array
                
            full_data_subset = None

            for nc_file in nc_file_array:
                # Validate the netcdf dataset
                vars_oi_index = self.dataValidation(nc_file)

                #self.dataIdentify(nc_file, vars_oi_index)

                ''' Read the netcdf dataset'''
                data_in_nc = NET.Dataset(nc_file)

                '''Calculate water inflows'''
                print "Calculating water inflows for", os.path.basename(nc_file) , grid_type, "..."

                data_subset_all = data_in_nc.variables[self.vars_oi[2]][:,min_sn_ind_all:max_sn_ind_all+1, min_we_ind_all:max_we_ind_all+1]/1000 \
                                + data_in_nc.variables[self.vars_oi[3]][:,min_sn_ind_all:max_sn_ind_all+1, min_we_ind_all:max_we_ind_all+1]/1000
                len_time_subset_all = data_subset_all.shape[0]
                len_sn_subset_all = data_subset_all.shape[1]
                len_we_subset_all = data_subset_all.shape[2]
                data_subset_all = data_subset_all.reshape(len_time_subset_all, (len_sn_subset_all * len_we_subset_all))


                # compute new indices based on the data_subset_all
                index_new = []
                for r in range(0,self.count-1):
                    ind_sn_orig = sn_ind_all[r]
                    ind_we_orig = we_ind_all[r]
                    index_new.append((ind_sn_orig - min_sn_ind_all)*len_we_subset_all + (ind_we_orig - min_we_ind_all))

                # obtain a new subset of data
                data_subset_new = data_subset_all[:,index_new]
                
                #combine data
                if full_data_subset is None:
                    full_data_subset = data_subset_new
                else:
                    full_data_subset = NUM.add(full_data_subset, data_subset_new)


            # start compute inflow
            len_wt = len(self.dict_list[self.header_wt[0]])
            pointer = 0
            for stream_index in xrange(self.size_streamID):
                npoints = int(self.dict_list[self.header_wt[4]][pointer])
                # Check if all npoints points correspond to the same streamID
                if len(set(self.dict_list[self.header_wt[0]][pointer : (pointer + npoints)])) != 1:
                    print "ROW INDEX", pointer
                    print "COMID", self.dict_list[self.header_wt[0]][pointer]
                    raise Exception(self.errorMessages[2])

                area_sqm_npoints = [float(k) for k in self.dict_list[self.header_wt[1]][pointer : (pointer + npoints)]]
                area_sqm_npoints = NUM.array(area_sqm_npoints)
                area_sqm_npoints = area_sqm_npoints.reshape(1, npoints)
                data_goal = full_data_subset[:, pointer:(pointer + npoints)]

                ''''IMPORTANT NOTE: runoff variables in WRF-Hydro dataset is cumulative through time'''
                ro_stream = NUM.concatenate([data_goal[0:1,],
                            NUM.subtract(data_goal[1:,],data_goal[:-1,])]) * area_sqm_npoints
                try:
                    #ignore masked values
                    if ro_stream.sum() is NUM.ma.masked:
                        data_out_nc.variables['m3_riv'][index*size_time:(index+1)*size_time,stream_index] = 0
                    else:
                        data_out_nc.variables['m3_riv'][index*size_time:(index+1)*size_time,stream_index] = ro_stream.sum(axis=1)
                except ValueError:
                    print "M3", len(data_out_nc.variables['m3_riv'][index*size_time:(index+1)*size_time,stream_index]), data_out_nc.variables['m3_riv'][index*size_time:(index+1)*size_time,stream_index]
                    print "RO", len(ro_stream.sum(axis=1)), ro_stream.sum(axis=1)
                    raise

                pointer += npoints


        data_out_nc.close()
