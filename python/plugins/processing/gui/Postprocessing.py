# -*- coding: utf-8 -*-

"""
***************************************************************************
    Postprocessing.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""


__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import traceback
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessingFeedback)

from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.ProcessingResults import resultsList
from processing.core.ProcessingLog import ProcessingLog

#from processing.gui.ResultsDock import ResultsDock
from processing.gui.RenderingStyles import RenderingStyles

from processing.core.outputs import OutputRaster
from processing.core.outputs import OutputVector
from processing.core.outputs import OutputTable
from processing.core.outputs import OutputHTML

from processing.tools import dataobjects


def handleAlgorithmResults(alg, feedback=None, showResults=True):
    wrongLayers = []
    if feedback is None:
        feedback = QgsProcessingFeedback()
    feedback.setProgressText(QCoreApplication.translate('Postprocessing', 'Loading resulting layers'))
    i = 0
    for out in alg.outputs:
        feedback.setProgress(100 * i / float(len(alg.outputs)))
        if out.hidden or not out.open:
            continue
        if isinstance(out, (OutputRaster, OutputVector, OutputTable)):
            try:
                if hasattr(out, "layer") and out.layer is not None:
                    out.layer.setName(out.description)
                    QgsProject.instance().addMapLayers([out.layer])
                else:
                    if ProcessingConfig.getSetting(
                            ProcessingConfig.USE_FILENAME_AS_LAYER_NAME):
                        name = os.path.basename(out.value)
                    else:
                        name = out.description
                    dataobjects.load(out.value, name, alg.crs,
                                     RenderingStyles.getStyle(alg.commandLineName(),
                                                              out.name))
            except Exception:
                ProcessingLog.addToLog(ProcessingLog.LOG_ERROR,
                                       "Error loading result layer:\n" + traceback.format_exc())
                wrongLayers.append(out.description)
        elif isinstance(out, OutputHTML):
            resultsList.addResult(alg.getIcon(), out.description, out.value)
        i += 1

    QApplication.restoreOverrideCursor()
    if wrongLayers:
        msg = "The following layers were not correctly generated.<ul>"
        msg += "".join(["<li>%s</li>" % lay for lay in wrongLayers]) + "</ul>"
        msg += "You can check the log messages to find more information about the execution of the algorithm"
        feedback.reportError(msg)

    return len(wrongLayers) == 0
