''' Utility Class for threaded agents (e.g. TransformationAgent)
    Mostly for logging
'''

import time
from DIRAC import gLogger

__RCSID__ = "247ca20 (2017-01-05 17:04:26 +0100) Philippe Charpentier <Philippe.Charpentier@cern.ch>"

AGENT_NAME = ''

class TransformationAgentsUtilities( object ):
  ''' logging utilities for threaded TS agents
  '''

  def __init__( self ):
    ''' c'tor
    '''
    self.transInThread = {}
    self.debug = False

  def __threadForTrans( self, transID ):
    try:
      return self.transInThread.get( transID, ' [None] [%s] ' % transID ) + AGENT_NAME + '.'
    except NameError:
      return ''

  def _logVerbose( self, message, param = '', method = "execute", transID = 'None', reftime = None ):
    ''' verbose '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    if self.debug:
      gLogger.info( '(V) ' + self.__threadForTrans( transID ) + method + ' ' + message, param )
    else:
      gLogger.verbose( self.__threadForTrans( transID ) + method + ' ' + message, param )

  def _logDebug( self, message, param = '', method = "execute", transID = 'None', reftime = None ):
    ''' debug '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    gLogger.debug( self.__threadForTrans( transID ) + method + ' ' + message, param )

  def _logInfo( self, message, param = '', method = "execute", transID = 'None', reftime = None ):
    ''' info '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    gLogger.info( self.__threadForTrans( transID ) + method + ' ' + message, param )

  def _logWarn( self, message, param = '', method = "execute", transID = 'None', reftime = None ):
    ''' warn '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    gLogger.warn( self.__threadForTrans( transID ) + method + ' ' + message, param )

  def _logError( self, message, param = '', method = "execute", transID = 'None', reftime = None ):
    ''' error '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    gLogger.error( self.__threadForTrans( transID ) + method + ' ' + message, param )

  def _logException( self, message, param = '', lException = False, method = "execute", transID = 'None', reftime = None ):
    ''' exception '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    gLogger.exception( self.__threadForTrans( transID ) + method + ' ' + message, param, lException )

  def _logFatal( self, message, param = '', method = "execute", transID = 'None', reftime = None ):
    ''' error '''
    if reftime is not None:
      method += " (%.1f seconds)" % ( time.time() - reftime )
    gLogger.fatal( self.__threadForTrans( transID ) + method + ' ' + message, param )

  def _transTaskName( self, transID, taskID ):
    return str( transID ).zfill( 8 ) + '_' + str( taskID ).zfill( 8 )

  def _parseTaskName( self, taskName ):
    try:
      return ( int( x ) for x in taskName.split( '_' ) )
    except Exception:
      return ( 0, 0 )
