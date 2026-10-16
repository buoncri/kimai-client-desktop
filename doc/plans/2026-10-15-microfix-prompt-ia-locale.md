Sei in C:\Users\luca\test\local-llm. Questa e' una run notturna NON
supervisionata: lavori da solo fino in fondo, senza che nessuno ti
risponda. Per questo le regole di arresto contano piu' della tua fretta.

Sei un agente di coding. Il piano di lavoro e' gia' scritto, verificato
e messo in ordine nel file sotto: il tuo compito e' eseguirlo alla
lettera, non ridiscuterlo e non migliorarlo.

    doc/plans/2026-10-15-microfix-ia-locale.md

Sono 7 micro-task di igiene e micro-bug (config, i18n, probe_api,
log degli errori di select, helper ottagono, helper combo,
micro-igiene). Nessuno cambia comportamento visibile dell'app.

=======================================================================
DOVE LAVORI
=======================================================================

Crea un branch dedicato PRIMA di toccare qualsiasi cosa:

    git checkout -b chore/microfix-ia-locale

Motivo: questa run avviene senza nessuno che guardi. Se a meta' hai
lasciato main in stato rotto, il danno e' gia' fatto; su un branch
main resta com'era, con i 221 test verdi, e il tuo lavoro e' isolato
e reversibile. Quando avrai finito, il branch si mergia solo dopo
una revisione umana. Non mergiare, non pushare, non aprire PR.

Verifica di partenza, e se una di queste due fallisce FERMATI:

    git log -1 --oneline                    deve essere ffece5b
    .venv\Scripts\python.exe -m pytest -q   deve dare 221 passed

Non usare MAI il comando `python`: su questa macchina e' uno stub di 0
byte del Microsoft Store che non esegue nulla. L'unico interprete e'
.venv\Scripts\python.exe. Ogni `pytest` nel piano significa
`.venv\Scripts\python.exe -m pytest`.

=======================================================================
COME LEGGI IL PIANO
=======================================================================

Leggi ONCE, all'inizio, le sezioni "DOVE LAVORI", "VINCOLI ASSOLUTI" ed
"ESCLUSO DA QUESTO PIANO" del piano. Poi leggi i Task uno alla volta,
quando arrivi a ciascuno. NON rileggere il piano intero piu' volte:
il contesto e' la risorsa scarsa.

Il piano e' autorevole su: nomi dei file, nomi dei test, firme delle
funzioni, stringhe esatte, ordine dei task, conteggi di test.

Il piano NON e' autorevole su: nulla. Se ti sembra che un passo sia
sbagliato, fermati su quel task e passa al successivo senza toccarlo.
Non improvvisare alternative.

=======================================================================
VINCOLI ASSOLUTI (ripetuti perche' valgono piu' della fretta)
=======================================================================

1. MAI cancellare, rinominare, saltare (`skip`) o indebolire un test
   esistente. Il numero di test puo' solo SALIRE, e solo della quantita'
   che il task dichiara (221 -> 222 -> 223 -> 225 -> 227 -> 229 ->
   230 -> 230). Se un test esistente ti sta contro, il codice e'
   sbagliato, non il test.
2. MAI modificare la firma di una funzione esistente.
3. MAI cambiare comportamento visibile dell'app.
4. Dopo OGNI task: suite intera verde prima del commit. Se e' rossa,
   ripara subito: non andare avanti con la suite rossa.
5. Un commit per task, con il messaggio indicato nel task. Alla fine
   `git status --short` deve essere vuoto (tutto committato).

=======================================================================
QUANDO HAI FINITO
=======================================================================

Verifica finale (dal piano, sezione "VERIFICA FINALE"): 230 passed,
7 commit sopra ffece5b, working tree pulito. Poi FERMATI e scrivi il
riepilogo (una riga "Task N: ok" per task). Non mergiare, non pushare.
