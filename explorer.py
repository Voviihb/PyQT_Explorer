from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, shutil, sys, csv, zipfile
from datetime import datetime
from ui import Ui_MainWindow


# классы исключений, которые будут вызываться при ошибках
class NameNotGiven(Exception):
    pass


class UnexpectedError(Exception):
    pass


class IsNotDir(Exception):
    pass


# переназначение shutil.copytree для правильного копирования папок в папку.
# оригинальный os.copytree по прежнему доступен и используется для копирования файла в папку
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


# доработанный архиватор. zipfile.ZipFile изначально не умел упаковывать внутренности папки в архив
def zipFilesInDir(dirName, zipFileName):
    # create a ZipFile object
    with zipfile.ZipFile(zipFileName, 'w', zipfile.ZIP_BZIP2) as zipObj:
        # Iterate over all the files in directory
        if os.path.isfile(dirName):
            zipObj.write(dirName)
        else:
            for root, dirs, files in os.walk(dirName):
                for file in files:
                    zipObj.write(os.path.join(root, file))


class FileBrowser(QMainWindow, Ui_MainWindow):
    EXIT_CODE_REBOOT = -123

    def __init__(self):
        super(FileBrowser, self).__init__()
        self.setupUi(self)
        self.create_first_window()
        self.create_second_window()
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.context_menu)
        self.treeView_2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView_2.customContextMenuRequested.connect(self.context_menu)
        self.treeView.doubleClicked.connect(self.open_file_clicked)
        self.treeView_2.doubleClicked.connect(self.open_file_clicked)
        self.treeView.clicked.connect(self.click)
        self.treeView_2.clicked.connect(self.click)
        [i.clicked.connect(self.run) for i in self.buttonGroup.buttons()]

    # создаем окна с файловым менеджером
    # я использую QFileSystemModel для этого
    def create_first_window(self):
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        # прописываю начальное положение, чтобы можно было видеть все диски
        self.treeView.setModel(self.model)
        # ставлю модельку на свое окно
        # path = "C:\\"
        # self.treeView.setRootIndex(model.index(path))
        # при желании можно дать доступ только к определенной папке, указав ее в path
        self.treeView.setSortingEnabled(True)

    def create_second_window(self):
        # прописываю начальное положение, чтобы можно было видеть все диски
        self.treeView_2.setModel(self.model)
        # ставлю модельку на свое окно
        # path = "D:\\"
        # self.treeView_2.setRootIndex(model.index(path))
        # при желании можно дать доступ только к определенной папке, указав ее в path
        self.treeView_2.setSortingEnabled(True)

    # по двойному клику можно открывать папки. Если нажатый объект не папка-попытаюсь открыть файл
    # средством по умолчанию. Например .mp3 откроется через плеер
    def open_file_clicked(self, signal):
        try:
            file_path = self.model.filePath(signal)
            if self.sender().objectName() == "treeView":
                if not self.model.isDir(self.treeView.currentIndex()):
                    os.startfile(file_path)

            elif self.sender().objectName() == "treeView_2":
                if not self.model.isDir(self.treeView_2.currentIndex()):
                    os.startfile(file_path)

            else:
                raise UnexpectedError("Unexpected Error")

        except UnexpectedError as e:
            self.exception_info = e
            self.exception_text = "You`re doing something incorrectly. Read FAQ and try again"
            self.showdialog()

    # создание горячих клавиш (shortcuts)
    def keyPressEvent(self, event):
        try:
            if int(event.modifiers()) == Qt.ControlModifier:
                if event.key() == Qt.Key_C:
                    self.copy()

                elif event.key() == Qt.Key_D:
                    self.confidence_text = "It will delete all the data. Data can`t be restored"
                    if self.is_confident() == QMessageBox.Ok:
                        self.delete()

                elif event.key() == Qt.Key_N:
                    self.new_folder()

                elif event.key() == Qt.Key_M:
                    self.move_button_action()

                elif event.key() == Qt.Key_R:
                    qApp.exit(FileBrowser.EXIT_CODE_REBOOT)

                elif event.key() == Qt.Key_Q:
                    self.confidence_text = "It will close the program. Do you want to close it?"
                    if self.is_confident() == QMessageBox.Ok:
                        sys.exit()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()

    # обработчик нажатий. Сохраняет последний выделенный элемент
    def click(self, signal):
        try:
            file_path = self.model.filePath(signal)
            if self.sender().objectName() == "treeView":
                self.current_selected = file_path

            elif self.sender().objectName() == "treeView_2":
                self.current_selected = file_path

            else:
                raise UnexpectedError("Unexpected Error")

        except UnexpectedError as e:
            self.exception_info = e
            self.exception_text = "You`re doing something incorrectly. Read FAQ and try again"
            self.showdialog()

    # создаем контекстное меню для каждого окна
    def context_menu(self):
        menu = QMenu()
        open = menu.addAction("Open")
        rename = menu.addAction("Rename")
        info = menu.addAction("Get Information")
        unpack_zip = menu.addAction("Unpack ZIP")
        pack_zip = menu.addAction("Pack to ZIP")
        self.sender_name = self.sender().objectName()
        open.triggered.connect(self.menu_actions)
        rename.triggered.connect(self.menu_actions)
        info.triggered.connect(self.menu_actions)
        unpack_zip.triggered.connect(self.menu_actions)
        pack_zip.triggered.connect(self.menu_actions)
        cursor = QCursor()
        menu.exec_(cursor.pos())

    # одна функция на все меню, которое вызывается правой кнопкой мыши
    def menu_actions(self):
        try:
            if self.sender().text() == "Open":
                if self.sender_name == "treeView":
                    index = self.treeView.currentIndex()
                    file_path = self.model.filePath(index)
                    os.startfile(file_path)

                elif self.sender_name == "treeView_2":
                    index = self.treeView_2.currentIndex()
                    file_path = self.model.filePath(index)
                    os.startfile(file_path)

            elif self.sender().text() == "Rename":
                try:
                    # Запрашиваю у пользователя новое имя. Если ОК не нажато, то действие отменяется
                    if self.sender_name == "treeView":
                        text, ok = QInputDialog.getText(self, 'Rename',
                                                        'Enter new file name with .file type:',
                                                        text="." + self.model.fileInfo(
                                                            self.treeView.currentIndex()).completeSuffix())
                        if ok:
                            index = self.treeView.currentIndex()
                            file_path = self.model.filePath(index)
                            file_dir = file_path.split("/")[:-1]
                            file_dir.append(text)
                            os.rename(file_path, "/".join(file_dir))

                    elif self.sender_name == "treeView_2":
                        text, ok = QInputDialog.getText(self, 'Rename',
                                                        'Enter new file name with .file type:',
                                                        text="." + self.model.fileInfo(
                                                            self.treeView_2.currentIndex()).completeSuffix())
                        index = self.treeView_2.currentIndex()
                        file_path = self.model.filePath(index)
                        file_dir = file_path.split("/")[:-1]
                        file_dir.append(text)
                        os.rename(file_path, "/".join(file_dir))

                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "Unexpected error"
                    self.showdialog()

            elif self.sender().text() == "Get Information":
                try:
                    if self.sender_name == "treeView":
                        file_info = self.model.fileInfo(self.treeView.currentIndex())

                    elif self.sender_name == "treeView_2":
                        file_info = self.model.fileInfo(self.treeView_2.currentIndex())

                    file_info_array = {"absoluteFilePath": (file_info.absoluteFilePath()),
                                       "absolutePath": (file_info.absolutePath()),
                                       "baseName": (file_info.baseName()),
                                       "completeSuffix": (file_info.completeSuffix()),
                                       "size": (file_info.size()),
                                       "isExecutable": (file_info.isExecutable()),
                                       "birthTime": (str(file_info.birthTime().date().toPyDate()) + " " +
                                                     str(file_info.birthTime().time().toString())),
                                       "lastModified": (str(file_info.lastModified().date().toPyDate()) + " " +
                                                        str(file_info.lastModified().time().toString())),
                                       "lastRead": (str(file_info.lastRead().date().toPyDate()) + " " +
                                                    str(file_info.lastRead().time().toString()))}

                    # "absoluteFilePath" - абсолютный путь до самого файла
                    # "absolutePath" - абсолютная директория файла
                    # "baseName" - название файла без расширения
                    # "completeSuffix" - расширение файла (exe, mp3, doc и т.д.)
                    # "size" - размер файла в байтах
                    # "isExecutable" - является ли файл исполняемым (exe)
                    # "birthTime" - Дата создания фалйа в формате year-month-day и время hour:minute:sec
                    # "lastModified" - Дата последнего изменения фалйа в формате year-month-day и время hour:minute:sec
                    # "lastRead" - Дата последнего чтения фалйа в формате year-month-day и время hour:minute:sec

                    directory = os.getcwd()

                    if os.path.isfile(f"{directory}\\files_info.csv"):
                        with open('files_info.csv', 'a', newline='', encoding="utf-8") as f:
                            writer = csv.DictWriter(
                                f, fieldnames=["absoluteFilePath", "absolutePath", "baseName", "completeSuffix", "size",
                                               "isExecutable", "birthTime", "lastModified", "lastRead"],
                                delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
                            writer.writerow(file_info_array)

                    else:
                        with open('files_info.csv', 'w', newline='', encoding="utf-8") as f:
                            writer = csv.DictWriter(
                                f, fieldnames=["absoluteFilePath", "absolutePath", "baseName", "completeSuffix", "size",
                                               "isExecutable", "birthTime", "lastModified", "lastRead"],
                                delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
                            writer.writeheader()
                            writer.writerow(file_info_array)

                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "Unexpected error"
                    self.showdialog()

            elif self.sender().text() == "Unpack ZIP":
                try:
                    if self.sender_name == "treeView":
                        index = self.treeView.currentIndex()
                        self.file_path = self.model.filePath(index)
                        file_info = self.model.fileInfo(self.treeView.currentIndex())
                        self.new_files_dir = file_info.absolutePath() + "//" + file_info.completeBaseName()

                    elif self.sender_name == "treeView_2":
                        index = self.treeView_2.currentIndex()
                        self.file_path = self.model.filePath(index)
                        file_info = self.model.fileInfo(self.treeView_2.currentIndex())
                        self.new_files_dir = file_info.absolutePath() + "//" + file_info.completeBaseName()

                    else:
                        raise UnexpectedError("Unexpected Error")

                    with zipfile.ZipFile(self.file_path, 'r') as zfile:
                        zfile.extractall(self.new_files_dir)

                except zipfile.BadZipFile as e:
                    self.exception_info = e
                    self.exception_text = "You`re trying to unpack file that is not an .zip file"
                    self.showdialog()

                # можно использовать allowZip64=True, но тогда на слабых машинах будет происходить зависание
                # системы, т.к. будет возможность открывать архивы больше 4ГБ
                except zipfile.LargeZipFile as e:
                    self.exception_info = e
                    self.exception_text = "The .zip file is too large"
                    self.showdialog()

                except UnexpectedError as e:
                    self.exception_info = e
                    self.exception_text = "Something went wrong with unpacking"
                    self.showdialog()

                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "Something went wrong. Read FAQ and try again"
                    self.showdialog()

            elif self.sender().text() == "Pack to ZIP":
                try:
                    if self.sender_name == "treeView":
                        index = self.treeView.currentIndex()
                        self.file_path = self.model.filePath(index)
                        file_info = self.model.fileInfo(self.treeView.currentIndex())
                        self.new_files_dir = file_info.absolutePath() + "//" + file_info.completeBaseName() + ".zip"

                    elif self.sender_name == "treeView_2":
                        index = self.treeView_2.currentIndex()
                        self.file_path = self.model.filePath(index)
                        file_info = self.model.fileInfo(self.treeView_2.currentIndex())
                        self.new_files_dir = file_info.absolutePath() + "//" + file_info.completeBaseName() + ".zip"

                    else:
                        raise UnexpectedError("Unexpected Error")

                    zipFilesInDir(self.file_path, self.new_files_dir)
                    # print(self.new_files_dir)
                    # print(self.file_path)

                except zipfile.BadZipFile as e:
                    self.exception_info = e
                    self.exception_text = "You`re trying to unpack file that is not an .zip file"
                    self.showdialog()

                # можно использовать allowZip64=True, но тогда на слабых машинах будет происходить зависание
                # системы, т.к. будет возможность открывать архивы больше 4ГБ
                except zipfile.LargeZipFile as e:
                    self.exception_info = e
                    self.exception_text = "The .zip file is too large"
                    self.showdialog()

                except UnexpectedError as e:
                    self.exception_info = e
                    self.exception_text = "Something went wrong with unpacking"
                    self.showdialog()

            else:
                raise UnexpectedError("Unexpected Error")

        except UnexpectedError as e:
            self.exception_info = e
            self.exception_text = "You`re doing something incorrectly. Read FAQ and try again"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Something went wrong. Read FAQ and try again"
            self.showdialog()

    # функция для всех кнопок
    def run(self):
        try:
            button_text = self.sender().text()
            if button_text == "Copy":
                self.copy()

            elif button_text == "Delete":
                self.confidence_text = "It will delete all the data. Data can`t be restored"
                if self.is_confident() == QMessageBox.Ok:
                    self.delete()

            elif button_text == "New folder":
                self.new_folder()

            elif button_text == "Take screenshot":
                try:
                    filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.jpg')
                    QScreen.grabWindow(app.primaryScreen(),
                                       QApplication.desktop().winId()).save(filename, 'png')
                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "The FAQ has been deleted. Download it again."
                    self.showdialog()

            elif button_text == "Show F.A.Q.":
                try:
                    os.startfile("F.A.Q..docx")
                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "The FAQ has been deleted. Download it again."
                    self.showdialog()

            elif button_text == "Move":
                self.move_button_action()

            elif button_text == "Exit from program":
                self.confidence_text = "It will close the program. Do you want to close it?"
                if self.is_confident() == QMessageBox.Ok:
                    sys.exit()

            elif button_text == "Reset":
                qApp.exit(FileBrowser.EXIT_CODE_REBOOT)

            else:
                raise UnexpectedError("Unexpected Error")

        except UnexpectedError as e:
            self.exception_info = e
            self.exception_text = "You`re doing something incorrectly. Read FAQ and try again"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()

    def open_file(self):
        try:
            if self.sender_name == "treeView":
                index = self.treeView.currentIndex()
                file_path = self.model.filePath(index)
                os.startfile(file_path)

            elif self.sender_name == "treeView_2":
                index = self.treeView_2.currentIndex()
                file_path = self.model.filePath(index)
                os.startfile(file_path)

            else:
                raise UnexpectedError("Unexpected Error")

        except UnexpectedError as e:
            self.exception_info = e
            self.exception_text = "You`re doing something incorrectly. Read FAQ and try again"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()

    def copy(self):
        try:
            file_path1 = self.model.filePath(self.treeView.currentIndex())
            file_path2 = self.model.filePath(self.treeView_2.currentIndex())

            # сравнение выбранных элементов в правом и левом окне с последним выбранным элементом
            # в каком окне будет совпадение - то выбранный элемент и является копируемым
            if file_path1 == self.current_selected:
                file_location = file_path1
                file_destination = file_path2

            elif file_path2 == self.current_selected:
                file_location = file_path2
                file_destination = file_path1

            if os.path.isdir(file_destination):
                # если не папка, то использую метод copy
                if not os.path.isdir(file_location):
                    try:
                        shutil.copy(file_location, file_destination)

                    except IOError as e:
                        self.exception_info = e
                        self.exception_text = "Change the file or directory and try again"
                        self.showdialog()

                    except Exception as e:
                        self.exception_info = e
                        self.exception_text = "Unexpected error"
                        self.showdialog()

                # если папка, то использую переназначенный метод shutil.copytree
                elif os.path.isdir(file_location):
                    try:
                        dfold = file_location.split("/")
                        newdirpath = f"{file_destination}//{dfold[-1]}"
                        os.mkdir(newdirpath)
                        copytree(file_location, newdirpath)

                    except IOError as e:
                        self.exception_info = e
                        self.exception_text = "Change the file or directory and try again"
                        self.showdialog()

                    except Exception as e:
                        self.exception_info = e
                        self.exception_text = "Unexpected error"
                        self.showdialog()
            else:
                raise IsNotDir("Unable to copy files/folder because current selected is not a directory")

        except IsNotDir as e:
            self.exception_info = e
            self.exception_text = "Copying error"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()

    def delete(self):
        try:
            if not os.path.isdir(self.current_selected):
                try:
                    os.remove(self.current_selected)

                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "File not found"
                    self.showdialog()

            elif os.path.isdir(self.current_selected):
                try:
                    shutil.rmtree(self.current_selected)

                except Exception as e:
                    self.exception_info = e
                    self.exception_text = "File or directory not found"
                    self.showdialog()

            else:
                raise UnexpectedError("Unexpected Error")

        except UnexpectedError as e:
            self.exception_info = e
            self.exception_text = "You`re doing something incorrectly. Read FAQ and try again"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Something went wrong while deleting. Read FAQ and try again"
            self.showdialog()

    def new_folder(self):
        text, ok = QInputDialog.getText(self, 'Rename',
                                        'Enter new folder name:',
                                        text="New Folder")

        try:
            if os.path.isdir(self.current_selected):
                if ok:
                    if text:
                        os.mkdir(os.path.join(self.current_selected, text))

                    else:
                        raise NameNotGiven("Name is not given")
            else:
                raise IsNotDir("Unable to make new folder because current selected is not a directory")

        except IsNotDir as e:
            self.exception_info = e
            self.exception_text = "Making new folder error"
            self.showdialog()

        except NameNotGiven as e:
            self.exception_info = e
            self.exception_text = "Give folder a name and try again"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Something went wrong while making new folder. Read FAQ and try again"
            self.showdialog()

    def move_button_action(self):
        try:
            file_path1 = self.model.filePath(self.treeView.currentIndex())
            file_path2 = self.model.filePath(self.treeView_2.currentIndex())

            # сравнение выбранных элементов в правом и левом окне с последним выбранным элементом
            # в каком окне будет совпадение - то выбранный элемент и является копируемым/перемещаемым
            if file_path1 == self.current_selected:
                file_location = file_path1
                file_destination = file_path2

            elif file_path2 == self.current_selected:
                file_location = file_path2
                file_destination = file_path1

            if os.path.isdir(file_destination):
                if not os.path.isdir(file_location):
                    try:
                        shutil.copy(file_location, file_destination)
                        # т.к. встроенных методов перемещения(а не копирования) в os и shutil нет, сначала копирую,
                        # а потом удаляю файл в начальной директории
                        self.delete()

                    except IOError as e:
                        self.exception_info = e
                        self.exception_text = "Change the file or directory and try again"
                        self.showdialog()

                    except Exception as e:
                        self.exception_info = e
                        self.exception_text = "Unexpected error"
                        self.showdialog()

                elif os.path.isdir(file_location):
                    try:
                        dfold = file_location.split("/")
                        newdirpath = f"{file_destination}//{dfold[-1]}"
                        os.mkdir(newdirpath)
                        copytree(file_location, newdirpath)
                        # т.к. встроенных методов перемещения(а не копирования) в os и shutil нет, сначала копирую,
                        # а потом удаляю файл в начальной директории
                        self.delete()

                    except IOError as e:
                        self.exception_info = e
                        self.exception_text = "Change the file or directory and try again"
                        self.showdialog()

                    except Exception as e:
                        self.exception_info = e
                        self.exception_text = "Unexpected error"
                        self.showdialog()
            else:
                raise IsNotDir("Unable to move files/folder because current selected is not a directory")

        except IsNotDir as e:
            self.exception_info = e
            self.exception_text = "Moving error"
            self.showdialog()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()

    def showdialog(self):
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("An error accured")
            msg.setInformativeText(self.exception_text)
            msg.setWindowTitle("Error")
            msg.setDetailedText(f"{self.exception_info}")
            msg.exec()

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()

    def is_confident(self):
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.setText("Do you want to continue?")
            msg.setInformativeText(self.confidence_text)
            msg.setWindowTitle("Are you sure?")
            return_value = msg.exec()
            return return_value

        except Exception as e:
            self.exception_info = e
            self.exception_text = "Unexpected error"
            self.showdialog()


if __name__ == '__main__':
    try:
        currentExitCode = FileBrowser.EXIT_CODE_REBOOT
        while currentExitCode == FileBrowser.EXIT_CODE_REBOOT:
            app = QApplication(sys.argv)
            w = FileBrowser()
            w.show()
            currentExitCode = app.exec_()
            app = None

    except Exception:
        print("Everything broke down. Write a message to a developer with your problem")
        qApp.exit()
