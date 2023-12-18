import os
import json
from PySide2 import QtCore, QtGui, QtWidgets
import pymel.core as pm
import pymel.api as pma
from shiboken2 import wrapInstance
from ColorOut import __author__, __version__, syntax
from ColorOut.loggingFn import Logger


def mayaMainWindow():
    mainWindowPtr = pma.MQtUtil.mainWindow()
    if mainWindowPtr:
        return wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    # else:
    #     mayaMainWindow()


class Dialog(QtWidgets.QDialog):

    USER_RULES = os.path.join(pm.moduleInfo(mn="ColorOut", p=1), "ColorOut", "rules", "user.json")  # type:str
    WINDOW_TITLE = "ColorOut settings"
    UI_NAME = "ColorOutSettings"
    UI_INSTANCE = None

    @classmethod
    def display(cls, *args):
        if not cls.UI_INSTANCE:
            cls.UI_INSTANCE = Dialog()

        if cls.UI_INSTANCE.isHidden():
            cls.UI_INSTANCE.show()
        else:
            cls.UI_INSTANCE.raise_()
            cls.UI_INSTANCE.activateWindow()

    def __init__(self, parent=mayaMainWindow()):
        super(Dialog, self).__init__(parent)
        if pm.about(macOS=1):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowIcon(QtGui.QIcon(":colorProfile.svg"))
        self.setMinimumSize(400, 300)

        # UI setup
        self.rules_dict = {}
        self.load_rules()
        self.geometry = None
        self.create_actions()
        self.create_menu_bar()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        self.reset_defaults_action = QtWidgets.QAction("Reset default rules", self)
        self.about_action = QtWidgets.QAction("About", self)

    def create_menu_bar(self):
        self.edit_menu = QtWidgets.QMenu("&Edit")
        self.edit_menu.addAction(self.reset_defaults_action)
        self.help_menu = QtWidgets.QMenu("Help")
        self.help_menu.addAction(self.about_action)

        self.menubar = QtWidgets.QMenuBar()
        self.menubar.addMenu(self.edit_menu)
        self.menubar.addMenu(self.help_menu)

    def create_widgets(self):
        self.all_rules = AllRulesWidget()
        self.rule_grp = QtWidgets.QGroupBox("Rule")
        self.rule_name = QtWidgets.QLineEdit()
        self.rule_pattern = QtWidgets.QLineEdit()
        self.rule_fg_color = ColorButton()
        self.rule_bg_color = ColorButton()
        self.rule_bg_color_checkbox = QtWidgets.QCheckBox("Background color")
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.hide()
        self.confirm_button = QtWidgets.QPushButton("Confirm")
        self.close_button = QtWidgets.QPushButton("Close")

        self.sections_splitter = QtWidgets.QSplitter()
        self.sections_splitter.addWidget(self.all_rules)
        self.sections_splitter.addWidget(self.rule_grp)

    def create_layouts(self):
        self.rule_color_layout = QtWidgets.QHBoxLayout()
        self.rule_color_layout.addWidget(QtWidgets.QLabel("Foregound color:"))
        self.rule_color_layout.addWidget(self.rule_fg_color)
        self.rule_color_layout.addStretch()
        self.rule_color_layout.addWidget(self.rule_bg_color_checkbox)
        self.rule_color_layout.addWidget(self.rule_bg_color)
        self.rule_color_layout.addStretch()

        self.main_rule_layout = QtWidgets.QFormLayout()
        self.main_rule_layout.addRow("Name:", self.rule_name)
        self.main_rule_layout.addRow("Pattern: ", self.rule_pattern)
        self.main_rule_layout.addRow(self.rule_color_layout)
        self.main_rule_layout.addRow(self.save_button)
        self.rule_grp.setLayout(self.main_rule_layout)

        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.confirm_button)
        self.buttons_layout.addWidget(self.close_button)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.sections_splitter)
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.setMenuBar(self.menubar)
        self.setLayout(self.main_layout)

    def create_connections(self):
        # Menubar
        self.reset_defaults_action.triggered.connect(self.reset_to_defaults)
        self.about_action.triggered.connect(self.about_window)
        # Buttons
        self.all_rules.list.currentItemChanged.connect(self.update_rule_info)
        self.all_rules.add_button.clicked.connect(self.add_rule)
        self.all_rules.delete_button.clicked.connect(self.delete_rule)
        self.rule_bg_color_checkbox.toggled.connect(self.rule_bg_color.setEnabled)
        self.save_button.clicked.connect(self.save_changes)
        self.confirm_button.clicked.connect(self.apply_rules)
        self.close_button.clicked.connect(self.hide)
        # Save button updates
        self.rule_name.textEdited.connect(self.toggle_save_button)
        self.rule_pattern.textEdited.connect(self.toggle_save_button)
        self.rule_bg_color_checkbox.stateChanged.connect(self.toggle_save_button)
        self.rule_fg_color.color_changed.connect(self.toggle_save_button)
        self.rule_bg_color.color_changed.connect(self.toggle_save_button)

    def showEvent(self, event):
        super(Dialog, self).showEvent(event)
        self.update_rule_list()
        if self.geometry:
            self.restoreGeometry(self.geometry)

    def hideEvent(self, event):
        if isinstance(self, Dialog):
            super(Dialog, self).hideEvent(event)
            self.geometry = self.saveGeometry()

    def load_rules(self):
        with open(self.USER_RULES, "r") as json_file:
            self.rules_dict = json.load(json_file)

    def serialize_info(self):
        fg_color = self.rule_fg_color.get_color()
        fg_color = [fg_color.red(), fg_color.green(), fg_color.blue()]
        if self.rule_bg_color_checkbox.isChecked():
            bg_color = self.rule_bg_color.get_color()
            bg_color = [bg_color.red(), bg_color.green(), bg_color.blue()]
        else:
            bg_color = []

        rule_dict = {
            "pattern": self.rule_pattern.text(),
            "fg_color": fg_color,
            "bg_color": bg_color}
        return rule_dict

    @QtCore.Slot()
    def reset_to_defaults(self):
        syntax.HighlightManager.reset_default_rules()
        self.load_rules()
        self.update_rule_list()
        self.all_rules.list.setCurrentRow(0)

    @QtCore.Slot()
    def about_window(self):
        QtWidgets.QMessageBox.about(self, "ColorOut", "Author: {0}\nVersion: {1}".format(__author__, __version__))

    @QtCore.Slot()
    def toggle_save_button(self, state):
        if isinstance(state, str):  # basestring in python2
            state = bool(state)
        else:
            state = True

        self.save_button.setVisible(state)

    @QtCore.Slot(QtWidgets.QWidgetItem)
    def update_rule_info(self, item):
        if not item:
            return
        rule_name = item.data(0)
        rule_data = item.data(QtCore.Qt.UserRole)
        self.rule_name.setText(rule_name)
        self.rule_pattern.setText(rule_data.get("pattern"))
        self.rule_fg_color.set_color(rule_data.get("fg_color"))
        self.rule_bg_color.set_color(rule_data.get("bg_color"))
        self.rule_bg_color_checkbox.setChecked(bool(rule_data.get("bg_color", False)))
        self.rule_bg_color.setEnabled(self.rule_bg_color_checkbox.isChecked())
        self.save_button.setVisible(0)

    @QtCore.Slot()
    def update_rule_list(self):
        self.all_rules.list.clear()
        for rule in self.rules_dict.keys():
            item = QtWidgets.QListWidgetItem(rule)
            item.setData(QtCore.Qt.UserRole, self.rules_dict[rule])
            self.all_rules.list.addItem(item)
        self.save_button.setVisible(0)

    @QtCore.Slot()
    def save_changes(self):
        check_expression = QtCore.QRegExp(self.rule_pattern.text())
        if not check_expression.isValid():
            error_message = QtWidgets.QErrorMessage(self)
            error_message.showMessage("Invalid regular expression: {0}".format(self.rule_pattern.text()))
            Logger.error("Invalid regular expression: {0}".format(self.rule_pattern.text()))
            return

        new_info_dict = {self.rule_name.text(): self.serialize_info()}
        self.rules_dict.update(new_info_dict)
        self.update_rule_list()

    @ QtCore.Slot()
    def add_rule(self):
        self.rule_name.setText("")
        self.rule_pattern.setText("")
        self.rule_fg_color.set_color(QtCore.Qt.white)
        self.rule_bg_color.set_color(QtCore.Qt.black)
        self.rule_bg_color_checkbox.setChecked(0)

    @ QtCore.Slot()
    def delete_rule(self):
        if self.all_rules.list.count() > 1:
            self.rules_dict.pop(self.all_rules.list.currentItem().data(0))
            self.update_rule_list()
            self.all_rules.list.setCurrentRow(0)
        else:
            QtWidgets.QMessageBox.warning(self, "Rule deletion", "At least 1 rule is required")

    @ QtCore.Slot()
    def apply_rules(self):
        Logger.debug("Writing rules dict: {0}".format(self.rules_dict))
        with open(self.USER_RULES, "w") as json_file:
            json.dump(self.rules_dict, json_file, indent=4)

        try:
            syntax.HighlightManager.remove_connection()
            syntax.HighlightManager.create_connection()
        except BaseException:
            Logger.exception("Failed to apply new rules")


class AllRulesWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AllRulesWidget, self).__init__(parent)

        # Widgets
        self.list = QtWidgets.QListWidget()
        self.add_button = QtWidgets.QPushButton("+")
        self.delete_button = QtWidgets.QPushButton("-")
        for btn in [self.add_button, self.delete_button]:
            btn.setMaximumWidth(30)

        # Layouts
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.delete_button)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.list)
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)


class ColorButton(QtWidgets.QLabel):

    color_changed = QtCore.Signal(QtGui.QColor)

    def __init__(self, parent=None, color=[1, 1, 1]):
        super(ColorButton, self).__init__(parent)

        self._color = QtGui.QColor()  # Invalid color

        self.set_size(25, 25)
        self.set_color(color)

    def set_size(self, width, height):
        self.setFixedSize(width, height)

    def set_color(self, color):
        Logger.debug("Set color: {0}".format(color))
        if isinstance(color, list):
            if not color:
                color = [1, 1, 1]
            color = QtGui.QColor.fromRgb(*color)

        color = QtGui.QColor(color)
        if self._color == color:
            return

        self._color = color
        pixmap = QtGui.QPixmap(self.size())
        pixmap.fill(self._color)
        self.setPixmap(pixmap)
        self.color_changed.emit(self._color)

    def get_color(self):
        return self._color

    def select_color(self):
        color = QtWidgets.QColorDialog.getColor(self.get_color(), self, options=QtWidgets.QColorDialog.DontUseNativeDialog)
        if color.isValid():
            self.set_color(color)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.select_color()


# if __name__ == "__main__":
#     try:
#         testTool.close()
#         testTool.deleteLater()
#     except BaseException:
#         pass
#
#     testTool = Dialog()
#     testTool.show()
