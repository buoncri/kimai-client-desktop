r"""Test strutturale delle finestre di Task 10.

Verifica solo la struttura: presenza delle classi e dei metodi.
La verifica visiva (layout, colori, posizione) è **[UMANO]** —
Task 12 Step 4.

Questo file non importa Tkinter: controlla solo che i moduli
siano importabili e che le classi espongano l'API attesa.
"""

from kemai_client.ui.settings_window import SettingsWindow
from kemai_client.ui.project_dialog import ProjectDialog


class TestSettingsWindow:
    def test_settings_window_exists(self):
        assert SettingsWindow is not None

    def test_settings_window_has_test_connection(self):
        assert hasattr(SettingsWindow, "test_connection")

    def test_settings_window_has_save(self):
        assert hasattr(SettingsWindow, "save")

    def test_settings_window_has_cancel(self):
        assert hasattr(SettingsWindow, "cancel")


class TestProjectDialog:
    def test_project_dialog_exists(self):
        assert ProjectDialog is not None

    def test_project_dialog_has_result(self):
        assert hasattr(ProjectDialog, "result")

    def test_project_dialog_has_save(self):
        assert hasattr(ProjectDialog, "save")

    def test_project_dialog_has_cancel(self):
        assert hasattr(ProjectDialog, "cancel")
