from tkinter import Toplevel, Label
from customtkinter import CTkButton
from os import path

from components.set_window_icon import SetWindowIcon
from installer_core.component_tools.thread_manager import ThreadManager
from installer_core.data_tools.load_json_data import LoadJsonData
from installer_core.window_tools.center_window import CenterWindow


class InfoModals(Toplevel):
    MODAL_TYPES = {
        "exit": "exit_modal",
        "attention": "attention_modal",
        "check_files_installed": "check_files_installed_modal",
        "check_files_not_installed": "check_files_not_installed_modal",
        "language_change": "language_change_modal",
    }

    def __init__(self, parent, base_dir, modal_type, app_language):
        super().__init__(parent)
        INFO_MODALS_DATA_PATH = path.join(
            base_dir,
            "language",
            "modals",
            "info_modals",
            f"{app_language}.json",
        )
        load_json_data = LoadJsonData()
        self.info_modals_data = load_json_data.load_json_data(
            INFO_MODALS_DATA_PATH
        ).get("modals", {})
        self.button_data = load_json_data.load_json_data(INFO_MODALS_DATA_PATH).get(
            "buttons", {}
        )
        self.base_dir = base_dir
        self.modal_key = self.get_modal_key(modal_type)
        self.configure_window(parent)
        CenterWindow(self).center_window()

        # Initialize ThreadManager
        self.thread_manager = ThreadManager()

        # Load UI data from JSON file
        self.modal_data = self.info_modals_data.get(self.modal_key, {})

        self.create_modal()

    def get_modal_key(self, modal_type):
        """Map modal type to modal key."""
        return self.MODAL_TYPES.get(modal_type.lower(), None)

    def configure_window(self, parent):
        """Configure the modal window properties."""
        self.transient(parent)
        self.configure(bg="#2B2631")
        self.resizable(False, False)
        self.wait_visibility()
        self.grab_set()
        SetWindowIcon(self.base_dir).set_window_icon(self)

    def create_modal(self):
        """Create the modal based on the type specified."""
        if not self.modal_key:
            raise ValueError(f"Invalid or unsupported modal type: {self.modal_key}")

        self.title(self.modal_data.get("modal_title", "Unknown"))
        self.create_label(self.modal_data.get("modal_label", "No message provided"))

        if self.modal_key == "exit_modal":
            self.create_exit_buttons()
        elif self.modal_key in ["attention_modal", "language_change_modal"]:
            self.create_attention_exit_button()
        else:
            self.create_button(self.button_data["ok_button"], "#10dc60", self.cancel_action).pack(
                pady=20
            )

    def create_label(self, text):
        """Create a label for the modal."""
        Label(
            self,
            text=text,
            fg="white",
            background="#2B2631",
            font=("Segoe UI", 15),
        ).pack(padx=10, pady=10)

    def create_buttons(self, buttons):
        """Create buttons based on a list of button configurations."""
        for text, color, command, side in buttons:
            self.create_button(text, color, command).pack(side=side, padx=10, pady=20)

    def create_exit_buttons(self):
        """Create Yes and No buttons for exit modal."""
        buttons = [
            (self.button_data["yes_button"], "#f04141", self.ok_action, "left"),
            (self.button_data["no_button"], "#10dc60", self.cancel_action, "right"),
        ]
        self.create_buttons(buttons)

    def create_attention_exit_button(self):
        """Create Ok button for attention modal."""
        self.protocol("WM_DELETE_WINDOW", self.ok_action)
        self.create_button(self.button_data["ok_button"], "#10dc60", self.ok_action).pack(pady=20)

    def create_button(self, text, fg_color, command):
        """Create a CTkButton with specified text, color, and command."""
        return CTkButton(
            self,
            text=text,
            text_color="white",
            command=command,
            bg_color="#2B2631",
            fg_color=fg_color,
            font=("Segoe UI", 15),
        )

    def ok_action(self):
        """Action to be taken when Ok button is pressed."""
        # Stop threads when exiting
        self.thread_manager.stop_threads()
        self.master.quit()
        self.destroy()

    def cancel_action(self):
        """Action to be taken when Cancel button is pressed."""
        self.destroy()
