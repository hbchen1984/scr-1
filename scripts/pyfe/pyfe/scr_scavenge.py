#! /usr/bin/env python

import os, sys
from datetime import datetime
from scr_param import SCR_Param
from scr_env import SCR_Env
import scr_const
import scr_common
from scr_common import tracefunction, getconf, runproc
import scr_hostlist

# scavenge checkpoint files from cache to PFS
# check for pdsh / (clustershell) errors in case any nodes should be retried

# Usage: $prog [--jobset <nodeset>] [--up <nodeset> | --down <nodeset>] --id <id> --from <dir> --to <dir>

def print_usage(prog):
  print('')
  print('  Usage:  '+prog+' [--jobset <nodeset>] [--up <nodeset> | --down <nodeset>] --id <id> --from <dir> --to <dir>\n')

def scr_scavenge(argv,scr_env=None):
  # the verbose flag is used at the bottom of this method
  verbose = False

  bindir = scr_const.X_BINDIR
  prog = 'scr_scavenge'
  pdsh = scr_const.PDSH_EXE

  # TODO: need to be able to set these defaults via config settings somehow
  # for now just hardcode the values

  # lookup buffer size and crc flag via scr_param
  param = SCR_Param();

  buf_size = os.environ.get('SCR_FILE_BUF_SIZE')
  if buf_size is None:
    buf_size = str(1024*1024)

  crc_flag = os.environ.get('SCR_CRC_ON_FLUSH')
  if crc_flag is None:
    crc_flag = '--crc'
  elif crc_flag == '0':
    crc_flag = ''

  start_time = datetime.now()

  # tag output files with jobid
  if scr_env is None:
    scr_env = SCR_Env()
  jobid = scr_env.getjobid()
  if jobid is None:
    print(prog+': ERROR: Could not determine jobid.')
    return 1

  # read node set of job
  jobset = scr_env.conf['nodes']
  if jobset is None:
    print(prog+': ERROR: Could not determine nodeset.')
    return 1

  # read in command line arguments
  conf = getconf(argv,keyvals={'-j':'nodeset_job','--jobset':'nodeset_job','-u':'nodeset_up','--up':'nodeset_up','-d':'nodeset_down','--down':'nodeset_down','-i':'id','--id':'id','-f':'dir_from','--from':'dir_from','-t':'dir_to','--to':'dir_to'},togglevals={'-v':'verbose','--verbose':'verbose'})
  if conf is None:
    print_usage(prog)
    return 1
  if 'verbose' in conf:
    sys.settrace(tracefunction)

  # check that we have a nodeset for the job and directories to read from / write to
  if 'nodeset_job' not in conf or 'dataset_id' not in conf or 'dir_from' not in conf or 'dir_to' not in conf:
    print_usage(prog)
    return 1

  # get directories
  cntldir   = conf['dir_from']
  prefixdir = conf['dir_to']

  # get nodesets
  jobnodes  = scr_hostlist.expand(conf['nodeset_job'])
  upnodes = []
  downnodes = []
  if 'nodeset_down' in conf:
    downnodes = scr_hostlist.expand(conf['nodeset_down'])
    upnodes   = scr_hostlist.diff(jobnodes, downnodes)
  elif 'nodeset_up' in conf:
    upnodes   = scr_hostlist.expand(conf['nodeset_up'])
    downnodes = scr_hostlist.diff(jobnodes, upnodes)
  else:
    upnodes = jobnodes

  ##############################
  # format up and down node sets for pdsh command
  #################
  upnodes = scr_hostlist.compress(upnodes)
  downnodes_spaced = ' '.join(downnodes)

  # add dataset id option if one was specified (this is required from above)
  # set the dataset flag
  dset = conf['dataset_id']

  # build the output filenames
  output = prefixdir+'/.scr/scr.dataset.$dset/$prog.pdsh.o.'+jobid #jobid needs to be set above #########
  error  = prefixdir+'/.scr/scr.dataset.$dset/$prog.pdsh.e.'+jobid

  cmd = ''

  # log the start of the scavenge operation
  returncode = scr_common.log(bindir=bindir,prefix=prefixdir,jobid=jobid,event_type='SCAVENGE_START',event_dset=dset,event_start=str(start_time))
  if returncode != 0:
    print(err)
    print('scr_log_event returned '+str(returncode))
    return 1

  # gather files via pdsh
  #### need to fix %h #########
  argv = ['srun','-n','1','-N','1','-w','%h',bindir+'/scr_copy','--cntldir',cntldir,'--id',dset,'--prefix',prefixdir,'--buf',buf_size,crc_flag,downnodes_spaced]
  #$cmd = "srun -n 1 -N 1 -w %h $bindir/scr_copy --cntldir $cntldir --id $dset --prefix $prefixdir --buf $buf_size $crc_flag $downnodes_spaced";
  err, returncode = runproc(argv=argv,getstderr=True)
  if returncode!=0:
    print(err)
    print('scr_copy returned '+str(returncode))
    return 1

  print(prog+': '+str(datetime.now()))

  ##### this top comand (where output redirected to file) was commented out ?
  # Does not work with "$cmd" for some reason using -Rexec
  #print "$prog: $pdsh -Rexec -f 256 -S -w '$upnodes' \"$cmd\" >$output 2>$error\n";
  #             '$pdsh -Rexec-f 256 -S -w '$upnodes'  "$cmd"  >$output 2>$error';
  #### need to expand %h ######
  argv = [pdsh,'-Rexec','-f','256','-S','-w',upnodes,'srun','-n1','-N1','-w','%h',bindir+'/scr_copy','--cntldir',cntldir,'--id',dset,'--prefix',prefixdir,'--buf',buf_size,crc_flag,downnodes_spaced]
  #print "$prog: $pdsh -Rexec -f 256 -S -w '$upnodes' srun -n1 -N1 -w %h 
  #$bindir/scr_copy --cntldir $cntldir --id $dset --prefix $prefixdir --buf $buf_size $crc_flag $downnodes_spaced";
  #             '$pdsh -Rexec -f 256 -S -w '$upnodes' srun -n1 -N1 -w %h 
  #$bindir/scr_copy --cntldir $cntldir --id $dset --prefix $prefixdir --buf $buf_size $crc_flag $downnodes_spaced';
  out, returncode = runproc(argv=argv,getstdout=True,getstderr=True)
  if returncode!=0:
    print(out[1])
    print('pdsh returned '+str(returncode))
    #sys.exit(1)
  # print pdsh output to screen
  if verbose==True:
    if len(out[0])>0:
      print('pdsh: stdout: cat '+output)
      print(out[0])
    if len(out[1])>0:
      print('pdsh: stderr: cat '+error)
      print(out[1])

  # TODO: if we knew the total bytes, we could register a transfer here in addition to an event
  # get a timestamp for logging timing values
  end_time = datetime.now()
  diff_time = end_time - start_time
  scr_common.log(bindir=bindir,prefix=prefixdir,jobid=jobid,event_type='SCAVENGE_END',event_dset=dset,event_start=str(start_time),event_secs=str(diff_time))
  return 0

if __name__=='__main__':
  ret = scr_scavenge(sys.argv[1:])
  print('scr_scavenge returned '+str(ret))

