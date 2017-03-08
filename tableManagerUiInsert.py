# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tableManagerUiInsert.ui'
#
# Created: Tue Jan 13 22:17:13 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Insert(object):
    def setupUi(self, Insert):
        Insert.setObjectName("Insert")
        Insert.resize(420, 260)
        self.gridlayout = QtGui.QGridLayout(Insert)
        self.gridlayout.setObjectName("gridlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = QtGui.QLabel(Insert)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.lineName = QtGui.QLineEdit(Insert)
        self.lineName.setMouseTracking(False)
        self.lineName.setMaxLength(10)
        self.lineName.setFrame(True)
        self.lineName.setObjectName("lineName")
        self.vboxlayout.addWidget(self.lineName)
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.vboxlayout.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(Insert)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.vboxlayout.addWidget(self.label_2)
        self.comboType = QtGui.QComboBox(Insert)
        self.comboType.setMaxVisibleItems(3)
        self.comboType.setObjectName("comboType")
        self.vboxlayout.addWidget(self.comboType)
        spacerItem1 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.vboxlayout.addItem(spacerItem1)
        self.label_3 = QtGui.QLabel(Insert)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.vboxlayout.addWidget(self.label_3)
        self.comboPos = QtGui.QComboBox(Insert)
        self.comboPos.setObjectName("comboPos")
        self.vboxlayout.addWidget(self.comboPos)
        self.gridlayout.addLayout(self.vboxlayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Insert)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.gridlayout.addWidget(self.buttonBox, 3, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem2, 1, 0, 1, 1)

        self.retranslateUi(Insert)
        self.comboType.setCurrentIndex(-1)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Insert.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Insert.reject)
        QtCore.QMetaObject.connectSlotsByName(Insert)
        Insert.setTabOrder(self.lineName, self.comboType)
        Insert.setTabOrder(self.comboType, self.comboPos)
        Insert.setTabOrder(self.comboPos, self.buttonBox)

    def retranslateUi(self, Insert):
        Insert.setWindowTitle(QtGui.QApplication.translate("Insert", "Insert field", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Insert", "Field name:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Insert", "Field type:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Insert", "Insert at position:", None, QtGui.QApplication.UnicodeUTF8))

