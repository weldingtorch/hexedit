from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


def setupUi(self):
    if not self.objectName():
        self.setObjectName(u"MainWindow")
    self.setWindowTitle(u"Hex Editor")
    self.setFixedSize(1120, 840)
    try:
        with open("colorscheme.txt") as colorscheme:
            stylesheet = colorscheme.read()

    except FileNotFoundError:
        stylesheet = u"""
                        QMenuBar {
                            background-color: rgb(116, 116, 116);
                            color: rgb(227, 227, 227);
                        }
                        QWidget#centralwidget {
                            background-color: rgb(100, 100, 100);
                        }
                        QTabWidget:pane {
                            background-color: rgb(75, 75, 75);
                            color: rgb(90, 90, 90);
                            border-color: rgb(0, 0, 0);
                        }
                        QTableWidget {
                            background-color: rgb(75, 75, 75);
                            color: rgb(90, 90, 90);
                            border-color: rgb(0, 0, 0);
                        }
                        QHeaderView {
                            background-color: rgb(75, 75, 75);
                            color: rgb(90, 90, 90);
                            border-color: rgb(0, 0, 0);
                        }
                        QCornerButton {
                            background-color: rgb(75, 75, 75);
                            color: rgb(90, 90, 90);
                            border-color: rgb(0, 0, 0);
                        }
                    """

        with open("colorscheme.txt", "w") as colorscheme:
            colorscheme.write(stylesheet)
    qApp.setStyleSheet(stylesheet)

    self.actionOpen = QAction(self)
    self.actionOpen.setObjectName(u"actionOpen")
    self.actionOpen.setText(u"Open")

    self.actionSave = QAction(self)
    self.actionSave.setObjectName(u"actionSave")
    self.actionSave.setText(u"Save Current")

    self.actionClose = QAction(self)
    self.actionClose.setObjectName(u"actionClose")
    self.actionClose.setText(u"Close Current")

    self.actionNew = QAction(self)
    self.actionNew.setObjectName(u"actionNew")
    self.actionNew.setText(u"New")

    self.actionSaveAll = QAction(self)
    self.actionSaveAll.setObjectName(u"actionSaveAll")
    self.actionSaveAll.setText(u"Save All")

    self.actionCloseAll = QAction(self)
    self.actionCloseAll.setObjectName(u"actionCloseAll")
    self.actionCloseAll.setText(u"Close All")

    self.actionQuit = QAction(self)
    self.actionQuit.setObjectName(u"actionQuit")
    self.actionQuit.setText(u"Quit")

    self.actionQuickHelp = QAction(self)
    self.actionQuickHelp.setObjectName(u"actionQuickHelp")
    self.actionQuickHelp.setText(u"Quick Help")

    self.actionShowHelp = QAction(self)
    self.actionShowHelp.setObjectName(u"actionShowHelp")
    self.actionShowHelp.setText(u"Show Help")

    self.centralwidget = QWidget(self)
    self.centralwidget.setObjectName(u"centralwidget")

    self.tabs = QTabWidget(self.centralwidget)
    self.tabs.setObjectName(u"tabs")
    self.tabs.setGeometry(QRect(0, 0, 1122, 841))
    self.tabs.setTabShape(QTabWidget.Rounded)
    self.tabs.setDocumentMode(False)
    self.tabs.setTabsClosable(True)
    self.tabs.setMovable(True)

    self.setCentralWidget(self.centralwidget)

    self.menuBar = QMenuBar(self)
    self.menuBar.setObjectName(u"menuBar")
    self.menuBar.setGeometry(QRect(0, 0, 1120, 26))

    self.menuFile = QMenu(self.menuBar)
    self.menuFile.setObjectName(u"menuFile")

    self.menuHelp = QMenu(self.menuBar)
    self.menuHelp.setObjectName(u"menuHelp")

    self.setMenuBar(self.menuBar)
    self.menuBar.addAction(self.menuFile.menuAction())
    self.menuFile.addAction(self.actionNew)
    self.menuFile.addAction(self.actionOpen)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionSave)
    self.menuFile.addAction(self.actionSaveAll)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionClose)
    self.menuFile.addAction(self.actionCloseAll)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionQuit)
    self.menuFile.setTitle(u"File")

    self.menuBar.addAction(self.menuHelp.menuAction())
    self.menuHelp.addAction(self.actionQuickHelp)
    self.menuHelp.addSeparator()
    self.menuHelp.addAction(self.actionShowHelp)
    self.menuHelp.setTitle(u"Help")

    self.tabs.setCurrentIndex(-1)

    QMetaObject.connectSlotsByName(self)
