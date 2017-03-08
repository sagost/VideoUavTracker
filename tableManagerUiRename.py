# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tableManagerUiRename.ui'
#
# Created: Sun May 25 01:26:37 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Rename(object):
    def setupUi(self, Rename):
        Rename.setObjectName("Rename")
        Rename.resize(QtCore.QSize(QtCore.QRect(0,0,397,126).size()).expandedTo(Rename.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(Rename)
        self.gridlayout.setObjectName("gridlayout")

        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setObjectName("vboxlayout")

        self.label = QtGui.QLabel(Rename)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)

        self.lineEdit = QtGui.QLineEdit(Rename)
        self.lineEdit.setMouseTracking(False)
        self.lineEdit.setMaxLength(10)
        self.lineEdit.setFrame(True)
        self.lineEdit.setObjectName("lineEdit")
        self.vboxlayout.addWidget(self.lineEdit)
        self.gridlayout.addLayout(self.vboxlayout,0,0,1,1)

        self.buttonBox = QtGui.QDialogButtonBox(Rename)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.gridlayout.addWidget(self.buttonBox,2,0,1,1)

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,1,0,1,1)

        self.retranslateUi(Rename)
        QtCore.QObject.connect(self.buttonBox,QtCore.SIGNAL("accepted()"),Rename.accept)
        QtCore.QObject.connect(self.buttonBox,QtCore.SIGNAL("rejected()"),Rename.reject)
        QtCore.QMetaObject.connectSlotsByName(Rename)

    def retranslateUi(self, Rename):
        Rename.setWindowTitle(QtGui.QApplication.translate("Rename", "Rename field", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Rename", "Enter new field name:", None, QtGui.QApplication.UnicodeUTF8))

