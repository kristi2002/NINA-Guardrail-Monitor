// Italian translations for the application
export const it = {
  analytics: {
    title: '📊 Dashboard Analitica',
    subtitle: 'Approfondimenti completi sulle prestazioni di gestione degli allarmi • Ultimo aggiornamento:',
    tabs: {
      overview: { label: 'Panoramica', icon: '📊' },
      notifications: { label: 'Notifiche', icon: '📧' },
      operators: { label: 'Amministratori', icon: '👥' },
      alerts: { label: 'Tendenze Allarmi', icon: '📈' },
      response: { label: 'Tempi di Risposta', icon: '⏱️' },
      escalations: { label: 'Escalation', icon: '⬆️' }
    },
    timeRanges: {
      '1d': 'Ultime 24 Ore',
      '7d': 'Ultimi 7 Giorni',
      '30d': 'Ultimi 30 Giorni'
    },
    buttons: {
      export: '📤 Esporta',
      retry: 'Riprova'
    },
    loading: {
      dashboard: 'Caricamento dashboard analitica...',
      data: 'Caricamento dati {tab}...',
      processing: 'Elaborazione dati {tab}...'
    },
    errors: {
      display: 'Errore nella visualizzazione dei dati {tab}',
      load: 'Errore nel caricamento dei dati {tab}',
      network: 'Errore di rete: Impossibile connettersi al server per i dati {tab}',
      failed: 'Impossibile caricare i dati {tab}: {status} {statusText}'
    },
    overview: {
      metrics: {
        totalAlerts: { title: 'Allarmi Totali', subtitle: 'Elaborati' },
        avgResponseTime: { title: 'Tempo di Risposta Medio', subtitle: 'Obiettivo: < 10m' },
        resolutionRate: { title: 'Tasso di Risoluzione', subtitle: 'Risolti con successo' },
        notificationSuccess: { title: 'Successo Notifiche', subtitle: 'Tasso di consegna' },
        slaCompliance: { title: 'Conformità SLA', subtitle: 'Entro gli obiettivi' },
        escalationRate: { title: 'Tasso di Escalation', subtitle: 'Escalation automatiche' }
      },
      charts: {
        alertProcessing: 'Elaborazione Allarmi nel Tempo',
        performanceSummary: 'Riepilogo Prestazioni',
        systemUptime: 'Tempo di Attività del Sistema',
        operatorUtilization: 'Utilizzo Amministratori',
        peakResponseTime: 'Tempo di Risposta di Picco'
      },
      legend: {
        criticalAlerts: 'Allarmi Critici',
        piiAlerts: 'Allarmi PII',
        otherAlerts: 'Altri Allarmi'
      }
    },
    notifications: {
      metrics: {
        deliveryRate: { title: 'Tasso di Consegna', subtitle: 'Successo complessivo' },
        totalSent: { title: 'Totale Inviati', subtitle: 'Tutti i canali' },
        emailRate: { title: 'Tasso Email', subtitle: 'Consegna email' },
        smsRate: { title: 'Tasso SMS', subtitle: 'Consegna SMS' }
      },
      charts: {
        performance: 'Prestazioni Notifiche nel Tempo',
        breakdown: 'Ripartizione Metodi di Consegna',
        emailsSent: 'Email Inviate',
        emailsDelivered: 'Email Consegnate',
        smsSent: 'SMS Inviato'
      },
      analysis: {
        title: '🔍 Analisi Errori di Consegna',
        failures: 'errori'
      },
      noData: 'Nessun dato notifiche disponibile. Prova ad aggiornare.'
    },
    operators: {
      summary: {
        title: '👥 Riepilogo Prestazioni Amministratori',
        activeOperators: 'Amministratori Attivi',
        totalAlertsHandled: 'Allarmi Totali Gestiti',
        teamAvgResponse: 'Risposta Media Team',
        topPerformer: 'Miglior Performer'
      },
      leaderboard: {
        title: '🏆 Classifica Prestazioni Amministratori',
        alerts: 'Allarmi:',
        response: 'Risposta:',
        resolution: 'Risoluzione:'
      },
      charts: {
        workload: 'Distribuzione Carico di Lavoro',
        trends: 'Tendenze Prestazioni',
        avgResponseTime: 'Tempo di Risposta Medio (s)',
        resolutionRate: 'Tasso di Risoluzione %'
      },
      noData: 'Nessun dato amministratori disponibile'
    },
    alerts: {
      metrics: {
        total: { title: 'Allarmi Totali', subtitle: 'Questo periodo' },
        critical: { title: 'Allarmi Critici', subtitle: 'Alta priorità' },
        active: { title: 'Allarmi Attivi', subtitle: 'Attualmente aperti' },
        mostCommon: { title: 'Tipo Più Comune', subtitle: 'Tipo di evento' }
      },
      charts: {
        trends: 'Tendenze Allarmi nel Tempo',
        distribution: 'Distribuzione Tipo Allarme',
        avgResolution: 'Risoluzione Media (min)',
        alertCount: 'Conteggio Allarmi'
      },
      severity: {
        title: 'Distribuzione Gravità'
      },
      noData: 'Nessun dato tendenze allarmi disponibile. Prova ad aggiornare.'
    },
    responseTimes: {
      metrics: {
        overallAvg: { title: 'Media Complessiva', subtitle: 'Tempo di risposta' },
        avgResolution: { title: 'Risoluzione Media', subtitle: 'Tempo di risoluzione' },
        fastest: { title: 'Risposta Più Rapida', subtitle: 'Miglior tempo' },
        improvement: { title: 'Miglioramento', subtitle: 'vs periodo precedente' }
      },
      sla: {
        title: '🎯 Tempo di Risposta per Gravità',
        avg: 'Media:',
        noData: 'Nessun dato tempo di risposta disponibile'
      },
      charts: {
        overTime: 'Tempi di Risposta nel Tempo',
        distribution: 'Distribuzione Tempi di Risposta',
        avgResolution: 'Risoluzione Media (min)',
        alertCount: 'Conteggio Allarmi'
      },
      noData: 'Nessun dato tempi di risposta disponibile. Prova ad aggiornare.'
    },
    escalations: {
      metrics: {
        total: { title: 'Escalation Totali', subtitle: 'Questo periodo' },
        auto: { title: 'Escalation Automatica', subtitle: 'Automatizzate' },
        rate: { title: 'Tasso di Escalation', subtitle: 'Su tutti gli allarmi' },
        avgTime: { title: 'Tempo Medio', subtitle: 'Per escalation' }
      },
      reasons: {
        title: '📋 Motivi di Escalation'
      },
      charts: {
        trends: 'Tendenze Escalation',
        supervisor: 'Prestazioni Risposta Supervisore',
        total: 'Escalation Totali',
        auto: 'Escalation Automatiche',
        manual: 'Escalation Manuali'
      },
      supervisor: {
        avgResponseTime: 'Tempo di Risposta Medio',
        resolutionRate: 'Tasso di Risoluzione',
        fastestEscalation: 'Escalation Più Rapida'
      },
      noData: 'Elaborazione dati escalation...'
    },
    export: {
      success: 'Dati analitici esportati con successo!',
      failed: 'Esportazione dati fallita'
    }
  }
}

// Helper function to get nested translation with fallback
export const t = (path, params = {}) => {
  const keys = path.split('.')
  let value = it
  
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key]
    } else {
      return path // Return path as fallback
    }
  }
  
  // Replace parameters in the string
  if (typeof value === 'string' && params) {
    return Object.entries(params).reduce((str, [key, val]) => {
      return str.replace(new RegExp(`\\{${key}\\}`, 'g'), val)
    }, value)
  }
  
  return value || path
}

