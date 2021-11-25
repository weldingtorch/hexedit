import sys
import pickle
import sqlite3

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

import FileTabLoadUI
import MainWindowLoadUI


class SessionHandler():
    def __init__(self):
        self.con = sqlite3.connect("../PyQT5Ya/hexedit/Sessions.sqlite3")
        self.cur = self.con.cursor()
        self.create_table()

    def create_table(self):
        self.cur.execute("""
                            CREATE TABLE IF NOT EXISTS filedata
                            ([filetab_id] INTEGER PRIMARY KEY AUTOINCREMENT, [filepath] TEXT, [is_new] BOOL, [changes] BLOB)
                        """)
        self.cur.execute("""
                            CREATE TABLE IF NOT EXISTS file_length 
                            ([filetab_id] INTEGER PRIMARY KEY AUTOINCREMENT, [length] INTEGER)
                        """)
        self.cur.execute("""
                            CREATE TABLE IF NOT EXISTS preferences
                            ([filetab_id] INTEGER PRIMARY KEY AUTOINCREMENT, [byteorder] TEXT, [capitalize] BOOL)
                        """)
        self.con.commit()

    def close_session(self):
        self.con.commit()
        self.con.close()

    def get_ids(self):
        self.cur.execute("""
                            SELECT filetab_id FROM filedata
                        """)
        return self.cur.fetchall()


class MainWindow(QMainWindow):
    def __init__(self, session):
        self.session = session

        super().__init__()
        MainWindowLoadUI.setupUi(self)

        self.actionNew.triggered.connect(lambda: self.open_file(new=True))
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSaveAll.triggered.connect(lambda: self.save_file(save_all=True))
        self.actionClose.triggered.connect(lambda: self.close_file())
        self.actionCloseAll.triggered.connect(lambda: self.close_file(close_all=True))
        self.actionQuit.triggered.connect(self.close)
        self.tabs.tabCloseRequested.connect(self.close_file)

        self.show()
        self.load_session()

    def load_session(self):
        ids = self.session.get_ids()
        if ids:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Hexedit was closed incorrectly")
            msg_box.setText("Previous session was found!")
            msg_box.setInformativeText("Do you want to load it?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Yes)
            btn = msg_box.exec()

            if btn == QMessageBox.Yes.numerator:
                for id in ids:
                    try:
                        new_tab = FileTab(self, self.session, id=id[0])
                        self.tabs.addTab(new_tab, new_tab.filepath.split("\\")[-1])
                    except FileExistsError:
                        pass
            elif btn == QMessageBox.Cancel.numerator:
                self.close()

    def open_file(self, new=False):
        if not new:
            filepath = QFileDialog.getOpenFileName(self, "Open File", "")[0]
            if filepath == "":
                return -1
            tab_name = filepath.split("/")[-1]
        else:
            tab_name = "unnamed"

        new_tab = FileTab(self, self.session, tab_name, new)
        self.tabs.addTab(new_tab, tab_name)
        if not new:
            self.tabs.setTabToolTip(self.tabs.count() - 1, filepath)

    def save_file(self, save_all=False):
        if not save_all:
            tab = self.tabs.currentWidget()
            if tab is not None:
                tab.save()
        else:
            for tab_index in range(self.tabs.count()):
                self.tabs.widget(tab_index).save()

    def close_file(self, index=None, close_all=False):
        if not close_all:
            if index is None:
                tab = self.tabs.currentWidget()
                if tab is not None:
                    index = tab.index()
                else:
                    return -1
            else:
                tab = self.tabs.widget(index)
            if tab.close() == 0:
                tab.delete_data()
                self.tabs.removeTab(index)
        else:
            for _ in range(self.tabs.count()):
                tab = self.tabs.widget(0)
                if tab.close() == 0:
                    tab.delete_data()
                    self.tabs.removeTab(0)
                else:
                    return -1
            return 0

    def closeEvent(self, event):
        if self.close_file(close_all=True) == 0:
            event.accept()
        else:
            event.ignore()


class FileTab(QWidget):
    def __init__(self, parent, session, filepath=None, isNew=False, id=None):
        super().__init__(parent)

        self.session = session
        self.id = id
        self.data = None
        self.length = None
        self.byteorder = "big"
        self.cap = False

        if id is not None:
            self.load_data()
        else:
            self.filepath = filepath
            self.isNew = isNew
            self.changes = dict()

        self.LoadUI()
        if self.id is None:
            self.create_data()

    def load_data(self):
        self.cur.execute(f"""
                        SELECT filepath, is_new, changes, byteorder, capitalize 
                        FROM filedata INNER JOIN preferences USING (filetab_id) 
                        WHERE filetab_id = ?
                        """, (self.id,))
        filedata = self.cur.fetchall()
        if filedata:
            self.filepath, self.isNew, changes, self.byteorder, cap = filedata[0]
            self.changes = pickle.loads(changes)
            self.cap = bool(cap)
            if self.isNew:
                self.cur.execute("SELECT length FROM file_length WHERE filetab_id = ?", (self.id,))
                self.length = self.cur.fetchall()[0][0]
        else:
            self.filepath, self.isNew, self.changes, self.length = [None] * 4

    def create_data(self):
        self.cur.execute(f"""
                            INSERT INTO filedata(filepath, is_new, changes) 
                            VALUES(?, ?, ?)
                        """, (self.filepath, self.isNew, pickle.dumps(self.changes),))
        self.cur.execute(f"""
                            INSERT INTO preferences(byteorder, capitalize)
                            VALUES(?, ?)
                        """, (self.byteorder, self.cap,))
        self.cur.execute(f"""
                            INSERT INTO file_length(length) VALUES(?)
                        """, (self.length,))
        self.con.commit()

        self.id = self.cur.lastrowid

    def update_data(self):
        self.cur.execute("""
                            UPDATE filedata SET changes = ? WHERE filetab_id = ?
                        """, (pickle.dumps(self.changes), self.id,))
        self.cur.execute(f"""       
                            UPDATE preferences SET byteorder = ?, capitalize = ?
                            WHERE filetab_id = ?
                        """, (self.byteorder, self.cap, self.id,))
        self.cur.execute(f"""
                            UPDATE file_length SET length = ? WHERE filetab_id = ?
                        """, (self.length, self.id,))
        self.con.commit()

    def delete_data(self):
        self.cur.execute("""
                            DELETE FROM filedata WHERE filetab_id = ?
                        """, (self.id,))
        self.cur.execute("""
                            DELETE FROM preferences WHERE filetab_id = ?
                        """, (self.id,))
        self.cur.execute("""
                            DELETE FROM file_length WHERE filetab_id = ?
                        """, (self.id,))
        self.con.commit()

    def LoadUI(self):
        if not self.isNew:
            retry_flag = True
            while retry_flag:
                try:
                    with open(self.filepath, "rb") as file:
                        self.data = file.read()
                    self.length = len(self.data)
                    retry_flag = False

                except FileNotFoundError:
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle(self.filepath.split("\\")[0])
                    msg_box.setText("Error while opening file.")
                    msg_box.setInformativeText("File was moved or deleted. \n"
                                               "Do you want to remove this file from session?")
                    msg_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Yes | QMessageBox.Cancel)
                    msg_box.setDefaultButton(QMessageBox.Retry)
                    btn = msg_box.exec()

                    if btn == QMessageBox.Retry.numerator:
                        continue

                    elif btn == QMessageBox.Yes.numerator:
                        self.delete_data()

                    raise FileExistsError
        else:
            if self.length is None:
                self.length, ok = QInputDialog.getInt(self, "Set file size", "Enter file size in bytes",
                                                      256, 1, 16 ** 4, 16)
                if not ok:
                    self.close()
            self.data = bytearray(self.length)

        FileTabLoadUI.LoadUI(self)
        self.fill_table()
        self.update_repr(full_fill=True)

    def change_prefs(self, arg):
        obj_name = self.sender().objectName()
        if obj_name == "capitalize":
            self.cap = arg
        elif obj_name == "byteorder_combo":
            self.byteorder = arg

        self.update_data()
        self.fill_table()

    def fill_table(self):
        try:
            self.table.cellChanged.disconnect()
        except TypeError:
            pass
        if self.cap:
            forms = ("{:0>2X}", "{:0>7X}0")
        else:
            forms = ("{:0>2x}", "{:0>7x}0")

        self.table.setHorizontalHeaderLabels([forms[0].format(i) for i in range(16)] + ["text representation"])
        self.table.setVerticalHeaderLabels([forms[1].format(i) for i in range(self.table.rowCount())])

        for i in range(len(self.data)):
            self.table.setItem(i // 16, i % 16, QTableWidgetItem(forms[0].format(self.data[i])))
        for i in range((16 - len(self.data) % 16) % 16):
            self.table.setItem((len(self.data) + i) // 16, (len(self.data) + i) % 16, QTableWidgetItem(""))

        for pos in self.changes.keys():
            self.table.setItem(pos // 16, pos % 16, QTableWidgetItem(forms[0].format(self.changes[pos])))
        self.table.setFont(QFont("Consolas"))
        self.table.cellChanged.connect(self.add_change)

    def update_repr(self, full_fill=False):
        try:
            self.table.cellChanged.disconnect()
        except TypeError:
            pass
        if full_fill:
            for row in range(len(self.data) // 16 + 1):
                work_bytes = self.data[row * 16:min((row + 1) * 16, len(self.data))]
                letters = [chr(b) if chr(b).isprintable() else "." for b in work_bytes]
                new_item = QTableWidgetItem("".join(letters))
                new_item.setFont(QFont("Consolas"))
                self.table.setItem(row, 16, new_item)
        if self.changes:
            for pos in self.changes.keys():
                item = self.table.item(pos // 16, 16)  # text representation item
                old_repr = item.text()
                new_char = chr(self.changes[pos])
                if old_repr[pos % 16] == new_char:
                    continue
                if not new_char.isprintable():
                    new_char = "."
                new_repr = old_repr[:pos % 16] + new_char + old_repr[pos % 16 + 1:]
                item.setText(new_repr)
        self.table.cellChanged.connect(self.add_change)

    def add_change(self, row, column):
        self.table.cellChanged.disconnect()
        item = self.sender().item(row, column)
        if column != 16:
            pos = row * 16 + column
            text = item.text()
            if pos < self.length and len(text.strip(" ")) <= 2:
                try:
                    self.changes[pos] = int(text, 16)
                    self.update_data()
                except ValueError:
                    item.setText("00")
                self.update_repr()
            else:
                item.setText("")
        else:
            self.update_data()
        self.table.cellChanged.connect(self.add_change)

    def save(self):
        if self.changes:
            change_pos_list = self.changes.keys()
            new_data = bytearray([self.changes[pos] if pos in change_pos_list
                                  else self.data[pos] for pos in range(len(self.data))])
            if not self.isNew:
                with open(self.filepath, "wb") as file:
                    file.write(new_data)
            else:
                filename = QFileDialog.getSaveFileName(self, "Save File", "")[0]
                if filename:
                    with open(filename, "wb") as file:
                        file.write(new_data)
                else:
                    return -1

            self.changes.clear()
        return 0

    def close(self):
        if self.changes or self.isNew:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(self.filepath.split("\\")[-1])
            msg_box.setText("You have unsaved changes!")
            msg_box.setInformativeText("Do you want to save before closing file?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Yes)
            btn = msg_box.exec()

            if btn == QMessageBox.Yes.numerator:
                return self.save()

            elif btn == QMessageBox.Cancel.numerator:
                return -1

        return 0


if __name__ == '__main__':
    app = QApplication(sys.argv)

    session = SessionHandler()
    app.aboutToQuit.connect(session.close_session)

    MainWindow(session)
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
