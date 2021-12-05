import sys
import os
import pickle
import sqlite3
import webbrowser
import random

from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import *

import FileTabLoadUI
import MainWindowLoadUI


class SessionHandler():
    def __init__(self):
        self.con = sqlite3.connect("Sessions.sqlite3")
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

    def get_filedata(self, filetab_id):
        self.cur.execute(f"""
                            SELECT filepath, is_new, changes, byteorder, capitalize 
                            FROM filedata INNER JOIN preferences USING (filetab_id) 
                            WHERE filetab_id = ?
                        """, (filetab_id,))
        return self.cur.fetchall()[0]

    def get_filelength(self, filetab_id):
        self.cur.execute("SELECT length FROM file_length WHERE filetab_id = ?", (filetab_id,))
        return self.cur.fetchall()[0][0]

    def set_filedata(self, filetab):
        self.cur.execute(f"""
                            INSERT INTO filedata(filepath, is_new, changes) 
                            VALUES(?, ?, ?)
                        """, (filetab.filepath, filetab.is_new, pickle.dumps(filetab.changes),))
        self.cur.execute(f"""
                            INSERT INTO preferences(byteorder, capitalize)
                            VALUES(?, ?)
                        """, (filetab.byteorder, filetab.cap,))
        self.cur.execute(f"""
                            INSERT INTO file_length(length) VALUES(?)
                        """, (filetab.length,))
        self.con.commit()

        return self.cur.lastrowid

    def update_filedata(self, filetab):
        self.cur.execute("""
                            UPDATE filedata SET changes = ? WHERE filetab_id = ?
                        """, (pickle.dumps(filetab.changes), filetab.filetab_id,))
        self.cur.execute(f"""       
                            UPDATE preferences SET byteorder = ?, capitalize = ?
                            WHERE filetab_id = ?
                        """, (filetab.byteorder, filetab.cap, filetab.filetab_id,))
        self.cur.execute(f"""
                            UPDATE file_length SET length = ? WHERE filetab_id = ?
                        """, (filetab.length, filetab.filetab_id,))
        self.con.commit()

    def delete_filedata(self, filetab_id):
        self.cur.execute("""
                            DELETE FROM filedata WHERE filetab_id = ?
                        """, (filetab_id,))
        self.cur.execute("""
                            DELETE FROM preferences WHERE filetab_id = ?
                        """, (filetab_id,))
        self.cur.execute("""
                            DELETE FROM file_length WHERE filetab_id = ?
                        """, (filetab_id,))
        self.con.commit()


class MainWindow(QMainWindow):
    def __init__(self, session):
        self.session = session
        self.images = []

        super().__init__()
        MainWindowLoadUI.setupUi(self)

        self.actionNew.triggered.connect(lambda: self.open_file(new=True))
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSaveAll.triggered.connect(lambda: self.save_file(save_all=True))
        self.actionClose.triggered.connect(self.close_file)
        self.actionCloseAll.triggered.connect(lambda: self.close_file(close_all=True))
        self.actionQuit.triggered.connect(self.close)
        self.actionQuickHelp.triggered.connect(self.open_image)
        self.actionShowHelp.triggered.connect(self.open_help)
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
                        new_tab = FileTab(self.session, filetab_id=id[0])
                        self.tabs.addTab(new_tab, new_tab.filename)
                    except FileExistsError:
                        pass
            elif btn == QMessageBox.Cancel.numerator:
                self.close()

    def open_file(self, new=False):
        if not new:
            filepath, ok = QFileDialog.getOpenFileName(self, "Open File", "")
            if not ok:
                return -1
        else:
            filepath = None

        try:
            new_tab = FileTab(self.session, filepath, new)
            self.tabs.addTab(new_tab, new_tab.filename)
            if not new:
                self.tabs.setTabToolTip(self.tabs.count() - 1, filepath)
        except (FileNotFoundError, ValueError):
            return -1
        return 0

    def save_file(self, save_all=False):
        if not save_all:
            tab = self.tabs.currentWidget()
            if tab is not None:
                try:
                    tab.save_tab()
                except ValueError:
                    return -1
        else:
            for tab_index in range(self.tabs.count()):
                try:
                    self.tabs.widget(tab_index).save_tab()
                except ValueError:
                    return -1

        return 0

    def close_file(self, index=None, close_all=False):
        if not close_all:
            if index is None:
                index = self.tabs.currentIndex()

            tab = self.tabs.widget(index)
            try:
                tab.close_tab()
                tab.session.delete_filedata(tab.filetab_id)
                self.tabs.removeTab(index)
            except ValueError:
                return -1
        else:
            for _ in range(self.tabs.count()):
                tab = self.tabs.widget(0)
                try:
                    tab.close_tab()
                    tab.session.delete_filedata(tab.filetab_id)
                    self.tabs.removeTab(0)
                except ValueError:
                    return -1
        return 0

    def open_image(self):
        new_image = ImageWindow()
        new_image.closeEvent = lambda event: self.images.remove(new_image) and event.accept()
        self.images.append(new_image)

    def open_help(self):
        webbrowser.open('https://github.com/weldingtorch/hexedit#readme', new=2)

    def closeEvent(self, event):
        if self.close_file(close_all=True) == 0:
            event.accept()
        else:
            event.ignore()


class FileTab(QWidget):
    def __init__(self, session, filepath=None, is_new=False, filetab_id=None):
        super().__init__()

        self.session = session
        self.filetab_id = filetab_id
        self.data = None
        self.length = None
        self.byteorder = "big"
        self.cap = True

        if self.filetab_id is not None:
            self.load_filedata()
            self.LoadUI()
        else:
            self.filepath = filepath
            self.is_new = is_new
            if self.is_new:
                self.filename = "unnamed"
            else:
                self.filename = self.filepath.split("/")[-1]
            self.changes = dict()
            self.LoadUI()
            self.filetab_id = self.session.set_filedata(self)

    def load_filedata(self):
        filedata = self.session.get_filedata(self.filetab_id)
        if filedata:
            self.filepath, self.is_new, changes, self.byteorder, cap = filedata
            self.changes = pickle.loads(changes)
            self.cap = bool(cap)
            if self.is_new:
                self.filename = "unnamed"
                self.length = self.session.get_filelength(self.filetab_id)
            else:
                self.filename = self.filepath.split("/")[-1]

    def LoadUI(self):
        if not self.is_new:
            retry_flag = True
            while retry_flag:
                try:
                    with open(self.filepath, "rb") as file:
                        self.data = file.read()
                    self.length = len(self.data)
                    retry_flag = False

                except FileNotFoundError:
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle(self.filename)
                    msg_box.setText("Error while opening file.")
                    msg_box.setInformativeText("File was moved or deleted. \n"
                                               "Do you want to remove this file from session?")
                    msg_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Yes | QMessageBox.Cancel)
                    msg_box.setDefaultButton(QMessageBox.Retry)
                    btn = msg_box.exec()

                    if btn == QMessageBox.Retry.numerator:
                        continue

                    elif btn == QMessageBox.Yes.numerator:
                        self.session.delete_filedata(self.filetab_id)

                    raise FileNotFoundError
        else:
            if self.length is None:
                self.length, ok = QInputDialog.getInt(self, "Set file size", "Enter file size in bytes",
                                                      256, 1, 16 ** 4, 16)
                if not ok:
                    self.close()
                    raise ValueError
            self.data = bytearray(self.length)

        FileTabLoadUI.LoadUI(self)
        self.fill_table()
        self.update_repr(full_fill=True)

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

    def change_prefs(self, arg):
        obj_name = self.sender().objectName()
        if obj_name == "capitalize":
            self.cap = arg
        elif obj_name == "byteorder_combo":
            self.byteorder = arg

        self.session.update_filedata(self)
        self.fill_table()

    def add_change(self, row, column):
        self.table.cellChanged.disconnect()
        item = self.sender().item(row, column)
        if column != 16:
            pos = row * 16 + column
            text = item.text().strip(" ")
            if pos < self.length:
                if len(text) <= 2:
                    try:
                        self.changes[pos] = int(text, 16)
                        self.session.update_filedata(self)
                    except ValueError:
                        item.setText("00")
                else:
                    item.setText("00")
                self.fill_table()
                self.update_repr()
            else:
                item.setText("")
        else:
            self.session.update_filedata(self)
        self.table.cellChanged.connect(self.add_change)

    def save_tab(self):
        change_pos_list = self.changes.keys()
        new_data = bytearray([self.changes[pos] if pos in change_pos_list
                              else self.data[pos] for pos in range(len(self.data))])
        if not self.is_new:
            with open(self.filepath, "wb") as file:
                file.write(new_data)
        else:
            filename, ok = QFileDialog.getSaveFileName(self, "Save File", "")
            if ok:
                with open(filename, "wb") as file:
                    file.write(new_data)
            else:
                raise ValueError

        self.changes.clear()

    def close_tab(self):
        if self.changes or self.is_new:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(self.filename)
            msg_box.setText("You have unsaved changes!")
            msg_box.setInformativeText("Do you want to save before closing file?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Yes)
            btn = msg_box.exec()

            if btn == QMessageBox.Yes.numerator:
                self.save_tab()

            elif btn == QMessageBox.Cancel.numerator:
                raise ValueError


class ImageWindow(QWidget):
    def __init__(self):
        super().__init__()
        try:
            images = os.listdir("./Images")
            if images:
                self.LoadUI(images)
                self.show()
        except WindowsError:
            os.mkdir("./Images")

    def LoadUI(self, images):
        imagename = random.choice(images)
        image_holder = QLabel()
        image = QPixmap("./Images/" + imagename)
        image_holder.setPixmap(image)
        grid = QGridLayout()
        grid.addWidget(image_holder)
        self.setLayout(grid)
        self.setWindowTitle("Quick Help")
        self.setFixedSize(self.sizeHint())


if __name__ == '__main__':
    app = QApplication(sys.argv)

    session = SessionHandler()
    app.aboutToQuit.connect(session.close_session)

    MainWindow(session)
    sys.exit(app.exec_())
