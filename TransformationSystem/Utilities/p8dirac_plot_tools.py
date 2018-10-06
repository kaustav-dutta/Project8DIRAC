#!/usr/bin/env python

from DIRAC.Core.Base import Script
Script.parseCommandLine()

from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Resources.Catalog.FileCatalogClient import FileCatalogClient
from DIRAC.ConfigurationSystem.Client.Helpers.Operations import Operations
from DIRAC import gLogger, gConfig, S_OK, S_ERROR

import os
import sys
import json
import collections
import pdb
import subprocess

ops_dict = Operations().getOptionsDict('Transformations/')
if not ops_dict['OK']:
    print('Failed to get SE information from DIRAC Operation config: %s'
            % ops_dict['Message'])
    sys.exit(-9)

ops_dict = ops_dict['Value']
PROD_DEST_DATA_SE = ops_dict.get('ProdDestDataSE', 'PNNL-PIC-SRM-SE')
PROD_DEST_MONITORING_SE = ops_dict.get('ProdDestMonitoringSE', '')

def check_lfn_health(lfn, software_tag):
    status = os.system("source /cvmfs/hep.pnnl.gov/project8/katydid/" + software_tag + "/setup.sh\nroot -b " + lfn + " -q")
    return status
  
def getPlotJobLFNs():
    # Get the LFNs associated with the job on the machine
    jobID = int(os.environ['JOBID'])

    # Get the input data
    dirac = Dirac()
    res = dirac.getJobInputData(jobID)
    if not res['OK']:
        print('Failed to get job input data: %s' % res['Message'])
        sys.exit(-9)

    # Try to extract the LFNs
    lfns = []
    try:
        lfns = res['Value'][jobID]
    except ValueError:
        print('Failed to extract LFN information')
        sys.exit(-9)

    # Clean up LFN
    input_lfns = [lfn.replace('LFN:', '') for lfn in lfns]
    return input_lfns

def quality_plots(input_file, tree_name,output_dir=None):
    '''
    Create quality plots of the relevant quantities contained into the tree of a root file.
    The plots are saved as pdf in the output_dir.
    Some cosmetic elements require the name of the files to be as events_000001097_katydid_v2.7.0_concat.root
    If changed, modify #1
    '''
    # variable to plot
    plotted_var = [
        'Event.fStartTimeInAcq',
        'Event.fTimeLength',
        'Event.fStartFrequency',
        'Event.fFirstTrackSlope',
        'Event.fFirstTrackTimeLength',
        'Event.fTracks.fSlope',
        'Event.fTotalEventSequences'
    ]
    # title for the x axis
    title_plotted_var = [
        'StartTimeInAcq [s]',
        'TimeLength [s]',
        'StartFrequency [Hz]',
        'FirstTrackSlope [Hz/s]',
        'FirstTrackTimeLength [s]',
        'Tracks Slope [Hz/s]',
        'Number of tracks per event'
    ]
    # enable/disable log y scale 
    scale_plotted_var = [
        0,
        1,
        0,
        0,
        1,
        0,
        1
    ]

    #more complex plots (in case of failure)
    more_complex_plot = [
        'JumpSize',
        'JumpSizeBetweenEvents',
        'JumpLength',
        'JumpLengthClose',
        'TrackEventLengths',
        'NumberTracksInEvent'
    ]
    more_complex_plot_title = [
        "Jump size [MHz]",
        "Jump size [MHz]",
        "Jump length between events [s]",
        "Jump length between events [s]",
        "Time [s]",
        "Number of tracks per event"
    ]

    # Transform list into single element
    if isinstance(input_file,list):
        input_file = input_file[0]
    input_filename = os.path.basename(os.path.splitext(input_file)[0])

    list_pfn_plots = []

    # Timestamp box
    timestampBox = ROOT.TPaveText(0.001,
                       0.001,
                       0.45,
                       0.06,
                       "BRNDC")
    timestampBox.SetTextColor(1)
    timestampBox.SetFillColor(0)
    timestampBox.SetTextAlign(12)
    timestampBox.SetTextSize(0.04)
    timestampBox.SetBorderSize(1)
    timestampBox.AddText(datetime.datetime.now().strftime("%a, %d. %b %Y %I:%M:%S%p UTC"))
    
    # empty tree box
    emptyTreeBox = ROOT.TPaveText(0.31,
                       0.41,
                       0.6,
                       0.6)
                    #    "BRNDC")
    emptyTreeBox.SetTextColor(4)
    emptyTreeBox.SetFillColor(0)
    emptyTreeBox.SetTextAlign(22)
    emptyTreeBox.SetTextAngle(45)
    emptyTreeBox.SetTextSize(0.04)
    emptyTreeBox.SetBorderSize(0)
    emptyTreeBox.AddText("Tree {}".format(tree_name))
    emptyTreeBox.AddText("does not exist")

    # Cosmetic #1
    title = input_file.replace("_"," ")
    title = title.replace("events ","Run #")
    title = title.replace("katydid","Katydid")
    title = title.replace("concat","")
    title = title.replace(".root","")

    print('postprocessing: Opening root file {}'.format(input_filename))
    file = ROOT.TFile.Open(str(input_file),'r')
    print('postprocessing: Opening tree {}'.format(tree_name))

    # Loop that will generate empty plots if the tree does not exist
    can =  ROOT.TCanvas("data_quality","data_quality",600,400)
    if not file.GetListOfKeys().Contains(str(tree_name)):
        print('postprocessing: tree name given ({}) is not in root file: will create empty plots!'.format(tree_name))
        htemp = ROOT.TH1F("htemp","Temporary histo",100,0,1)
        print('postprocessing: Generating basic plots')
        for i,var in enumerate(plotted_var):
            htemp.SetTitle(title)
            htemp.GetXaxis().SetTitle(title_plotted_var[i])
            htemp.Draw()
            timestampBox.Draw()
            emptyTreeBox.Draw()
            filename = str(input_filename)+'_'+str(var).replace('.','_')+'.pdf'
            can.SetLogy(scale_plotted_var[i])
            if output_dir is None:
                can.SaveAs(filename)
                list_pfn_plots.append(filename)
            else:
                can.SaveAs(os.path.join(output_dir,filename))
                list_pfn_plots.append(os.path.join(output_dir,filename))
            can.SetLogy(0)
        print('postprocessing: Generating more complex plots')
        for i,var in enumerate(more_complex_plot):
            htemp.SetTitle(title)
            htemp.GetXaxis().SetTitle(more_complex_plot_title[i])
            htemp.Draw()
            timestampBox.Draw()
            emptyTreeBox.Draw()
            filename = str(input_filename)+'_'+str(var).replace('.','_')+'.pdf'
            # can.SetLogy(scale_plotted_var[i])
            if output_dir is None:
                can.SaveAs(filename)
                list_pfn_plots.append(filename)
            else:
                can.SaveAs(os.path.join(output_dir,filename))
                list_pfn_plots.append(os.path.join(output_dir,filename))
            can.SetLogy(0)
        return list_pfn_plots
    
    # Proper generation of the plots if the tree exists
    tree = file.Get(str(tree_name))
    print('postprocessing: Generating basic plots')
    for i,var in enumerate(plotted_var):
        print('postprocessing: Generating {} histogram'.format(str(var)))
        tree.Draw(str(var))
        htemp = ROOT.gPad.GetPrimitive("htemp")
        htemp.SetTitle(title)
        htemp.GetXaxis().SetTitle(title_plotted_var[i])
        htemp.Draw()
        timestampBox.Draw()

        filename = str(input_filename)+'_'+str(var).replace('.','_')+'.pdf'
        can.SetLogy(scale_plotted_var[i])
        if output_dir is None:
            can.SaveAs(filename)
            list_pfn_plots.append(filename)
        else:
            can.SaveAs(os.path.join(output_dir,filename))
            list_pfn_plots.append(os.path.join(output_dir,filename))
        can.SetLogy(0)

    print('postprocessing: Generating more complex plots')

    print('postprocessing: Generating {} histogram'.format("jump size"))
    jumpSize = []
    # variable for the jump length and cut jump size
    startTimeTrack = []
    endTimeTrack = []
    startFreqTrack = []
    endFreqTrack = []
    jumpLength = []
    jumpLengthClose = []
    jumpSizeBetweenEvents = []
    jumpSizeBetweenEventsCut = []
    for iEntry in range(tree.GetEntries()):
        tree.GetEntry(iEntry)
        startTimeTrack.append(tree.GetLeaf("fStartTimeInRunC").GetValue())
        endTimeTrack.append(tree.GetLeaf("fEndTimeInRunC").GetValue())
        startFreqTrack.append(tree.GetLeaf("fStartFrequency").GetValue())
        endFreqTrack.append(tree.GetLeaf("fEndFrequency").GetValue())
        for i in range(1,tree.GetLeaf("fTracks.fStartFrequency").GetLen()):
            jumpSize.append(-tree.GetLeaf("fTracks.fStartFrequency").GetValue(i)+tree.GetLeaf("fTracks.fEndFrequency").GetValue(i-1))
    for iValue in range(len(startTimeTrack)-1):
        jumpLength.append(+endTimeTrack[iValue]-startTimeTrack[iValue+1])
        jumpSizeBetweenEvents.append(-startFreqTrack[iValue+1]+endFreqTrack[iValue])
        if -endTimeTrack[iValue]+startTimeTrack[iValue+1]>-0.2 and -endTimeTrack[iValue]+startTimeTrack[iValue+1] <0.2:
            jumpLengthClose.append(endTimeTrack[iValue]-startTimeTrack[iValue+1])
            jumpSizeBetweenEventsCut.append(-startFreqTrack[iValue+1]+endFreqTrack[iValue])

def uploadJobOutputRoot():
    dirac = Dirac()
    ############################
    ## Get Merge LFNs  #########
    ############################
    lfn_list = getPlotJobLFNs()
    print(lfn_list)
    if len(lfn_list) == 0:
        print('No ROOT/HDF5 files found')
        sys.exit(-9)

    ################################
    # Get all lfns based on run_id # . --- Do we need this step??
    ################################
    try:
        fc = FileCatalogClient()
    except Exception:
        print("Failed to initialize file catalog object.")
        sys.exit(-9)
    metadata = fc.getFileUserMetadata(lfn_list[0])
    run_id = metadata['Value']['run_id']
    software_tag = metadata['Value']['SoftwareVersion']
    config_tag = metadata['Value']['ConfigVersion']
    meta = {}
    meta['run_id'] = run_id
    meta['DataExt'] = 'root'
    meta['DataFlavor'] = 'event'
    meta['DataLevel'] = 'merged'
    verifiedlfnlist = fc.findFilesByMetadata(meta)
    verifiedlfnlist = verifiedlfnlist['Value']
    print(verifiedlfnlist)

    ########################
    # Check health of LFNs #
    ########################
    lfn_good_list = []
    lfn_bad_list = []
    for lfn in verifiedlfnlist:
        status = check_lfn_health(lfn, software_tag)
        if status > 0:
            lfn_good_list.append(lfn)
        else:
            lfn_bad_list.append(lfn)
    if len(lfn_good_list) < 1:
        sys.exit(-9)
    dirname = os.path.dirname(lfn_good_list[0])
    basename = os.path.basename(lfn_good_list[0])
    datatype_dir = dirname.replace('ts_processed', 'plots')
    software_dir = os.path.join(datatype_dir, 'katydid_%s' % software_tag)
    config_dir = os.path.join(software_dir, 'termite_%s' % config_tag)

    ################
    # Plot #
    ################
    print('p8dirac_postprocessing: postprocessing.quality_plots({},...)'.format(basename))
    list_pfn_plots = quality_plots(basename, 'multiTrackEvents')
    if len(list_pfn_plots) > 0:
        print('postprocessing: plots done\n')
    else:
        print('failed to create plots for %s.' %(basename))
        
    ###############
    # Upload File #
    ###############
    for file in list_pfn_plots:
        event_lfn = config_dir + '/' + file
        event_pfn = os.getcwd() + '/' + file
        res = dirac.addFile(event_lfn, event_pfn, PROD_DEST_DATA_SE)
        if not res['OK']:
            print('Failed to upload plot file %s to %s.' % (event_pfn, event_lfn))
            sys.exit(-9)

    ###################
    # Change metadata #
    ###################
    metadata['DataLevel'] = 'plots'
    res = fc.setMetadata(datatype_dir, metadata)
    if not res['OK']:
        print('Failed to register metadata to LFN %s: %s' % (datatype_dir, metadata))
        sys.exit(-9)

    ####################
    # Update Ancestory #
    ####################
    for file in list_pfn_plots:
        event_lfn = config_dir + '/' + file
        ancestry_dict = {}
        ancestry_dict[event_lfn] = {'Ancestors': lfn_good_list}
        res = fc.addFileAncestors(ancestry_dict)
        if not res['OK']:
            print('Failed to register ancestors: %s' % res['Message'])
            sys.exit(-9)

