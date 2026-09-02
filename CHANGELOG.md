# Changelog

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il
versionamento segue [SemVer](https://semver.org/lang/it/).

## [1.0.1] - 2026-09-02

### Modificato

- L'etichetta predefinita della stagione di raffreddamento passa da
  `Condizionamento` a `Raffrescamento`, termine più corretto per un impianto
  di termoregolazione. Allineate anche le traduzioni italiane, gli esempi del
  README e le tre card in `resources/cards/`.

### Aggiornamento da 1.0.0

Le installazioni esistenti non cambiano comportamento: l'etichetta è
memorizzata nella voce di configurazione e continua a essere quella scelta
al momento dell'installazione. Per adottare il nuovo termine servono due
passaggi, in quest'ordine:

1. cambiare l'opzione in `knx.yaml` e ricaricare l'integrazione KNX;
2. aprire **Configura** sull'integrazione e aggiornare il campo
   "Etichetta opzione Raffrescamento".

L'etichetta deve sempre corrispondere all'opzione dichiarata in `knx.yaml`:
se le due divergono, il comando di commutazione stagione viene scartato e
registrato come warning nel log.

## [1.0.0] - 2026-09-02

Prima release pubblica. Richiede Home Assistant 2024.11 o superiore e
l'integrazione KNX già configurata.

### Aggiunto

- Entità `climate` costruita aggregando le entità KNX generiche di un
  termostato Vimar: un `sensor` per la temperatura, i `select` di modalità,
  stagione e ventola, e i `number` dei tre setpoint.
- Configurazione interamente da interfaccia, con selettori di entità e
  possibilità di modificare tutto in seguito da **Configura**. Obbligatori
  solo il sensore di temperatura, il select modalità e almeno un setpoint.
- Selezione automatica del setpoint attivo: "Temp Auto" in modalità
  Automatico, altrimenti estate o inverno secondo la stagione. Anche `min`,
  `max` e `step` seguono l'entità attiva, quindi lo slider cambia scala
  insieme alla stagione.
- Profili Vimar mappati sui preset standard di Home Assistant
  (`Automatico → home`, `Manuale → comfort`, `A Tempo → boost`), scelta
  modificabile per singolo profilo. La mappatura si disattiva da sola se due
  profili finissero sullo stesso preset.
- Velocità ventola normalizzate su `low` / `medium` / `high`, riconoscendo
  anche le forme abbreviate, italiane e numeriche. Sul bus viene comunque
  scritta l'opzione originale di `knx.yaml`.
- Etichette delle opzioni dei select configurabili, per adattarsi a
  installazioni che usano nomi diversi da quelli predefiniti. Devono
  corrispondere a quelli scritti in `knx.yaml`.
- Attributi `vimar_modalita`, `vimar_stagione` e `setpoint_attivo`, utili per
  automazioni e per le card: `vimar_stagione` resta leggibile anche a
  termostato spento, quando `hvac_mode` vale `off`.
- Ripristino dell'ultimo profilo usato alla riaccensione, dato che il
  termostato non distingue fra "acceso" e profilo di funzionamento.
- Icone e logo del progetto, in variante chiara e scura, distribuiti nella
  cartella `brand/` dell'integrazione. Sorgenti SVG e script di generazione
  in `resources/icons/`.
- Tre configurazioni Lovelace di esempio in `resources/cards/`, per Simple
  Thermostat e per button-card.
- Traduzioni italiana e inglese.
- Diagnostica all'avvio: un warning nel log segnala le entità sorgente
  mancanti o prive di opzioni, che è la causa più frequente di una riga di
  comandi assente sulla card.

### Note

- L'integrazione non parla direttamente con il bus KNX: la connessione resta
  interamente all'integrazione KNX ufficiale. Nessun secondo tunnel verso il
  gateway, nessuna dipendenza da API interne.
- `hvac_action` non è esposto: richiederebbe un indirizzo di gruppo di stato
  del relè o della valvola.

[1.0.1]: https://github.com/tempod/vimar-knx-climate-home-assistant/releases/tag/v1.0.1
[1.0.0]: https://github.com/tempod/vimar-knx-climate-home-assistant/releases/tag/v1.0.0
