from PyQt5.QtWidgets import QFrame, QTableWidget, QComboBox, QLineEdit, QToolButton, \
                            QCheckBox, QLabel, QPushButton, QHeaderView
from PyQt5.QtCore import QRect, Qt


def LoadUI(self):

    self.table = QTableWidget(len(self.data) // 16 + (len(self.data) % 16 != 0), 17, self)
    self.table.setGeometry(0, 40, 1121, 747)
  # загрузить из csv
    self.table.setStyleSheet("""QHeaderView::section{background-color: rgb(100, 100, 100);
                                                     color: rgb(200, 200, 200);
                                                     font:8pt "Consolas";
                                                    }
                                QTableWidget{color: rgb(200, 200, 200);
                                            }""")
    hh = self.table.horizontalHeader()
    vh = self.table.verticalHeader()

    hh.setSectionResizeMode(QHeaderView.Fixed)
    hh.setSectionResizeMode(16, QHeaderView.Stretch)
    hh.setFixedHeight(41)
    vh.setFixedWidth(80)
    hh.setMinimumSectionSize(44)
    hh.setMaximumSectionSize(44)
    vh.setMinimumSectionSize(44)
    vh.setMaximumSectionSize(44)

    self.frame = QFrame(self)
    self.frame.setObjectName(u"frame")
    self.frame.setGeometry(QRect(0, 0, 1121, 41))
    self.frame.setStyleSheet(u"background-color: rgb(116, 116, 116);\n"
                             "color: rgb(227, 227, 227);")
    self.frame.setFrameShape(QFrame.StyledPanel)
    self.frame.setFrameShadow(QFrame.Raised)

    self.byteorder_combo = QComboBox(self.frame)
    self.byteorder_combo.addItem("big")
    self.byteorder_combo.addItem("little")
    self.byteorder_combo.setCurrentText(self.byteorder)
    self.byteorder_combo.setObjectName(u"byteorder_combo")
    self.byteorder_combo.setEnabled(True)
    self.byteorder_combo.setGeometry(QRect(20, 10, 61, 22))
    self.byteorder_combo.setCurrentText(self.byteorder)
    self.byteorder_combo.currentTextChanged.connect(self.change_prefs)

    self.byteorder_label = QLabel(self.frame)
    self.byteorder_label.setObjectName(u"byteorder_label")
    self.byteorder_label.setGeometry(QRect(85, 10, 81, 20))
    self.byteorder_label.setText("-endian")

    self.ln_ed_search = QLineEdit(self.frame)
    self.ln_ed_search.setObjectName(u"ln_ed_search")
    self.ln_ed_search.setEnabled(False)
    self.ln_ed_search.setGeometry(QRect(370, 10, 271, 21))

    self.btn_search = QPushButton(self.frame)
    self.btn_search.setObjectName(u"btn_search")
    self.btn_search.setEnabled(False)
    self.btn_search.setGeometry(QRect(660, 10, 93, 21))
    self.btn_search.setText("Search")

    self.btn_search_prev = QToolButton(self.frame)
    self.btn_search_prev.setObjectName(u"btn_search_prev")
    self.btn_search_prev.setEnabled(False)
    self.btn_search_prev.setGeometry(QRect(910, 10, 27, 22))
    self.btn_search_prev.setCheckable(False)
    self.btn_search_prev.setChecked(False)
    self.btn_search_prev.setArrowType(Qt.UpArrow)

    self.btn_search_next = QToolButton(self.frame)
    self.btn_search_next.setObjectName(u"btn_search_next")
    self.btn_search_next.setEnabled(False)
    self.btn_search_next.setGeometry(QRect(940, 10, 27, 22))
    self.btn_search_next.setArrowType(Qt.DownArrow)

    self.label = QLabel(self.frame)
    self.label.setObjectName(u"label")
    self.label.setGeometry(QRect(764, 10, 141, 20))
    self.label.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
    self.label.setText("0 from 0 found")

    self.line = QFrame(self.frame)
    self.line.setObjectName(u"line")
    self.line.setGeometry(QRect(340, 0, 16, 41))
    self.line.setFrameShape(QFrame.VLine)
    self.line.setFrameShadow(QFrame.Sunken)

    self.capitalize = QCheckBox(self.frame)
    self.capitalize.setObjectName(u"capitalize")
    self.capitalize.setEnabled(True)
    self.capitalize.setGeometry(QRect(210, 10, 121, 20))
    self.capitalize.setChecked(self.cap)
    self.capitalize.setText("Capitalize Letters")
    self.capitalize.clicked.connect(self.change_prefs)
