# $HeadURL$
__RCSID__ = "754cc67 (2016-12-06 10:31:00 +0100) Christophe Haen <chaen@pclhcb31.dyndns.cern.ch>"

from DIRAC.FrameworkSystem.Client.Logger import Logger

class SubSystemLogger( Logger ):

  def __init__( self, subName, masterLogger, child = True ):
    Logger.__init__( self )
    self.__child = child
    self._minLevel = masterLogger._minLevel
    for attrName in dir( masterLogger ):
      attrValue = getattr( masterLogger, attrName )
      if isinstance( attrValue, basestring ):
        setattr( self, attrName, attrValue )
    self.__masterLogger = masterLogger
    self._subName = subName

  def processMessage( self, messageObject ):
    if self.__child:
      messageObject.setSubSystemName( self._subName )
    else:
      messageObject.setSystemName( self._subName )
    self.__masterLogger.processMessage( messageObject )
