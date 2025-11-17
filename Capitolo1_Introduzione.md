# Capitolo 1: Introduzione

## 1.1 Contesto

La crescente adozione di sistemi di intelligenza artificiale conversazionale in settori critici, come quello sanitario, ha reso essenziale l'implementazione di meccanismi di monitoraggio e validazione in tempo reale per garantire la sicurezza, l'affidabilità e la conformità delle interazioni AI. I tradizionali approcci di validazione post-facto, sebbene utili in molte situazioni, possono rivelarsi limitati quando si tratta di identificare e prevenire violazioni di sicurezza, esposizione di dati sensibili o contenuti inappropriati nel momento stesso in cui vengono generati. Questa limitazione ha alimentato l'interesse verso sistemi di guardrail e monitoraggio in tempo reale, che consentono di osservare, analizzare e validare le conversazioni AI mentre si svolgono, fornendo capacità di intervento immediato con latenza minima.

Il monitoraggio in tempo reale si distingue per la sua capacità di acquisire dati immediatamente, offrire approfondimenti tempestivi e osservare continuamente un sistema o un processo, permettendo la rilevazione immediata di anomalie o deviazioni. Nel contesto delle conversazioni AI, questa metodologia assume un ruolo cruciale: la capacità di analizzare e validare le interazioni AI mentre si svolgono consente di identificare rapidamente problemi quali la divulgazione non autorizzata di informazioni personali identificabili (PII), l'utilizzo di linguaggio tossico o inappropriato, e la violazione di normative di conformità, garantendo al contempo un'esperienza utente fluida e sicura.

In ambito sanitario, dove la protezione dei dati sensibili e la conformità normativa sono di importanza critica, il monitoraggio in tempo reale delle conversazioni AI può assicurare che le informazioni fornite siano accurate, pertinenti e conformi agli standard etici e legali, come il Regolamento Generale sulla Protezione dei Dati (GDPR) e le normative specifiche del settore sanitario. I sistemi di guardrail moderni combinano tecniche di rilevamento stateless, analisi contestuale basata su modelli linguistici avanzati, e meccanismi di apprendimento adattivo che si perfezionano attraverso il feedback degli operatori, creando un ciclo continuo di miglioramento e ottimizzazione.

## 1.2 Motivazioni

Attraverso l'utilizzo di tecnologie moderne come Apache Kafka per la messaggistica asincrona, framework web come Flask e React per la realizzazione di interfacce di monitoraggio, e sistemi di validazione basati su Guardrails-AI, questa ricerca si propone di esplorare le potenzialità di tali strumenti nella gestione avanzata del monitoraggio e della validazione delle conversazioni AI, con particolare attenzione alle applicazioni in contesti sanitari dove la sicurezza e la conformità sono requisiti fondamentali.

## 1.3 Obiettivi

L'obiettivo principale di questa tesi è l'analisi e lo sviluppo di una piattaforma web per il monitoraggio e la validazione in tempo reale di conversazioni AI, con particolare focus sulle applicazioni in contesti sanitari. Andremo dunque a dimostrare come l'uso di sistemi di guardrail distribuiti, architetture basate su microservizi e meccanismi di apprendimento adattivo possa portare a una gestione più efficace delle interazioni AI, a una validazione più accurata e tempestiva, e a una visualizzazione più intuitiva degli eventi critici, facilitando l'interazione degli operatori con il sistema e migliorando l'esperienza complessiva di monitoraggio.

Gli obiettivi specifici del lavoro includono:

- **Progettazione e sviluppo di un sistema di validazione multi-stadio** che combini rilevamento stateless di informazioni personali identificabili (PII), controllo di tossicità del linguaggio, verifica di conformità normativa e analisi contestuale basata su modelli linguistici avanzati.

- **Implementazione di un'architettura distribuita e scalabile** basata su microservizi, utilizzando Apache Kafka per la comunicazione asincrona tra componenti, garantendo resilienza e capacità di gestire carichi di lavoro elevati.

- **Sviluppo di un sistema di monitoraggio in tempo reale** con dashboard web interattiva che consenta agli operatori di visualizzare, analizzare e intervenire sugli eventi di guardrail in modo tempestivo ed efficace.

- **Integrazione di meccanismi di apprendimento adattivo** che permettano al sistema di ottimizzare continuamente le soglie di sensibilità dei guardrail basandosi sul feedback degli operatori, riducendo i falsi positivi e migliorando l'accuratezza complessiva.

- **Implementazione di strategie di resilienza** attraverso circuit breakers e meccanismi di degradazione controllata, garantendo la continuità operativa anche in presenza di guasti parziali o indisponibilità temporanea di servizi esterni.

- **Valutazione delle prestazioni e dell'efficacia** del sistema sviluppato attraverso test funzionali, di integrazione e di carico, dimostrando la capacità del sistema di operare efficacemente in scenari reali.

## 1.4 Struttura della Tesi

La struttura della presente tesi sarà articolata in diversi capitoli, ciascuno dei quali affronterà specifici aspetti correlati al tema trattato. Questa sezione introduttiva, pertanto, ha lo scopo di fornire una panoramica chiara e concisa dei contenuti che verranno esaminati nei successivi capitoli, facilitando così la comprensione del percorso che il lettore intraprenderà nella lettura del lavoro.

Il **Capitolo 2, "Background e Stato dell'Arte"**, si concentrerà sull'analisi dei concetti fondamentali relativi al monitoraggio in tempo reale, ai sistemi di guardrail per AI, e alle tecnologie di messaggistica asincrona, fornendo una solida base di conoscenze per comprendere i temi successivi trattati. Verranno inoltre esaminati i requisiti normativi e di conformità specifici per le applicazioni AI in contesti sanitari.

Il **Capitolo 3, "Analisi dei Requisiti"**, approfondirà gli aspetti legati all'analisi dei requisiti funzionali e non funzionali della piattaforma, con particolare attenzione agli aspetti di sicurezza, conformità normativa, scalabilità e resilienza. Verranno definiti i casi d'uso principali e gli scenari operativi del sistema.

Il **Capitolo 4, "Progettazione del Sistema"**, descriverà l'architettura complessiva della piattaforma, presentando le scelte progettuali relative all'organizzazione in microservizi, alla comunicazione asincrona tramite Kafka, e all'integrazione tra i vari componenti. Verranno inoltre esaminati i pattern architetturali adottati, come il circuit breaker pattern per la gestione della resilienza.

Il **Capitolo 5, "Tecnologie e Strumenti"**, presenterà le tecnologie utilizzate nel processo di sviluppo, includendo Flask per i servizi backend, React per l'interfaccia utente, Apache Kafka per la messaggistica, PostgreSQL per la persistenza dei dati, e Guardrails-AI per la validazione. Verranno discusse le motivazioni alla base delle scelte tecnologiche.

Il **Capitolo 6, "Implementazione"**, descriverà la realizzazione pratica del progetto, presentando la struttura del codice, le principali componenti implementate, e i dettagli tecnici relativi ai sistemi di validazione, monitoraggio, e apprendimento adattivo. Verranno inoltre illustrate le soluzioni adottate per garantire resilienza e scalabilità.

Il **Capitolo 7, "Valutazione e Test"**, presenterà i test effettuati per valutare le prestazioni, l'affidabilità e la sicurezza della piattaforma, includendo test funzionali, di integrazione, di carico e di resilienza. Verranno discussi i risultati ottenuti e le metriche di performance.

Infine, il **Capitolo 8, "Conclusioni e Sviluppi Futuri"**, sintetizzerà i risultati ottenuti dalla ricerca, discuterà le limitazioni del lavoro svolto e le possibili evoluzioni e direzioni di approfondimento nell'ambito del monitoraggio e della validazione delle conversazioni AI, contribuendo al dibattito sulle migliori pratiche nella sicurezza e conformità delle applicazioni AI.

