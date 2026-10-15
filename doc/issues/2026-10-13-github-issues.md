# Issue GitHub - kimai-client-desktop

- Repo: buoncri/kimai-client-desktop (pubblico)
- URL: https://github.com/buoncri/kimai-client-desktop
- Branch di default: `qwen38-35b-distill`
- Scaricato il: 2026-10-13 (via API `GET /repos/buoncri/kimai-client-desktop/issues`)
- Issue totali: 1 (aperte: 1)

| # | Stato | Titolo | Autore | Aperta |
|---|-------|--------|--------|--------|
| [#1](https://github.com/buoncri/kimai-client-desktop/issues/1) | open | Pulsante Ferma non funziona | @edi1973 | 2026-10-13 |

---

## #1 - Pulsante Ferma non funziona

- URL: https://github.com/buoncri/kimai-client-desktop/issues/1
- Stato: open
- Autore: @edi1973
- Creata: 2026-10-13T10:59:46Z
- Commenti: 0

### Testo integrale

```
Come da oggetto non funziona il pulsante Ferma una volta avviata l'attività dallo stesso pulsante (Avvia). In un caso uscendo dal menù Modifica - Esci ha salvato. In un altro non ha nemmeno salvato. Cercherò di indagare se c'è una logica in questo
```

### Analisi (2026-10-13)

Il difetto è nel cablaggio tra `can_start()` e lo stato "disabled" del pulsante, non
nell'endpoint. `toggle()` e `stop()` sono corretti: il semplice fatto che il click non
arriva è sufficiente a spiegare il sintomo.

**Causa 1 - il pulsante si disabilita da solo mentre cronometra (grave)**

`kemai_client/ui/main_window.py:229`

```python
self._stop_button.set_enabled(self._controller.can_start())
```

`AppController.can_start()` (`kemai_client/controller.py:269-277`) restituisce `False`
quando `self._timesheet_id` è valorizzato, cioè esattamente mentre un'attività è in
corso. Effetto a catena:

1. l'utente preme Avvia -> `start()` imposta `_timesheet_id` -> `notify()` -> `refresh()`;
2. `_refresh_state()` chiama `set_enabled(False)`;
3. `StopButton.set_enabled(False)` (`kemai_client/ui/widgets.py:127-130`) esegue
   `self.config(state="disabled", ...)` **sul Canvas intero**: da quel momento Tkinter
   non consegna più *nessun* evento a quel widget, nemmeno a quelli già legati con
   `tag_bind`;
4. il label al centro resta "Ferma" (`main_window.py:226-228` lo imposta da
   `is_running()`), quindi l'utente vede un bottone che dice "Ferma", grigio e morto.

Il pulsante è letteralmente spento mentre serve di più: è l'unico modo per fermarlo.
`can_start()` è la risposta corretta alla domanda "posso avviare?", non a "il pulsante
è cliccabile?". Le due condizioni vanno tenute separate.

**Causa 2 - nessuna percorso di uscita ferma il timesheet (grave)**

Tutti i tre "Esci" chiamano `root.quit()` e basta, senza mai passare da
`controller.stop()`:

- `main_window.py:62` - File > Esci -> `self._root.quit`
- `main_window.py:69` - Modifica > Esci -> `self._root.quit`
- `tray.py:167` - vassoio > Esci -> `root.after(0, root.quit)`

`root.quit()` termina il main loop ma non chiude il record sul server: il timesheet
resta aperto in Kimai. In più non chiama `tray.stop()` né `root.destroy()`
(il commento in `app.py:100` dice "Destroy richiede root.quit() + tray.stop()" ma il
destroy non c'è), quindi il thread daemon di pystray tiene vivo il processo: l'app
scompare dalla taskbar ma gira ancora nel vassoio. Da qui l'incoerenza descritta
nella issue, fra un caso "ha salvato" e uno "non ha nemmeno salvato": in un caso il
collega ha creduto fosse uscita quando stava solo andando nel vassoio, e la
chiusura è comunque delegata a mano su Kimai.

**Debolezza dei test che ha lasciato passare il bug**

`tests/test_main_window.py` contiene solo tre smoke test (`test_main_window_exists`,
`test_main_window_has_refresh`, `test_main_window_has_start_ticking`), tutti `hasattr`.
Nessun test esercita `_refresh_state()` né il contratto "il pulsante Ferma è
cliccabile mentre l'attività è in corso". `can_start()` invece è ben coperto
(`test_controller.py:131-140`) ed è proprio lì che il difetto è visibile: c'è un
test che asserisce `can_start() is False` a timesheet attivo, cioè la semantica è
voluta e corretta per l'avvio, e solo l'uso nella UI è sbagliato.

Linea di base: 152 test passati (`pytest -q`, 0.76 s) su `main` = `origin/main` = `e882545`.

### Correzioni da applicare

1. Separare i due concetti nella UI: il pulsante è cliccabile se
   `can_start() or is_running()`, cioè se la cascata è completa (per avviare) **o**
   se c'è un'attività in corso (per fermare).
2. Non usare `state="disabled"` sul Canvas per la disattivazione: in
   `set_enabled(False)` spegnere solo i colori, e lasciare che siano `can_start()` /
   `is_running()` a decidere se il click debba essere onesto. Così l'utente non può
   cliccare un bottone che non fa niente, senza disattivare i binding.
3. Unificare i tre "Esci" in una sola funzione di uscita che, nell'ordine:
   ferma il timesheet se in corso -> `tray.stop()` -> `root.destroy()`.
4. Se `stop()` fallisce per rete, non bloccare l'uscita: avvisare e uscire lo stesso,
   registrando l'evento nel log.
5. Copertura obbligatoria: test su `_refresh_state()` che verifica il pulsante
   cliccabile in tutti e tre gli stati (cascata incompleta, pronto, in corso).