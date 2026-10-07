r"""Test strutturale della finestra principale.

Verifica solo la struttura: presenza della classe, dei metodi e dei
widget di base. La verifica visiva (layout, colori, posizione) è
**[UMANO]** — Task 12 Step 4.

Questo file non importa Tkinter: le finestre Tk non si testano via
assert su coordinate, ma si importa il modulo e si controlla che
l'API sia esposta.
"""

from kemai_client.ui.main_window import MainWindow


class TestMainWindowStructural:
    """Struttura di MainWindow — senza creare un oggetto reale."""

    def test_main_window_exists(self):
        """La classe MainWindow è importabile."""
        assert MainWindow is not None

    def test_main_window_has_refresh(self):
        """MainWindow ha il metodo refresh."""
        assert hasattr(MainWindow, "refresh")

    def test_main_window_has_start_ticking(self):
        """MainWindow ha il metodo start_ticking."""
        assert hasattr(MainWindow, "start_ticking")
