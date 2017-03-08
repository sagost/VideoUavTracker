# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tableManagerUiClone.ui'
#
# Created: Sat Jan 17 20:54:37 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Clone(object):
    def setupUi(self, Clone):
        Clone.setObjectName("Clone")
        Clone.resize(375, 210)
        self.gridlayout = QtGui.QGridLayout(Clone)
        self.gridlayout.setObjectName("gridlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setObjectName("vboxlayout")
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        self.vboxlayout.addItem(spacerItem)
        self.label = QtGui.QLabel(Clone)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.lineDsn = QtGui.QLineEdit(Clone)
        self.lineDsn.setMouseTracking(False)
        self.lineDsn.setMaxLength(10)
        self.lineDsn.setFrame(True)
        self.lineDsn.setObjectName("lineDsn")
        self.vboxlayout.addWidget(self.lineDsn)
        self.label_3 = QtGui.QLabel(Clone)
        self.label_3.setObjectName("label_3")
        self.vboxlayout.addWidget(self.label_3)
        self.comboDsn = QtGui.QComboBox(Clone)
        self.comboDsn.setObjectName("comboDsn")
        self.vboxlayout.addWidget(self.comboDsn)
        self.gridlayout.addLayout(self.vboxlayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Clone)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.gridlayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        self.gridlayout.addItem(spacerItem1, 1, 0, 1, 1)

        self.retranslateUi(Clone)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Clone.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Clone.reject)
        QtCore.QMetaObject.connectSlotsByName(Clone)
        Clone.setTabOrder(self.lineDsn, self.comboDsn)
        Clone.setTabOrder(self.comboDsn, self.buttonBox)

    def retranslateUi(self, Clone):
        Clone.setWindowTitle(QtGui.QApplication.translate("Clone", "Clone field", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Clone", "A name for the new field:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Clone", "Insert at position:", None, QtGui.QApplication.UnicodeUTF8))

