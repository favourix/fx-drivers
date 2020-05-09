#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  fx-drivers
#
#  Copyright © 2019 Favourix <vladimir.kokes@favourix.com
#  This file is part of Favourix OS Driver manager.
#
#  Favourix is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  Favourix is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#
#  You should have received a copy of the GNU General Public License
#  along with Favourix; If not, see <http://www.gnu.org/licenses/>.

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QRadioButton
import sys
import devutils
import device

class MainForm(QtWidgets.QMainWindow):

        def __init__(self, **kwargs):
                super(MainForm, self).__init__(**kwargs)

                # Command line options
                cmd_line = device.parse_options()
                device.setup_logging(cmd_line)

                # Check for loading of ids files
                try:
                        device.load_ids()
                except FileNotFoundError:
                        device.log_error("Cannot load ids files")
                        no_ids = QMessageBox.critical(self, 'Error', "Cannot load ids files", QMessageBox.Ok , QMessageBox.Ok)
                        if no_ids == QMessageBox.Ok:
                                sys.exit()

                        return

                # Inicializing GPU vendor
                vendor=str(devutils.get_gpu_vendor())
                #vendor="virtualbox"
                gpuName = str(devutils.get_gpu_name())

                # Title, icon, window width
                self.setWindowTitle("Favourix Driver manager")
                self.setWindowIcon(QtGui.QIcon("src/drivers.svg"))
                self.setMinimumWidth(450)
                self.setMinimumHeight(200)

                # Main widget and BoxLayout
                form = QtWidgets.QWidget()
                formLayout = QtWidgets.QVBoxLayout()
                form.setLayout(formLayout)
                self.setCentralWidget(form)

                # Vendor branding
                vendorLayout = QtWidgets.QHBoxLayout()
                gpuNameLayout = QtWidgets.QHBoxLayout()
                self.vendorLabel = QtWidgets.QLabel()
                self.vendorLabel.setPixmap(QtGui.QPixmap("src/{0}.svg".format(vendor)).scaledToWidth(75))
                vendorLayout.addStretch()
                vendorLayout.addWidget(self.vendorLabel)
                vendorLayout.addStretch()
                gpuNameLayout.addStretch()
                gpuNameLayout.addWidget(QtWidgets.QLabel(gpuName))
                gpuNameLayout.addStretch()

                formLayout.addLayout(vendorLayout)
                formLayout.addLayout(gpuNameLayout)

                # Driver menu
                if (vendor != "nvidia" and vendor != "unknown"):
                        # first label layout
                        flLayout = QtWidgets.QHBoxLayout()
                        # second label layout
                        slLayout = QtWidgets.QHBoxLayout()
                        # Button layout
                        buttonLayout = QtWidgets.QHBoxLayout()

                        # closeButton setup
                        self.closeButton = QtWidgets.QPushButton("Close")
                        self.closeButton.setMinimumHeight(25)
                        self.closeButton.setMinimumWidth(50)
                        self.closeButton.setIcon(QtGui.QIcon("src/drop.png"))
                        self.closeButton.setIconSize(QtCore.QSize(24,24))
                        self.closeButton.clicked.connect(self.close_clicked)

                        # Widgets including to layouts
                        flLayout.addStretch()
                        flLayout.addWidget(QtWidgets.QLabel("Pre-installed MESA driver works pretty well."))
                        flLayout.addStretch()
                        slLayout.addStretch()
                        slLayout.addWidget(QtWidgets.QLabel("Your vendor has no better driver."))
                        slLayout.addStretch()
                        buttonLayout.addStretch()
                        buttonLayout.addWidget(self.closeButton)
                        buttonLayout.addStretch()

                        # Layouts including to formLayout
                        formLayout.addLayout(flLayout)
                        formLayout.addLayout(slLayout)
                        formLayout.addLayout(buttonLayout)

                elif vendor == "unknown":
                        # first label layout
                        flLayout = QtWidgets.QHBoxLayout()
                        # second label layout
                        slLayout = QtWidgets.QHBoxLayout()
                        # Button layout
                        buttonLayout = QtWidgets.QHBoxLayout()

                        # closeButton setup
                        self.closeButton = QtWidgets.QPushButton("Close")
                        self.closeButton.setMinimumHeight(25)
                        self.closeButton.setMinimumWidth(50)
                        self.closeButton.setIcon(QtGui.QIcon("src/drop.png"))
                        self.closeButton.setIconSize(QtCore.QSize(24,24))
                        self.closeButton.clicked.connect(self.close_clicked)

                        # Widgets including to layouts
                        flLayout.addStretch()
                        flLayout.addWidget(QtWidgets.QLabel("Pre-installed MESA driver probably works good."))
                        flLayout.addStretch()
                        slLayout.addStretch()
                        slLayout.addWidget(QtWidgets.QLabel("We have no other driver for your device."))
                        slLayout.addStretch()
                        buttonLayout.addStretch()
                        buttonLayout.addWidget(self.closeButton)
                        buttonLayout.addStretch()
                        
                        # Layouts including to formLayout
                        formLayout.addLayout(flLayout)
                        formLayout.addLayout(slLayout)
                        formLayout.addLayout(buttonLayout)

                else:
                        # Getting list of drivers
                        drivers = device.check_device()

                        # Label layout
                        labelLayout = QtWidgets.QHBoxLayout()
                        # Choose layout
                        chooseLayout = QtWidgets.QVBoxLayout()
                        # Button layout
                        buttonLayout = QtWidgets.QHBoxLayout()

                        # Buttons setup
                        self.applyButton = QtWidgets.QPushButton()
                        self.applyButton.setMinimumHeight(25)
                        self.applyButton.setMinimumWidth(50)
                        self.applyButton.setIcon(QtGui.QIcon("src/apply.png"))
                        self.applyButton.setIconSize(QtCore.QSize(24,24))
                        self.applyButton.clicked.connect(self.apply_clicked)
                        self.applyButton.setEnabled(False)
                        self.dropButton = QtWidgets.QPushButton()
                        self.dropButton.setMinimumHeight(25)
                        self.dropButton.setMinimumWidth(50)
                        self.dropButton.setIcon(QtGui.QIcon("src/drop.png"))
                        self.dropButton.setIconSize(QtCore.QSize(24,24))
                        self.dropButton.clicked.connect(self.drop_clicked)
                        self.dropButton.setEnabled(False)

                        # Widgets including to layouts
                        labelLayout.addWidget(QtWidgets.QLabel("Available drivers"))
                        labelLayout.addStretch()

                        index=0
                        for index, driver in enumerate(drivers):
                                chooseLayout.addWidget(QRadioButton("{}".format(driver)))

                        buttonLayout.addStretch()
                        buttonLayout.addWidget(self.dropButton)
                        buttonLayout.addWidget(self.applyButton)
                        buttonLayout.addStretch()


                        # Layouts including to formLayout
                        formLayout.addLayout(labelLayout)
                        formLayout.addLayout(chooseLayout)
                        formLayout.addLayout(buttonLayout)

                self.show()

                

        def setup(self):
                pass
        
        def close_clicked(self):
                sys.exit()

        def apply_clicked(self):
                pass

        def drop_clicked(self):
                pass

class App(QtWidgets.QApplication):

        def __init__(self):
                super(App, self).__init__(sys.argv)

        def build(self):
                self.main_form = MainForm()
                

                self.main_form.setup()
                sys.exit(self.exec_())

root = App()
root.build()