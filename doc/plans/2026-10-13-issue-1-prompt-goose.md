# Prompt per l'agente goose — issue #1 "Pulsante Ferma non funziona"

> File di lavoro per l'agente. Il piano completo è in `doc/plans/2026-10-13-issue-1-pulsante-ferma.md`, la diagnosi in `doc/issues/2026-10-13-github-issues.md`. **Leggi solo il task che ti viene assegnato**: ogni prompt è autosufficiente e uno eseguito dopo l'altro sullo stesso ramo.

## Come usare questo file

Cinque prompt, uno per task. Ogni prompt è completo e non richiede di sapere cosa hanno fatto i precedenti, tranne il test di verifica finale, che include il conteggio atteso.

**Consiglio operativo:** assegna **un prompt per sessione**. Se ne accorpi due in una sessione sola, l'agente li esegue in sequenza e il revisore non vede più una frontiera netta tra i task. La sequenza conta: il Task 2 dipende dal Task 1.

---

## Prompt 1 — Task 1: `StopButton.set_enabled` non spegne più il Canvas

```
Leggi il Task 1 di doc/plans/2026-10-13-issue-1-pulsante-ferma.md e quel task
lo esegui per intero, alla lettera, senza deviazioni.

Dove ti trovi: C:\Users\luca\test\local-llm, branch main, allineato con
origin/main a e882545. Suite di partenza: 152 test verdi.

Il difetto che stai correggendo, in una frase: StopButton.set_enabled(False)
esegue config(state="disabled") sul Canvas intero, e in Tkinter disabilitare
un Canvas non blocca "l'ottagono" ma blocca TUTTO il widget: smette di
consegnare qualunque evento, anche quelli gia' legati con tag_bind. Per questo
il pulsante Ferma, dopo che l'attivita' e' partita, non e' cliccabile.

Regole che valgono per questo task:
- Solo TDD: prima il test che fallisce, poi il codice minimo.
- Non modificare kemai_client/api/client.py e non aggiungere chiavi a i18n.STRINGS.
- Non aggiungere dipendenze.
- Ogni commit deve avere la suite completa verde.

Quando hai finito, riporta: l'output di pytest -q, l'hash del commit, e una
riga sul fatto che set_enabled(False) ora lascia il Canvas a state="normal".
Non dichiarare verificato a mano nulla che non hai visto tu: questo task non
ha passaggi umani, quindi o il test passa o il task non è finito.
```

---

## Prompt 2 — Task 2: `AppController.toggle()` a tre vie

```
Leggi il Task 2 di doc/plans/2026-10-13-issue-1-pulsante-ferma.md e quel task
lo esegui per intero, alla lettera, senza deviazioni.

Prerequisito: il Task 1 deve essere gia' committato. Verificalo con
git log -1 --oneline e con pytest: se set_enabled(False) non lascia il Canvas a
state="normal", fermati e riferisci che il Task 1 manca.

Perche' questo task esiste, e non e' un rifacimento: nel Task 1 il Canvas non
e' piu' spento, quindi un click su un bottone grigio ARRIVA davvero a toggle().
Senza la guardia a tre vie, start() partirebbe con project_id=None e farebbe
una POST al server con un progetto inesistente. Questo task rimette la
sicurezza nel posto giusto, cioe' nel controller e non nella UI.

Il punto che conta piu' di tutti nel test: quando la cascata e' incompleta
toggle() non deve fare NESSUNA richiesta, non solo "non deve partire un timer".
Asserisci che il FakeClient non registra start_timesheet ne' stop_timesheet.

Regole: solo TDD; niente dipendenze nuove; niente chiavi i18n nuove; ogni commit
con la suite completa verde.

Riporta: output di pytest -q, hash del commit, e la conferma esplicita che
toggle() con cascata incompleta non produce richieste.
```

---

## Prompt 3 — Task 3: `_refresh_state` abilita Ferma mentre l'attività è in corso

```
Leggi il Task 3 di doc/plans/2026-10-13-issue-1-pulsante-ferma.md e quel task
lo esegui per intero, alla lettera, senza deviazioni.

Questo e' il cuore della issue #1 e il suo test e' quello che, se fallisce,
dimostra che il bug non e' stato corretto:
test_button_enabled_while_running deve chiamare set_enabled(True) con
can_start() False e is_running() True.

Perche' quel test e' scritto come e': non devi costruire una MainWindow reale,
perche' il suo __init__ crea venti widget e registra un after. Usa
MainWindow.__new__(MainWindow) e inietta tre Mock (_controller, _stop_button,
_entry_started). Stai verificando il CONTRATTO DI CABLAGGIO — quale argomento
arriva a set_enabled — ed e' esattamente li' che il bug vive.

Il principio che i test stanno fissando, in parole: un controllo che sembra
cliccabile deve fare qualcosa, e un controllo che non puo' fare niente non deve
sembrare cliccabile. can_start() risponde a "posso avviare?", non a "e'
cliccabile?". Sono due domande diverse e vanno tenute separate.

NON cancellare i tre test strutturali gia' presenti in quel file: si aggiungono
ai cinque nuovi, quindi il file passa da 3 a 8 test.

Regole: solo TDD; niente dipendenze nuove; niente chiavi i18n nuove; ogni commit
con la suite completa verde.

Riporta: output di pytest -q, hash del commit, e le due righe di commento che
hai messo in _refresh_state.
```

---

## Prompt 4 — Task 4: un unico percorso di uscita che ferma il timesheet

```
Leggi il Task 4 di doc/plans/2026-10-13-issue-1-pulsante-ferma.md e quel task
lo esegui per intero, alla lettera, senza deviazioni.

Questo e' il secondo difetto della issue #1 ed e' quello piu' grave perche'
fa perdere ore di lavoro: oggi i tre "Esci" (File, Modifica, vassoio) chiamano
tutti root.quit() e basta. root.quit() chiude il main loop ma NON chiude il
record sul server e NON termina il processo, perche' il thread daemon di
pystray lo tiene vivo. L'app sparisce dalla taskbar e gira ancora nel vassoio.

Questo task cambia TRE firme. Rileggile prima di scrivere codice:
- build_menu(controller, root, on_quit) in tray.py: terzo parametro nuovo
- MainWindow.__init__(..., on_open_settings, on_new_project, on_quit): quinto
- compare exit_sequence(controller, root, tray) -> None in un modulo NUOVO
  kemai_client/exit_handler.py

L'ordine dentro exit_sequence NON e' negoziabile e c'e' un test che lo verifica
con una lista di chiamate: stop, tray_stop, quit, destroy. Chiudere il vassoio
dopo destroy lascia il thread daemon vivo, che e' esattamente il bug.

Le tre eccezioni che devi sopportare senza bloccare l'uscita: KimaiError da
stop() (401 incluso), RuntimeError da tray.stop(), e in ogni caso root.quit e
root.destroy devono essere comunque raggiunti. Un'uscita bloccata e' peggio di
un'uscita che non ha chiuso il record.

ATTENZIONE a due punti che rompono silenziosamente:
1. In app.py, MainWindow viene costruito PRIMA di tray. E' un closure, quindi
   va bene: tray viene risolto alla chiamata, non all'istruzione. Lo stesso
   schema e' gia' usato per on_open_settings e on_new_project.
2. Il ramo withdraw di on_close NON deve chiamare exit_sequence e NON deve
   fermare l'attivita'. Se l'utente ha "Chiudi nel vassoio" e preme la X,
   nascondersi senza fermare e' il comportamento giusto: fermare li farebbe
   perdere ore. Non "migliorare" quel ramo.

Nel test in tests/test_tray.py, AGGIORNA test_menu_callbacks_are_deferred per
la firma nuova: aggiungi un terzo argomento Mock. Non cancellarlo.

Regole: solo TDD; niente dipendenze nuove; niente chiavi i18n nuove; ogni commit
con la suite completa verde.

Riporta: output di pytest -q, hash del commit, e conferma esplicita che il
ramo withdraw non chiama exit_sequence.
```

---

## Prompt 5 — Task 5: etichetta del vassoio coerente con lo stato

```
Leggi il Task 5 di doc/plans/2026-10-13-issue-1-pulsante-ferma.md e quel task
lo esegui per intero, alla lettera, senza deviazioni.

Questo e' l'unico task che allarga il perimetro di quanto chiesto nella issue:
la voce "Avvia" del menu del vassoio dice sempre btn_start, anche mentre
l'attivita' e' in corso. Se preferisci non allargare, e' legittimo fermarsi
qui e dire che hai finito il perimetro stretto: in quel caso non fare questo
task e non mentire dicendo di averlo fatto.

Il motivo per cui vale la pena farlo e' che e' lo stesso difetto di classe
della issue #1: lo stato non raggiunge il controllo che lo muta. Un collega
che usa il vassoio ci arriva tra una settimana.

Perche' toggle_label e' una funzione e non una lambda inline: perche' sia
testabile. E' la stessa scelta che il progetto ha gia' fatto con close_behaviour,
ed e' l'unico modo di testarla senza dipendere dagli interni di pystray.

Nessuna chiave i18n nuova: btn_start e btn_stop esistono gia' nel dizionario, e
test_no_extra_keys asserisce che le chiavi siano esattamente 32.

Regole: solo TDD; niente dipendenze nuove; ogni commit con la suite verde.

Riporta: output di pytest -q, hash del commit, e le due asserzioni di toggle_label.
```

---

## Prompt finale — verifica complessiva e chiusura

Da dare **solo dopo** che tutti i task sono committati.

```
Esegui la sezione "Chiusura dell'intervento" di
doc/plans/2026-10-13-issue-1-pulsante-ferma.md.

Poi controlla una cosa sola, e dimmi il risultato: la suite deve dare
esattamente 172 passed e 0 failed. Se il numero e' diverso, il conteggio
ti dice subito che un task ha aggiunto o perso test rispetto al piano: nel
piano ogni task dichiara il totale atteso, e la sequenza e
152 -> 155 -> 158 -> 163 -> 170 -> 172.

Non chiudere la issue #1 su GitHub: e' il collega che l'ha aperta e la chiude
lui dopo aver verificato che il pulsante gli funziona.

Infine, elenca i quattro passaggi [UMANO] rimandati alla persona e scrivi per
ciascuno cosa hai lasciato esattamente da fare e come si fa a verificarlo.
Un agente che scrive "verificato a mano" senza aver visto nulla sta mentendo,
ed e' peggio di un agente che si ferma e lo dichiara.
```

---

## Se l'agente si blocca o sbaglia

**Segnali ricorrenti, e cosa significano.**

| Cosa dice | Cosa significa davvero |
|---|---|
| "Il test passa ma non so se il bug è risolto" | Il test verifica il cablaggio, non l'utente. Il wiring è corretto; serve un passaggio umano. Dillo, non indovinare. |
| "Ho aggiunto una chiave in i18n perché serviva un messaggio" | Fuori piano. `test_no_extra_keys` asserisce 32 chiavi esatte. Torna indietro e usa un messaggio già esistente. |
| "Ho dovuto modificare client.py perché l'endpoint era sbagliato" | Non è vero: gli endpoint sono verificati dal vivo. Sei cascato in una diagnosi sbagliata. Torna alla riga `Analysis` in doc/issues. |
| "Aggiungo pytest-mock per i mock" | Dipendenza nuova non necessaria. `unittest.mock` è già usato in tests/test_tray.py e tests/test_controller.py. |
| "Il Task 4 rompe l'ordine di costruzione in app.py" | È previsto e va bene: è un closure. Tray viene risolto alla chiamata, `on_quit` non viene mai invocato durante `MainWindow.__init__`. |
| "Non riesco a testare `on_close` perché vive dentro `main()`" | Corretto, ed è dichiarato nel piano: Review Focus #5 non ha test automatico ed è un passaggio umano. Non rifattorizzare `app.main()` per poterlo testare. |

**Il test che vale più di tutti**, se un agente consegna in fretta:
`tests/test_main_window.py::TestRefreshState::test_button_enabled_while_running`.
Se quello passa, la issue #1 è corretta alla fonte. Se passa solo perché
qualcuno ha cambiato la firma di `set_enabled` per accomodare il test, non è
corretta: rileggi la sezione **Interfaces** del Task 3.