# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Qgis2DocDockWidget
                                 A QGIS plugin
 Layerattribute in Wordvorlage einfügen
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2020 by eGov/GIS
        email                : gis@stadt.erlangen.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os, re, zipfile, shutil, win32com.client, time, tempfile, win32print, win32api

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtXml import QDomDocument
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QComboBox
from PyQt5.QtGui import QIcon

from qgis.core import QgsApplication
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgis_2_doc_dockwidget_base.ui'), resource_suffix='')


class Qgis2DocDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(Qgis2DocDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/plugins/qgis_2_doc/icon.svg'))

        self.l_hint.setMargin(5)
        self.tb_select_doc_filename.clicked.connect(self.selectDocument)
        self.pb_create_docs.clicked.connect(self.createDocuments)
        #iface.layerTreeView().currentLayerChanged.connect(self.setCurrentLayer)
        self.setCurrentLayer(iface.activeLayer())


    def restoreSettings(self):
        pass


    def setCurrentLayer(self, lyr):
        self.cb_layer.setLayer(lyr)


    def selectDocument(self):
        filename, filter = QFileDialog.getOpenFileName(None, 'Dokument wählen...', '', 'Worddateien (*.docx))')
        self.le_doc_filename.setText(filename)
        self.findReplaceFieldsInDocument(filename)


    def findReplaceFieldsInDocument(self, docx_filename):
        with open(docx_filename, 'rb') as f:
            zip = zipfile.ZipFile(f)
            doc = zip.read('word/document.xml')
        fields = set(re.findall(r"qgis_[a-z]+_", doc.decode('UTF-8')))
        fields = list(fields)
        fields.sort()
        self.tw_field_mapping.setRowCount(len(fields))
        r = 0
        for f in fields:
            self.tw_field_mapping.setItem(r, 0, QTableWidgetItem(f))
            self.tw_field_mapping.setCellWidget(r, 1, self.makeAttributeCombo(f))
            r += 1


    def makeAttributeCombo(self, doc_fieldname):
        doc_fieldname = doc_fieldname[5:-1]
        combo = QComboBox()
        combo.addItem('Bitte wählen...')
        attrs = [f.name() for f in self.cb_layer.currentLayer().fields()]
        attrs.sort()
        for a in attrs:
            combo.addItem(a)
        if doc_fieldname in attrs:
            combo.setCurrentText(doc_fieldname)
        return combo


    def makeFieldMappingDict(self):
        field_mapping = {}
        for r in range(self.tw_field_mapping.rowCount()):
            field_mapping[self.tw_field_mapping.item(r, 0).text()] = self.tw_field_mapping.cellWidget(r, 1).currentText()
        return field_mapping


    def createDocuments(self):
        default_printer = win32print.GetDefaultPrinter()
        tar_dir = self.le_out_folder.text()
        if tar_dir == '':
            tar_dir = r"C:\tmp"
        src_file = self.le_doc_filename.text()
        path, src_file_name = os.path.split(src_file)

        field_mapping = self.makeFieldMappingDict()

        doc_count = 0
        # Ein Dokument für jedes ausgewählte Feature erzeugen
        feat_ct = self.cb_layer.currentLayer().selectedFeatureCount()
        self.pb_doc_processing.setMaximum(feat_ct)
        self.pb_doc_processing.setValue(0)

        for feat in self.cb_layer.currentLayer().selectedFeatures():
            self.l_doc_processing.setText('Verarbeite {0} von {1}.'.format(doc_count + 1, feat_ct))
            QgsApplication.instance().processEvents()
            cur_doc = os.path.join(tar_dir, src_file_name.replace('.docx', '_ausgabe_{}.docx'.format(doc_count)))
            shutil.copy2(src_file, cur_doc)
            #with open(cur_doc, 'rb') as f:
            f = open(cur_doc, 'rb')
            zip = zipfile.ZipFile(f)
            docxml = zip.read('word/document.xml').decode('UTF-8')
            for k in field_mapping.keys():
                #print(k, feat[field_mapping[k]], doc.find(k))
                docxml = docxml.replace(k, feat[field_mapping[k]])
            self.writeAndCloseDocx(zip, docxml, cur_doc)
            f.close()

            ext = 'docx'
            if self.cb_secure.isChecked():
                self.convertDocxToPdf(cur_doc)
                if self.cb_delete_docx.isChecked():
                    os.remove(cur_doc)
                ext = 'pdf'

            if self.cb_direct_print.isChecked():
                win32api.ShellExecute(0, "print", cur_doc.replace('docx', ext), '/d:"%s"' % default_printer, ".", 0)

            doc_count += 1
            self.pb_doc_processing.setValue(doc_count)
            QgsApplication.instance().processEvents()

        self.l_doc_processing.setText('Fertig.')


    def writeAndCloseDocx(self, zip, xml_content, output_filename):
        #temporäres Verzeichnis erzeugen (virtuell?)
        tmp_dir = tempfile.mkdtemp()
        #docx Inhalt in temporäres Verzeichnis extrahieren
        zip.extractall(tmp_dir)
        # Inhalt überschreiben
        with open(os.path.join(tmp_dir, 'word/document.xml'), 'w') as f:
            #xmlstr = etree.tostring(xml_content, pretty_print=True)
            #f.write(xmlstr)
            f.write(xml_content)
        # Liste aller Dateien im ursprünglichen docx holen
        filenames = zip.namelist()
        # Neues zipfile erzeugen und alle Dateien dem Archiv hinzufügen
        with zipfile.ZipFile(output_filename, 'w') as docx:
            for filename in filenames:
                docx.write(os.path.join(tmp_dir, filename), filename)

        # temporäres Verzeicnis verräumen :-)
        shutil.rmtree(tmp_dir)


    def convertDocxToPdf(self, docx_filename):
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = True
        out_file = docx_filename.replace('docx', 'pdf')
        wdFormatPDF = 17
        time.sleep(3)
        print(docx_filename)
        doc = word.Documents.Open(docx_filename)
        doc.SaveAs(out_file, FileFormat = wdFormatPDF)
        try:
            doc.Close()
        except:
            pass
        word.Quit()


    def closeEvent(self, event):

        self.closingPlugin.emit()
        event.accept()