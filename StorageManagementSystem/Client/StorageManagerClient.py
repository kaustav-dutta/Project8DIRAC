""" Class that contains client access to the StorageManagerDB handler.
"""
__RCSID__ = "2e7124e (2017-02-22 13:35:15 +0100) Philippe Charpentier <Philippe.Charpentier@cern.ch>"

import random

from DIRAC import S_OK, S_ERROR, gLogger
from DIRAC.Core.Base.Client                         import Client
from DIRAC.Core.Utilities.Proxy                     import executeWithUserProxy
from DIRAC.DataManagementSystem.Client.DataManager  import DataManager
from DIRAC.Resources.Storage.StorageElement         import StorageElement

def getFilesToStage( lfnList, jobState = None ):
  """ Utility that returns out of a list of LFNs those files that are offline,
      and those for which at least one copy is online
  """
  if not lfnList:
    return S_OK( {'onlineLFNs':[], 'offlineLFNs': {}} )

  dm = DataManager()

  lfnListReplicas = dm.getReplicasForJobs( lfnList, getUrl = False )
  if not lfnListReplicas['OK']:
    return lfnListReplicas

  if lfnListReplicas['Value']['Failed']:
    return S_ERROR( "Failures in getting replicas" )

  lfnListReplicas = lfnListReplicas['Value']['Successful']
  # Check whether there is any file that is only at a tape SE
  # If a file is reported here at a tape SE, it is not at a disk SE as we use disk in priority
  seToLFNs = dict()
  onlineLFNs = set()
  for lfn, ld in lfnListReplicas.iteritems():
    for se in ld:
      status = StorageElement( se ).getStatus()
      if not status['OK']:
        gLogger.error( "Could not get SE status", "%s - %s" % ( se, status['Message'] ) )
        return status
      if status['Value']['DiskSE']:
        # File is at a disk SE, no need to stage
        onlineLFNs.add( lfn )
        break
      else:
        seToLFNs.setdefault( se, list() ).append( lfn )

  offlineLFNsDict = {}
  if seToLFNs:
    # If some files are on Tape SEs, check whether they are online or offline
    if jobState:
      # Get user name and group from the job state
      userName = jobState.getAttribute( 'Owner' )
      if not userName[ 'OK' ]:
        return userName
      userName = userName['Value']

      userGroup = jobState.getAttribute( 'OwnerGroup' )
      if not userGroup[ 'OK' ]:
        return userGroup
      userGroup = userGroup['Value']
    else:
      userName = None
      userGroup = None
    result = _checkFilesToStage( seToLFNs, onlineLFNs,  # pylint: disable=unexpected-keyword-arg
                                 proxyUserName = userName,
                                 proxyUserGroup = userGroup,
                                 executionLock = True )
    if not result['OK']:
      return result
    offlineLFNs = set( lfnList ) - onlineLFNs

    for offlineLFN in offlineLFNs:
      ses = lfnListReplicas[offlineLFN].keys()
      if ses:
        offlineLFNsDict.setdefault( random.choice( ses ), list() ).append( offlineLFN )

  return S_OK( {'onlineLFNs':list( onlineLFNs ), 'offlineLFNs': offlineLFNsDict} )

@executeWithUserProxy
def _checkFilesToStage( seToLFNs, onlineLFNs ):
  """
  Checks on SEs whether the file is NEARLINE or ONLINE
  onlineLFNs is modified to contain the files found online
  """
  # Only check on storage if it is a tape SE
  failed = {}
  for se, lfnsInSEList in seToLFNs.iteritems():
    fileMetadata = StorageElement( se ).getFileMetadata( lfnsInSEList )
    if not fileMetadata['OK']:
      failed[se] = dict.fromkeys( lfnsInSEList, fileMetadata['Message'] )
    else:
      if fileMetadata['Value']['Failed']:
        failed[se] = fileMetadata['Value']['Failed']
      # is there at least one replica online?
      for lfn, mDict in fileMetadata['Value']['Successful'].iteritems():
        # SRM returns Cached, but others may only return Accessible
        if mDict.get( 'Cached', mDict['Accessible'] ):
          onlineLFNs.add( lfn )

  # If the file was found staged, ignore possible errors, but print out errors
  for se, failedLfns in failed.items():
    gLogger.error( "Errors when getting files metadata", 'at %s' % se )
    for lfn, reason in failedLfns.items():
      if lfn in onlineLFNs:
        gLogger.info( '%s: %s, but there is an online replica' % ( lfn, reason ) )
        failed[se].pop( lfn )
      else:
        gLogger.info( '%s: %s, no online replicas' % ( lfn, reason ) )
    if not failed[se]:
      failed.pop( se )
  if failed:
    gLogger.error( "Could not get metadata", "for %d files" % len( set( lfn for lfnList in failed.itervalues() for lfn in lfnList ) ) )
    return S_ERROR( "Could not get metadata for files" )

  return S_OK()


class StorageManagerClient( Client ):
  """ This is the client to the StorageManager service, so even if it is not seen, it exposes all its RPC calls
  """

  def __init__( self, **kwargs ):
    Client.__init__( self, **kwargs )
    self.setServer( 'StorageManagement/StorageManager' )
