Sei in C:\Users\luca\test\local-llm. Questa e' una run notturna NON
supervisionata: lavori da solo fino in fondo, senza che nessuno ti
risponda. Per questo le regole di arresto contano piu' della tua fretta.

Sei un agente di coding che corregge un difetto segnalato da un collega.
Il piano di lavoro e' gia' scritto, verificato e messo in ordine: il tuo
compito e' eseguirlo alla lettera, non ridiscuterlo e non migliorarlo.

=======================================================================
DOVE LAVORI
=======================================================================

Crea un branch dedicato PRIMA di toccare qualsiasi cosa:

    git checkout -b fix/issue-1-ferma

Motivo della deviazione dal piano, che dice di lavorare su main: questa run
avviene senza nessuno che guardi. Se a meta' hai lasciato main in stato
rotto, il danno e' gia' fatto; su un branch main resta com'era, con i
152 test verdi, e il tuo lavoro e' isolato e reversibile. Quando avrai
finito, il branch si mergia solo dopo una revisione umana.

Verifica di partenza, e se una di queste due fallisce FERMATI:
    git log -1 --oneline           deve essere e882545
    .venv\Scripts\python.exe -m pytest -q     deve dare 152 passed

Non usare MAI il comando `python`: su questa macchina e' uno stub di 0 byte
del Microsoft Store che non esegue nulla. L'unico interprete e'
.venv\Scripts\python.exe.

=======================================================================
IL DIFETTO DA CORREGGERE
=======================================================================

Causa 1, grave, e' questa che ha rotto il pulsante. In
kemai_client/ui/main_window.py la riga 229 chiama
`set_enabled(self._controller.can_start())`. Ma can_start() restituisce
False quando c'e' un timesheet attivo, cioe' esattamente mentre l'attivita'
sta girando. E StopButton.set_enabled(False), in
kemai_client/ui/widgets.py, esegue `config(state="disabled")` sul Canvas
INTERO: in Tkinter disabilitare un Canvas non blocca "l'ottagono" disegnato
dentro, blocca tutto il widget e smette di consegnare qualunque evento,
anche quelli gia' legati con tag_bind. Risultato: dopo l'Avvia il bottone
si spegne da solo. L'etichetta continua pero' a dire "Ferma", quindi
l'utente vede un bottone grigio con scritto Ferma, e morto.

Causa 2, grave. I tre "Esci" (menu File riga 62, menu Modifica riga 69,
vassoio tray.py riga 167) chiamano tutti `root.quit()` e basta: nessuno
chiama controller.stop(), nessuno tray.stop(), nessuno root.destroy().
root.quit() chiude il main loop ma NON chiude il record sul server e NON
termina il processo, perche' il thread daemon di pystray lo tiene vivo.
L'app sparisce dalla taskbar e gira ancora nel vassoio. Ecco perche' il
collega ha visto comportamenti diversi tra un caso e l'altro.

Gli endpoint NON sono il problema: sono verificati dal vivo e sono
corretti. Non modificare kemai_client/api/client.py.

=======================================================================
DOVE IL PIANO E' E NON E' AUTOREVOLE
=======================================================================

Leggi ONCE, all'inizio, la sezione "Global Constraints" di
doc/plans/2026-10-13-issue-1-pulsante-ferma.md. Poi leggi i Task uno alla
volta, quando arrivi a ciascuno. NON rileggere il piano intero piu' volte:
il contesto e' il risorsa scarsa e ti e' gia' capitato di esaurirlo.

Il piano e' autorevole su: nomi dei file, nomi dei test, firme delle
funzioni, ordine delle operazioni, conteggi di test.

Il piano NON e' autorevole su: nulla. Se ti sembra che un passo sia
sbagliato, fermati e segnalalo. Non improvvisare.

=======================================================================
VINCOLI ASSOLUTI
=======================================================================

1. MAI cancellare, rinominare, saltare (`skip`) o indebolire un test
   esistente. Il numero di test puo' solo SALIRE, e solo della quantita'
   che il piano dichiara. Se un test esistente ti sta contro, il codice
   e' sbagliato, non il test. E' gia' successo: un altro agente ha
   cancellato 18 test per far passare la suite. Non lo rifai.

2. MAI scrivere un test che il piano non chiede. E' gia' successo anche
   questo: un altro agente si e' inventato un test con un'euristica
   sbagliata, quel test era insoddisfacibile, e il modello e' finito in un
   loop infinito trying-to-fix un requisito che si era auto-imposto. Se
   hai un'idea per un test che nel piano non c'e', lasciala fuori e
   segnalala alla fine.

3. MAI aggiungere chiavi a i18n.STRINGS. Un test asserisce che le chiavi
   sono esattamente 32, e aggiungerne una senza usarla rompe la suite.
   btn_start e btn_stop esistono gia' e bastano.

4. MAI aggiungere dipendenze. unittest.mock basta ed e' gia' usato nel
   repo. Niente pytest-mock.

5. MAI usare PowerShell per riscrivere un file intero, e MAI usare
   `Get-Content` per riaprire un file con accenti. Su questa macchina
   PowerShell legge con codepage 1252 e corrompe gli accenti UTF-8: e'
   gia' successo e ha reso illeggibili stringhe come "Attivita'". Se ti
   accorgi che un accento e' diventato "?", devi fare revert di quel file
   e rifarlo con l'editor, non rattoppare a mano.

6. Ogni commit deve avere la suite COMPLETA verde, non solo il file che
   hai toccato. Un commit che passa solo il proprio test non va committato.

7. Nessun segnaposto TODO o TBD nel codice finale.

8. Commenti e docstring in italiano, nomi di simboli pubblici in inglese.
   Segui lo stile gia' presente nei file che modifichi.

=======================================================================
PROCEDURA
=======================================================================

Esegui i cinque task nell'ordine. L'ordine NON e' decorativo: il Task 2
dipende dal Task 1, perche' il Task 1 toglie lo spegnimento del Canvas e
senza la guardia del Task 2 un click su un bottone grigio arriverebbe
davvero a toggle() e farebbe una POST con project_id=None.

    Task 1  widgets.py     set_enabled non spegne piu' il Canvas   152 -> 155
    Task 2  controller.py  toggle() a tre vie                     155 -> 158
    Task 3  main_window.py Ferma cliccabile mentre gira           158 -> 163
    Task 4  exit_handler   un unico percorso di uscita            163 -> 170
    Task 5  tray.py        etichetta del vassoio coerente         170 -> 172

Dopo ogni task: run della suite completa, confronto con il numero atteso,
poi commit con il messaggio che il piano prescrive. Se il numero non
corrisponde, il task NON e' finito: fermati e riporta la differenza.

=======================================================================
LA TRAPPOLA DEL TEST CHE PASSA SUBITO
=======================================================================

Questo e' il controllo che distingue un lavoro vero da un lavoro
compiaciuto. Il piano chiede, per ogni test, di vederlo FALLIRE prima
dell'implementazione e poi passare. Se scrivi un test che passa gia' alla
prima esecuzione, quel test non sta verificando la correzione: hai scritto
un test che conferma il codice di prima. In quel caso FERMATI e riscrivilo.

Il test piu' importante di tutti e' questo:

    tests/test_main_window.py::TestRefreshState::test_button_enabled_while_running

Deve fallire PRIMA del Task 3 e passare DOPO. Se non l'hai visto
fallire, non hai corretto la issue #1: hai solo cambiato qualcosa.

Attenzione al modo scorretto di farlo passare: non cambiare la firma di
set_enabled, non aggiungere un parametro nuovo, non modificare la
docstring per far quadrare i conti. La firma di `set_enabled` resta
`set_enabled(self, enabled: bool) -> None`. Rileggi la sezione Interfaces
del Task 3 se sei tentato.

=======================================================================
REGOLA ANTI-LOOP
=======================================================================

Se ti blocchi, usa questa procedura e non improvvisare:

  - Lo stesso approccio fallisce due volte di fila? FERMATI. Non
    ripetere un terzo giro cambiando parole. Cambiare approccio senza
    sapere perché il primo non funzionava è come il modello che traduceva
    "File" in italiano e non accettava che la traduzione fosse "File".

  - Un test che hai scritto tu è insoddisfacibile e non riesci a farlo
    passare? Quasi certamente il requisito è sbagliato, non il codice.
    FERMATI e riporta il test e l'impossibilità. Non "sistemarlo" a forza
    e non cancellarlo di nascosto.

  - Il piano e il codice reale si contraddicono? FERMATI e riporta la
    contraddizione. Non scegliere da che parte stare e andare avanti.

In tutti e tre i casi: lascia il branch con i task già finiti committati,
e riporta esattamente dove ti sei fermato e perché. Un agente che si
ferma e dichiara il blocco è UTILE. Un agente che "risolve" inventando un
requisito e toccando 40 file è un disastro che costa più di quanto ha
risparmiato.

=======================================================================
PASSAGGI UMANI: NON ESEGUIRLI
=======================================================================

Il piano ha una sezione "Passaggi riservati all'umano" con quattro voci.
Non sono tue. NON eseguirle, NON simularle, NON scrivere che le hai fatte.

Non puoi premere un pulsante, non puoi guardare una finestra, non puoi
vedere se il processo di Python è davvero terminato. L'unica cosa che puoi
fare è scrivere i test che coprono quei comportamenti dove sono copribili
automaticamente, e dichiarare il resto come non verificato.

Scrivere "verificato a mano" senza aver visto nulla è mentire, ed è
peggio di un agente che si ferma e dice "non posso verificarlo". Alla
fine della tua relazione, elenca i quattro passaggi umani rimandati e
cosa serve fare per ciascuno.

=======================================================================
COSA DEVI CONSEGNARE
=======================================================================

Alla fine, in questo ordine e senza reticenza:

1. L'output finale di pytest -q. Deve dire 172 passed. Se non lo dice,
  consegna comunque il lavoro e spiega il numero che hai trovato: un
  conteggio diverso da quello atteso significa che un task ha aggiunto o
  perso test rispetto al piano, e quella informazione vale più di un
  verde altrimenti poco convincente.

2. Una tabella con cinque righe, una per task: nome del file toccato,
  hash del commit, numero di test prima e dopo.

3. Per ogni task, una riga che dica cosa hai cambiato e PERCHE'. Non come
  hai cambiato: lo si vede nel diff. Perché è l'unica cosa che il diff non
  dice.

4. Qualcosa che hai fatto che il piano non chiedeva, o una decisione che
  hai presointerpretando un passo ambiguo. Se non hai fatto niente di
  questo, scrivi esplicitamente "niente": il silenzio su questo punto
  vuol dire che hai seguito il piano alla lettera, ed è una notizia utile.

5. I quattro passaggi umani rimandati, uno per uno, con come verificarli.

6. git log --oneline fix/issue-1-ferma, i cinque commit in ordine.

Non fare merge su main. Non cambiare il default branch del repository.
Non chiudere la issue #1 su GitHub: è il collega che l'ha aperta e la
chiude lui dopo aver verificato che il pulsante gli funziona.