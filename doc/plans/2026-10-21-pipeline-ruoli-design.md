# Pipeline a ruoli per lo sviluppo assistito: design

**Data**: 2026-10-21
**Stato**: Design approvato (implementazione da fare)
**Autore**: Luca + supervisore
**Verifica empirica**: due A/B su task reali del repo (`kemai_client/config.py`,
`kemai_client/geometry.py` + `exit_handler.py`), piu' misure dai log di Lemonade
(`%TEMP%\lemonade-server.log`) e dal campionamento della RAM

---

## 1. Perche' una pipeline a ruoli, e perche' con questi vincoli

Il box ha **un solo modello LLM residente** (Lemonade `max_loaded_models: 1`),
31,1 GB di RAM di cui ~7 GB lasciati al sistema, 4 GB di VRAM (RX 6400) e inferenza Vulkan/CPU.
Misure decisive:

- **Il costo di un turno non e' la generazione, e' il prefill** della conversazione
  crescente (ogni turno ri-prefilla tutto) piu' la verbosita' del modello.
- I modelli **MoE con 2-3B attivi** battono i densi di 4-7x sul prefill:
  FrogNano-4B 88,6 t/s, LFM2.5-24B-A2B 73,1, Qwen3.8-35B-A3B 43,9,
  Granite-4.2-8B (denso, 8B attivi) 11,6.
- I ruoli builtin di `pi-subagents` **sono gia' costruiti per questa catena**:
  `scout` produce `context.md`, `worker` ha `defaultReads: context.md, plan.md`,
  `oracle` e' descritto come "decision-consistency oracle" ed e' il source degli
  "approved oracle handoffs", `reviewer` ha `watchdog_diff` e un formato di output
  rigido, `delegate` "inherits the parent model with no default reads".

Conseguenza progettuale: **il piano sposta l'intelligenza dall'esecutore al
pianificatore**. L'esecutore non deve scoprire nulla, deve eseguire: e' il motivo
per cui un modello da 4B regge il ruolo di scrittore.

## 2. La pipeline in cinque passi

| # | passo | ruolo builtin | modello | artefatto prodotto | costo misurato |
|---|---|---|---|---|---|
| 1 | ragionare sull'intervento | `scout` (ricognizione stretta: file, simboli, entry point) | LFM2.5-24B-A2B | `context.md` | swap 2-6 s + 2-4 min |
| 2 | creare il piano | `oracle` (fork del contesto del main) | Qwen3.8-35B-A3B | `plan.md` (criteri di accettazione, file toccati, test da far passare) | prefill incrementale nel main |
| 3 | eseguire il piano | `worker` (legge `plan.md` + `context.md`) | FrogNano-4B | diff + output dei test | swap 2 s + ~6 min |
| 4 | valutare l'esecuzione | `reviewer` (sul diff, contro test/requisiti) | modello indipendente (vedi 8) | review con P0/P1/P2 + merge verdict | swap 20-30 s + 5-12 min |
| 5 | committare | main | Qwen3.8-35B-A3B | commit | nel main |

Il passo 4 **non** riceve il piano: riceve i **criteri di accettazione** e verifica
il codice contro codice, test e documentazione. Solo cosi' puo' dire "l'obiettivo
era sbagliato", invece di limitarsi a verificare la conformita' al piano.

## 3. Mappa ruoli -> modello

| ruolo | modello | note |
|---|---|---|
| `main` | Qwen3.8-35B-A3B | 43,9 t/s prefill, 18,3 decode; il piu' conciso e accurato misurato |
| `oracle` | Qwen3.8-35B-A3B | pianifica: fork del contesto del main |
| `researcher` | Qwen3.8-35B-A3B | invariato (web research) |
| `evidence-auditor` | Qwen3.8-35B-A3B | invariato |
| `reviewer` | **indipendente** (vedi 8) | fresh context, non negozia i finding |
| `scout` | LFM2.5-24B-A2B | solo ricognizione: la sua verbosita' qui e' un vantaggio (scrive `context.md`) |
| `worker` | FrogNano-4B | **unico scrittore**; 2/2 pulite su entrambi i task, diff minimo, 3,2 GB, load 2 s |
| `delegate` | *nessun override* | eredita il modello del main: non e' un secondo profilo di scrittura |

## 4. Invarianti

1. **Un solo scrittore.** `worker` scrive il codice; `delegate` non ha override e
   segue il main. Nessun doppio profilo.
2. **Il piano trasporta l'intelligenza.** L'esecutore esegue, non scopre.
3. **Il reviewer e' indipendente** dal pianificatore e dall'esecutore, e gira in
   **contesto fresco** (non nel contesto lungo del main: un prefill da 45k token
   nel main costa ~17 minuti, in un subagent da 8k costa ~3 minuti).
4. **Il reviewer non negozia i propri finding.** In Pi il supervisore di un
   subagent e' la sessione padre, cioe' l'autore del piano: se il reviewer chiede
   "il mio finding e' valido?", la risposta arriva da chi ha scritto il piano.
   Divieto esplicito nel task (vedi 5).
5. **Un modello residente.** Gli swap sono il costo per task e vanno contati:
   ~2-6 s (Frog, LFM) e ~20-30 s (i modelli da 13-22 GB).
6. **Nessun modello cloud, nessun agente custom, un modello per ruolo**
   (nessuna alternanza per richiesta).

## 5. Protocollo del reviewer (test da usare)

Il task che il main compone per il reviewer deve contenere:

- il diff e il "seam" di codice interessato, piu' i **criteri di accettazione**
  (non il piano);
- "verifica ogni affermazione contro codice, test e documentazione; cita
  `file:line`";
- **"non usare `contact_supervisor` per giudicare un finding**: se sei incerto,
  riportalo come P2 con l'incertezza esplicita. Non chiedere al supervisore se
  un finding e' valido";
- output: `## Review`, `Correct`, `Finding` con P0/P1/P2 e `file:line`,
  `Merge verdict: BLOCK | OK | OK with notes`, e la frase esatta
  `No issues found.` se non c'e' nulla.

Il main, a sua volta, **non risponde alle domande tecniche del reviewer**: legge
la review finale e decide (o escala all'umano).

## 6. Costi misurati (riassunto)

Ruolo worker/coder, due task reali:

| modello | task | durata | turni | token out | diff | esito |
|---|---|---|---|---|---|---|
| FrogNano-4B | coder (2 file, 4 bug) | 357,9 s / 393,6 s | 15 / 13 | 3.169 / 3.007 | 2 / 2 | 2/2 PULITO, 8/8 e 8/8 |
| Qwen3.8-35B-A3B | coder | 278,5 s / 386,4 s | 13 / 13 | 2.147 / 2.587 | 2 / 8 | 2/2 PULITO, 8/8 e 6/8 |
| LFM2.5-24B-A2B | coder | 1.752,2 s | 52 | 27.945 | 2 | PULITO ma 2 violazioni di protocollo |
| FrogNano-4B | worker (`config.py`) | 297,1 s / 434,2 s | 9 / 9 | 1.468 / 2.749 | 2 / 2 | 2/2 PULITO |
| Qwen3.8-35B-A3B | worker (`config.py`) | 515,7 s / 295,0 s | 16 / 6 | 4.024 / 1.560 | 3 / **0** | 2/2 PULITO |

Frog e' il piu' **costante** (diff 2 sempre, 9 turni sempre); Qwen3.8 e' il piu'
**capace** ma variabile (una run ha ripristinato `config.py` esattamente all'originale,
diff 0; l'altra ha aggiunto 8 righe e 2 commenti gratuiti).

RAM (contesto 64k, KV committata lazy): Qwen3.8 22,1 GB residenti (~2 GB liberi),
LFM 14,6 GB (~9 GB liberi), Qwen3-Coder 21,3 GB (~4 GB liberi).

Domanda di contesto misurata: i ruoli subagent vivono con **2-4k token** (16k
bastano); la sessione main e' l'unico vero consumatore (~45k token, ~3 GB di KV).

## 7. Decisioni prese

- `worker`/`delegate` restano su **FrogNano-4B**: non si elimina Frog.
- Il `reviewer` sara' **indipendente** (non l'oracle): il costo e' uno swap
  (~25 s) su una review da 5-12 minuti, e il beneficio e' che il reviewer possa
  dire "il piano era sbagliato".
- Lo `scout` resta, ma con un task **stretto** (mappa file/simboli), non una
  ricognizione completa.
- Nessun ruolo custom: si usano i builtin con `agentOverrides` in `settings.json`.

## 8. Cosa resta aperto

1. **Validare Frog su un piano vero.** Gli A/B precedenti misuravano Frog su task
   di *scoperta* (trovare il bug), non di *esecuzione di un piano*. Va fatta una
   run con `plan.md` reale: il worker deve eseguire, non scoprire.
2. **Il reviewer indipendente: quale modello.** Qwen3-Coder-30B-A3B ha **rilevato
   il bug seminato** con citazioni `file:line` e verdict BLOCK, ma la run e' stata
   lenta (18 min di cui ~8 di round-trip `contact_supervisor`, cioe' protocollo e
   non modello) e ha prodotto **un'allucinazione** ("un `return points` dentro il
   for loop" che nel diff non c'e'). Alternative in valutazione: GLM-4.7-Flash
   (17,5 GB, famiglia diversa, MoE), Qwen3.5-9B (6,9 GB, economico), Ornith-1.5-35B-A3B
   (22,6 GB, A3B + coding/reasoning/tool-calling).
3. **Contesto dei modelli grandi**: il `ctx_size` richiesto per Qwen3-Coder non e'
   stato riconosciuto (Pi pubblica 262,1K nativi invece di 32k) e va sistemato; va
   misurata la pendenza della KV con un carico lungo.

## 9. Cosa non cambia

- Ruoli builtin di `pi-subagents`, nessun agente custom.
- Un modello per ruolo, nessuna alternanza per richiesta, fallback esplicito.
- Solo modelli locali via Lemonade; nessun modello cloud.
- L'`oracle` resta diverso dal `reviewer`.
