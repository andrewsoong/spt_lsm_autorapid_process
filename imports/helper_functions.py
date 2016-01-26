# -*- coding: utf-8 -*-
##
##  helper_functions.py
##  spt_erai_autorapid_process
##
##  Created by Alan D. Snow 2016.
##  Copyright © 2016 Alan D Snow. All rights reserved.
##

import os
#----------------------------------------------------------------------------------------
# HELPER FUNCTIONS
#----------------------------------------------------------------------------------------
def partition(lst, n):
    """
        Divide list into n equal parts
    """
    q, r = divmod(len(lst), n)
    indices = [q*i + min(i,r) for i in xrange(n+1)]
    return [lst[indices[i]:indices[i+1]] for i in xrange(n)], \
           [range(indices[i],indices[i+1]) for i in xrange(n)]

def get_valid_watershed_list(input_directory):
    """
    Get a list of folders formatted correctly for watershed-subbasin
    """
    valid_input_directories = []
    for directory in os.listdir(input_directory):
        if os.path.isdir(os.path.join(input_directory, directory)) \
            and len(directory.split("-")) == 2:
            valid_input_directories.append(directory)
        else:
            print directory, "incorrectly formatted. Skipping ..."
    return valid_input_directories

def get_watershed_subbasin_from_folder(folder_name):
    """
    Get's the watershed & subbasin name from folder
    """
    input_folder_split = folder_name.split("-")
    watershed = input_folder_split[0].lower()
    subbasin = input_folder_split[1].lower()
    return watershed, subbasin