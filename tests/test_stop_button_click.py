r"""Test del clic sul pulsante ottagonale, con Tkinter vero.

Perche' serve una finestra vera e non un Mock: il difetto non si vede
leggendo il codice, si vede cliccando.

`StopButton` disegna l'ottagono e POI l'etichetta sopra. In Tk un item
del canvas afferra il clic solo se e' il piu' in alto, quindi il testo
si mangia il clic sopra la parola "Avvia"/"Ferma": il posto dove
l'utente preme. Con l'etichetta larga ~30px il buco e' grosso, e il
pulsante sembra morto solo al centro.

Nota sul perche' qui si chiama `set_label`: a costruzione l'etichetta e'
vuota e il suo bbox e' di 2 pixel, quindi il difetto e' invisibile. La
finestra reale chiama `set_label` a ogni refresh: e' quello stato che va
testato, non quello del costruttore.

Su una root nascosta Tk non consegna eventi: qui la root viene mostrata
per il tempo del test e poi ri-nascosta.
"""

from unittest.mock import Mock

from kemai_client.i18n import t
from kemai_client.ui.widgets import StopButton


def _visible(root):
    """Mostra la root condivisa e restituisce il ripristino."""
    was_withdrawn = not root.winfo_ismapped()
    if was_withdrawn:
        root.deiconify()
    root.update()

    def restore():
        root.withdraw()
        root.update()

    return restore


def _button(root, clicked):
    """Pulsante come lo costruisce la finestra reale: con etichetta."""
    btn = StopButton(root, on_click=lambda: clicked.append(1))
    btn.pack()
    btn.set_label(t("btn_start"))  # "Avvia"
    root.update()
    return btn


class TestStopButtonClick:
    def test_click_on_the_label_activates_the_button(self, tk_root):
        """Il clic sulla parola "Avvia" deve attivare.

        E' il difetto: l'etichetta copre l'ottagono e, non avendo un
        binding, intercetta il clic. Il pulsante risultava morto
        esattamente al centro, dove si preme.
        """
        restore = _visible(tk_root)
        clicked = []
        try:
            btn = _button(tk_root, clicked)
            btn.event_generate("<Button-1>", x=36, y=36)
            tk_root.update()
            btn.destroy()
        finally:
            restore()

        assert clicked, (
            "il clic sopra l'etichetta non ha raggiunto la callback: "
            "l'etichetta copre l'ottagono"
        )

    def test_click_on_the_octagon_body_activates_the_button(self, tk_root):
        """La parte libera dell'ottagono funziona gia' e deve continuare."""
        restore = _visible(tk_root)
        clicked = []
        try:
            btn = _button(tk_root, clicked)
            btn.event_generate("<Button-1>", x=36, y=12)
            tk_root.update()
            btn.destroy()
        finally:
            restore()

        assert clicked

    def test_the_whole_widget_is_the_button(self, tk_root):
        """Il widget e' il pulsante: ogni clic dentro deve valere.

        Un binding a livello di Canvas copre etichetta, ottagono e bordi
        senza dipendere da quale item sia in cima, quindi il pulsante non
        si rompe di nuovo se domani si aggiunge un'etichetta lunga.
        """
        restore = _visible(tk_root)
        clicked = []
        try:
            btn = _button(tk_root, clicked)
            width, height = btn.winfo_width(), btn.winfo_height()
            points = [
                (width // 2, height // 2),   # sopra l'etichetta
                (width // 2, 12),           # ottagono
                (12, height // 2),           # ottagono
                (width // 2, height - 12),   # ottagono
                (3, 3),                      # angolo del widget
                (width - 4, height - 4),     # angolo opposto
            ]
            for x, y in points:
                btn.event_generate("<Button-1>", x=x, y=y)
                tk_root.update()
            btn.destroy()
        finally:
            restore()

        assert len(clicked) == len(points), (
            f"clic attivati: {len(clicked)} su {len(points)}"
        )

    def test_binding_is_on_the_canvas_not_on_one_item(self, tk_root):
        """Il binding non deve stare su un singolo item.

        Ogni item aggiunto in futuro coprirebbe quello sotto e si
        ripeterebbe lo stesso buco: e' esattamente come è nato.
        """
        restore = _visible(tk_root)
        try:
            btn = _button(tk_root, Mock())
            registered = btn.bind("<Button-1>")
            assert registered, (
                "il Canvas deve avere il binding: se sta solo sull'ottagono, "
                "qualsiasi item disegnato sopra lo rende irraggiungibile"
            )
            btn.destroy()
        finally:
            restore()

    def test_label_can_be_changed_without_breaking_the_click(self, tk_root):
        """Cambiare etichetta non deve cambiare la hit area."""
        restore = _visible(tk_root)
        clicked = []
        try:
            btn = _button(tk_root, clicked)
            for label in (t("btn_stop"), t("btn_start"), "X" * 40):
                btn.set_label(label)
                tk_root.update()
                n = len(clicked)
                btn.event_generate("<Button-1>", x=36, y=36)
                tk_root.update()
                assert len(clicked) > n, (
                    f"clic morto con etichetta {label!r}"
                )
            btn.destroy()
        finally:
            restore()