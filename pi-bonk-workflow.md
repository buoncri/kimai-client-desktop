# Workflow Pi + Lemonade — schema attuale (aggiornato 2026-10-29)

Hardware ridotto: Lemonade Server (llama.cpp, Vulkan) + Pi Agent + pi-subagents + pi-superpowers.
Criteri: qualità batte velocità; un solo modello alla volta in VRAM (swap 8-30 s, accettabile).

## Mappa ruoli definitiva (confermata con A/B 26-28/10)

| Fase | Ruolo | Modello | Note |
|---|---|---|---|
| F0 Brainstorming | skill pi-superpowers nel **main session** | qwen3.8 IQ4_XS (defaultModel) | variante-2 confermata: delega al primo turno (26/10 e 28/10, anche senza pensiero) |
| F1 Pianificazione | subagent `oracle` | Qwen3.8-35B | riceve il riassunto F0 nel `task`; legge i sorgenti da solo; piano con `file:line`; domande di chiarimento PRIMA del piano |
| F2 Implementazione | subagent `worker` | Spark-X2.6-4B (Q5_K_M) | CONFERMATO con A/B 28/10 (987 s vs timeout di Flint-Q2); unico scrittore; esegue il piano alla lettera (non esplora) |
| F3 Review | subagent `reviewer` | FrogNano-4B | routine: 157 s, zero falsi positivi; cross-check profondo → seconda opinione a Flint |

Seconda opinione / deep-worker: **Flint-39.8B** (UD-Q2_K_XL 12,6 GB predefinito; IQ4_XS 20,7 GB; UD-Q3_K_XL 17,2 GB)
— giudice/cross-check puntuale su poche deleghe, MAI esecutore implementativo: prefill ~21,7 t/s con
ri-prefill completo per turno = 4-6 min/turno → timeout sui task di scrittura (A/B 28/10: 0 file in 30 min).
UD-Q3_K_XL (17,2 GB): provato dall'utente il 27/10, resta in catalogo come riserva (fuori mappa ruoli);
impressione d'uso non più ricordata (29/10) — eventuale ritest quando Flint tornerà in primo piano.
Riserve: `delegate` = FrogNano; `researcher`/`evidence-auditor` = Qwen3.8-35B (pensiero attivo
dalla mattina del 29/10, vedi Config — prima del 29/10 giravano senza pensiero: collasso F1 del 28/10).
Scout: scartato dalla pipeline (mai consumato in 30+ run valide); override `scout → gpt-oss` mantenuto
come fallback a costo zero.
Ornith-1.5 ritirato il 28/10 (catalogo + 18,8 GB su disco liberati): catch profondo ma 30+ min/run;
ruolo coperto da Flint (profondo) e frog (routine).

## Config attiva (29/10)

- `~\.pi\agent\settings.json`: `defaultModel` = Qwen3.8-35B-A3B-Distill-GGUF-IQ4_XS (lemonade);
  agentOverrides: scout=gpt-oss-20b-Q4_K_M · worker=Spark-Q5 · delegate=FrogNano ·
  researcher/oracle/evidence-auditor=Qwen3.8 · reviewer=FrogNano
- `recipe_options.json`, entrata qwen: `--chat-template-kwargs '{"enable_thinking":true}'` +
  `--reasoning on` + `--spec-type draft-mtp` → pensiero ATTIVO server-level (29/10; sonde:
  reasoning_content separato, content pulito, tool-calling OK — vedi causa radice in coda)
- entrata gpt-oss: `--reasoning-format auto --chat-template-kwargs '{"reasoning_effort":"low"}'` (arm 3, riserva)
- Catalogo Lemonade: 11 voci (dopo ritiro ornith); Flint-UD-Q2_K_XL montato e testato 28/10
- Backup: `recipe_options.json.bak-qwen-thinkoff-20261028` · `user_models.json.bak-ornith-20261028` ·
  `backups\settings-ornith-removal-20261028.json` (+ storici: `settings-qwen-main-arm-20261026`,
  `.bak-flint-20261026`, `stack-step1-20261023`)
- Deposito: commit `2076bb0` (lerp) + `6dbeba4` (polyline_length) su main; baseline attesa
  **"1 failed, 297 passed"** (`TestCheckActiveSession`, permanente — aggiornare il numero a ogni
  commit di test); test sempre col venv del repo (`.venv\Scripts\python.exe -m pytest`)

## Invocazione subagent (schema del tool, pi-subagents)

```json
subagent({ "agent": "oracle", "task": "..." })
```

- Nomi agente **minuscoli**: oracle, worker, reviewer, scout, delegate...
- `action` solo per gestione (`status`, `guide`, `children.list`) — `action:"guide"` restituisce la
  documentazione, NON lancia una run
- `agent` maiuscolo o `message` al posto di `task` = call respinta
- Il main decide se chiamare `subagent`; in sessioni fresh il tool parte come loader
  (`subagents_enable`) che il main deve richiamare prima
- ⚠ `max_runtime_ms` nel TESTO del prompt NON viene applicato (arm Flint-Q2 28/10 tagliata a 1800 s
  anziché 2700): passarlo top-level della call e verificarlo nel meta

## Regole operative

- Baseline test intoccata: "1 failed, 297 passed" è l'attesa in ogni run
- Perimetro drift dichiarato nel piano; worker unico scrittore; review indipendente
- Teatro: server HTTP porta **13305** (`/api/v1/health`; 9000 = WebSocket); `NO_PROXY=127.0.0.1`
  con Invoke-RestMethod; log `$env:TEMP\lemonade-server.log`
- Backends: pin llama.cpp **b11895** in `backend_versions.json` (supporto arch flint; backup `.bak-flint-20261026`)

## Lezioni consolidate (26-28/10)

- **Verifica sempre sul grezzo**: mai fidarsi della parafrasi del main — il 28/10 ha affermato un
  falso («implementazione ancora in main» con deposito pulito). Conteggi dei child: verificare il SET
  eseguito (il «22» era giusto: 10+10+2, ma la parafrasi non esplicitava il set).
- **Interruttori generativi**: qwen → `--reasoning on/off` + `enable_thinking` nei kwargs; gpt-oss →
  `reasoning_effort` nei kwargs. ⚠ DAL BACKEND b11895 `--reasoning off` SOPPRIME la generazione del
  pensiero (non è più solo visualizzazione come sul backend vecchio) e PREVALE sui kwargs: il 28/10
  il think-off era reale, il 29/10 il ripristino col solo kwarg `enable_thinking:true` è stato un
  no-op finché non è entrato `--reasoning on`. `auto` = rileva dal template (qwen3.8-distill →
  niente pensiero). La per-richiesta `chat_template_kwargs` vince sul server-level (override al volo
  possibile). La cronologia col pensiero: `--reasoning-preserve` (default GIÀ attivo; il kwarg
  `preserve_thinking` era inutile).
- **Le etichette del catalogo Lemonade non sono verificate in pratica** (AceStep-5Hz: label
  chat/tool-calling ma genera token musicali, contenuto vuoto): sondaggio di chat (~13-15 s) sempre
  per le voci nuove.
- **Le sonde piccole sovrastimano**: Flint-Q2 19-22 t/s in sondaggio ma 13,6-16 t/s in lavoro reale;
  il collo è il prefill (21,7 t/s vs 51 di qwen; cache KV non riutilizzata tra turni → TTFT 4-6 min).
- **Pensiero forzato al template** (Flint, ornith): non disattivabile → la tassa si moltiplica per i turni.
- **Think-off del main**: la delega regge (2/2 gate F0 superati); da sorvegliare la qualità su
  contesti lunghi (primo segnale: affermazione falsa nel rapporto finale 28/10).
- Windows: file `nul` (nome riservato) si rimuove col prefisso `\\?\`; un `package-lock.json` vuoto
  in radice = spazzatura da `npm install` accidentale.

## Lezioni del pilota 2026-10-23 (F0+F1)

- F0 in main con thinking off: gpt-oss ha tentato (1) un edit fuori ruolo su SKILL.md (fallito safe
  by design) e (2) la call subagent con schema sbagliato in loop (`action:"guide"` + `ORACLE`).
  Correzione: dare al main la call espatta pronta (agent minuscolo + `task`).
- F0→F1 handoff: il riassunto strutturato va INCLUSO nel `task` dell'oracle, altrimenti F1 parte da zero.

## Variante-2 — CONFERMATA e attiva (26/10)

Test F0 delega-worker: gpt-oss main saltava la delega in 2/2 arm di config (`off`, `auto` — flag di
visualizzazione); qwen3.8 main delega al primo turno (26/10: child Spark 244 s) e il 28/10 anche con
pensiero disattivato. `defaultModel` = qwen3.8 dal 26/10; gpt-oss resta scout-fallback.

## Stato alla chiusura del 28/10

- Tavola di marcia completata (fasi 1-5): commit lerp `2076bb0` · spazzatura rimossa (`nul`,
  `package-lock.json`) · ornith ritirato (catalogo + disco) · riavvio con catalogo Q2 · gate F0
  think-off PASS · load-test Flint-Q2 · A/B Spark vs Flint-Q2 → Spark confermato
- Artefatti A/B: `d59a5178` (Spark, 987,6 s, 30 turni, 20 test verdi) vs `decdf280` (Flint-Q2,
  timeout 1800 s, 10 turni, 0 file); deposito ripristinato tra i bracci, nessun residuo
- Aperti: destino del worktree `config-hardening-20261019-180310` (19/10); impressione utente su
  Flint-Q3_K_XL (provato 27/10) da registrare nella scheda Flint; `plan.md` e
  `doc/plans/2026-10-19-refactor-piano-corretto.md` non tracciati (decidere il destino)

## Aggiornamento 29/10 (mattina)

- Pilota-2 (28/10 pomeriggio, polyline_length): F2 Spark 592,8 s ✓ · F3 frog 81,1 s ✓ · F1 oracle
  **collassato** (3 tentativi, ~75 min: 116 turni senza sintesi + 2 uscite dal ruolo) → colpa del
  pensiero assente (causa radice qui sotto). Piano finale comunque di buona qualità; 2 deviazioni
  lecite del worker (incl. correzione aritmetica del piano: spezzata aperta di 8 punti = 7 segmenti).
  Commit `6dbeba4`; parafrasi del main con 4 numeri su 4 sbagliati (F1 «~30 min»→75+, F2 «~120 s»→
  592,8, F3 «~3 s»→81,1, piano «57 righe»→117).
- **Causa radice** trovata e sistemata: `--reasoning off` di b11895 sopprime la generazione del
  pensiero e prevale sui kwargs; fix `--reasoning on` + `enable_thinking:true` → sonde verdi
  (think server-level, override per-richiesta, tool-calling). Config qwen ora: kwargs
  `enable_thinking:true` + `--reasoning on` (backup: `.bak-qwen-reasoning-off-20261029`).
- Da rifare quando possibile: F1/pilota con la config sistemata per verificare il recupero
  dell'oracle (collasso ~75 min vs attesi ~1-2 min con pensiero).
