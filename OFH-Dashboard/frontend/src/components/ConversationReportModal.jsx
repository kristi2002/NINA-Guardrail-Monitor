import React, { useState } from 'react';
import html2pdf from 'html2pdf.js'; // Make sure to install this library
import './ConversationReportModal.css';

const ConversationReportModal = ({ reportData, isOpen, onClose }) => {
  const [exporting, setExporting] = useState(false);

  if (!isOpen || !reportData) return null;

  /**
   * Generates and downloads a PDF report from the reportData.
   * This function builds an HTML string and passes it directly
   * to html2pdf.js for a more reliable export.
   */
  const handleExportPDF = async () => {
    setExporting(true);

    // Create a well-structured HTML string for the PDF content.
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>Report Conversazione</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; color: #333; background: white; }
            .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #1976d2; }
            .title { font-size: 24px; font-weight: bold; color: #1976d2; margin-bottom: 10px; }
            .section { margin-bottom: 25px; page-break-inside: avoid; }
            .section-title { font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }
            .info-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            .info-table td { padding: 12px; border: 1px solid #ddd; }
            .info-table td:first-child { background: #f8f9fa; font-weight: bold; color: #1976d2; width: 30%; }
            .status-badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; background: #ff9800; color: white; }
            .risk-section { background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .events-section { margin-top: 20px; }
            .event-item { border-left: 4px solid #1976d2; padding: 15px; margin-bottom: 15px; background: #f8f9fa; border-radius: 0 6px 6px 0; }
            .event-header { font-weight: bold; color: #1976d2; margin-bottom: 8px; }
            .event-description { margin-bottom: 8px; }
            .event-details { color: #666; font-style: italic; font-size: 12px; }
            .summary-section { background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-top: 30px; }
            .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; }
            .summary-item { background: white; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; }
            .summary-label { font-weight: bold; color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }
            .summary-value { color: #333; font-size: 18px; font-weight: bold; }
            .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="header"><div class="title">REPORT CONVERSAZIONE</div></div>
          <div class="section">
            <div class="section-title">Informazioni Paziente</div>
            <table class="info-table">
              <tr><td>Nome</td><td>${reportData.patientInfo?.name || reportData.patientId || 'N/A'}</td></tr>
              <tr><td>ID Paziente</td><td>${reportData.patientId || 'N/A'}</td></tr>
              <tr><td>Età</td><td>${reportData.patientInfo?.age || 'N/A'} anni</td></tr>
              <tr><td>Sesso</td><td>${reportData.patientInfo?.gender || 'N/A'}</td></tr>
              <tr><td>Patologia</td><td>${reportData.patientInfo?.pathology || 'N/A'}</td></tr>
            </table>
          </div>
          <div class="section">
            <div class="section-title">Dettagli Conversazione</div>
            <table class="info-table">
              <tr><td>Data</td><td>${reportData.conversationDate || 'N/A'}</td></tr>
              <tr><td>Ora</td><td>${reportData.conversationTime || 'N/A'}</td></tr>
              <tr><td>Durata</td><td>${reportData.duration || 'N/A'} minuti</td></tr>
              <tr><td>Stato</td><td><span class="status-badge ${(reportData.status || '').toLowerCase().replace('_', '-')}">${reportData.status || 'N/A'}</span></td></tr>
            </table>
          </div>
          <div class="section">
            <div class="section-title">Valutazione del Rischio</div>
            <div class="risk-section">
              <table class="info-table">
                <tr><td>Livello Rischio</td><td>${reportData.summary?.riskLevel || 'N/A'}</td></tr>
                <tr><td>Situazione</td><td>${reportData.situation || 'N/A'}</td></tr>
              </table>
            </div>
          </div>
          ${reportData.analysis ? `<div class="section">
            <div class="section-title">Analisi Conversazione</div>
            <div style="background: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 20px;">
              <table class="info-table">
                <tr><td>Temi Principali</td><td>${(reportData.analysis.keyTopics || []).join(', ') || 'Nessun tema identificato'}</td></tr>
                <tr><td>Tono Emotivo</td><td>${reportData.analysis.emotionalTone || 'N/A'}</td></tr>
                <tr><td>Fattori di Rischio</td><td>${(reportData.analysis.riskFactors || []).join(', ') || 'Nessun fattore di rischio identificato'}</td></tr>
                <tr><td>Aspetti Positivi</td><td>${(reportData.analysis.positiveAspects || []).join(', ') || 'Nessun aspetto positivo identificato'}</td></tr>
              </table>
            </div>
          </div>` : ''}
          <div class="section">
            <div class="section-title">Cronologia Eventi</div>
            <div class="events-section">${reportData.events && reportData.events.length > 0 ? reportData.events.map(event => `<div class="event-item"><div class="event-header">${event.type} - ${new Date(event.timestamp).toLocaleString('it-IT')}</div><div class="event-description">${event.description || 'Nessuna descrizione'}</div>${event.details ? `<div class="event-details">${event.details}</div>` : ''}</div>`).join('') : '<div class="event-item"><div class="event-description">Nessun evento registrato</div></div>'}</div>
          </div>
          <div class="summary-section">
            <div class="section-title">Riepilogo Eventi</div>
            <div class="summary-grid">
              <div class="summary-item"><div class="summary-label">Eventi Totali</div><div class="summary-value">${reportData.summary?.totalEvents || 0}</div></div>
              <div class="summary-item"><div class="summary-label">Avvisi</div><div class="summary-value">${reportData.summary?.warningEvents || 0}</div></div>
              <div class="summary-item"><div class="summary-label">Allarmi</div><div class="summary-value">${reportData.summary?.alertEvents || 0}</div></div>
            </div>
          </div>
          <div class="footer">Report generato il ${new Date(reportData.generatedAt).toLocaleString('it-IT')}</div>
        </body>
      </html>
    `;

    // Define reliable options for html2pdf
    const options = {
      margin: [0.5, 0.5, 0.5, 0.5], // Margins in inches [top, left, bottom, right]
      filename: `conversation-report-${reportData.id}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 }, // Higher scale for better resolution
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
    };

    try {
      // Use html2pdf directly on the HTML string
      await html2pdf().set(options).from(htmlContent).save();
    } catch (error) {
      console.error('Failed to export PDF:', error);
      alert('Errore nell\'esportazione del PDF. Prova a usare Ctrl+P per stampare manualmente.');
    } finally {
      setExporting(false);
    }
  };

  const getSituationConfig = (situation) => {
    const configs = {
      'Regolare': { label: 'Regolare', class: 'situation-normal', color: '#4caf50' },
      'Segni di autolesionismo': { label: 'Segni di autolesionismo', class: 'situation-warning', color: '#ff9800' },
      'Gesti pericolosi': { label: 'Gesti pericolosi', class: 'situation-danger', color: '#f44336' },
    };
    return configs[situation] || configs['Regolare'];
  };

  const getRiskLevelConfig = (level) => {
    const configs = {
      'low': { label: 'Basso', class: 'risk-low', color: '#4caf50' },
      'medium': { label: 'Medio', class: 'risk-medium', color: '#ff9800' },
      'high': { label: 'Alto', class: 'risk-high', color: '#f44336' },
    };
    return configs[level] || configs['medium'];
  };

  const formatDateTime = (dateString) => {
    // Handle null, undefined, or invalid date strings
    if (!dateString) {
      return 'N/A';
    }

    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Data non valida';
    }

    return date.toLocaleString('it-IT', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="conversation-report-modal-overlay">
      <div className="conversation-report-modal">
        <div className="modal-header">
          <h2>Report Conversazione</h2>
          <div className="header-actions">
            <button
              className="btn-export-pdf"
              onClick={handleExportPDF}
              disabled={exporting}
            >
              <span className="btn-icon">📄</span>
              {exporting ? 'Generazione...' : 'Esporta PDF'}
            </button>
            <button
              className="btn-export-json"
              onClick={() => {
                const dataStr = JSON.stringify(reportData, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `conversation-report-${reportData.id}.json`;
                link.click();
                URL.revokeObjectURL(url);
              }}
            >
              <span className="btn-icon">📋</span>
              Esporta JSON
            </button>
            <button className="modal-close" onClick={onClose}>
              <span>×</span>
            </button>
          </div>
        </div>

        <div className="report-content">
          {/* Patient Information Section */}
          <div className="report-section">
            <h3 className="report-section-title">Informazioni Paziente</h3>
            <div className="patient-info-grid">
              <div className="info-item">
                <span className="info-label">Paziente</span>
                <span className="info-value">{reportData.patientInfo?.name || `Paziente ${reportData.patientId}`}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Età</span>
                <span className="info-value">{reportData.patientInfo?.age} anni</span>
              </div>
              <div className="info-item">
                <span className="info-label">Sesso</span>
                <span className="info-value">{reportData.patientInfo?.gender}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Patologia</span>
                <span className="info-value">{reportData.patientInfo?.pathology}</span>
              </div>
            </div>
          </div>

          {/* Conversation Details Section */}
          <div className="report-section">
            <h3 className="report-section-title">Dettagli Conversazione</h3>
            <div className="conversation-details-grid">
              <div className="detail-item">
                <span className="detail-label">Data</span>
                <span className="detail-value">{reportData.conversationDate}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Ora</span>
                <span className="detail-value">{reportData.conversationTime}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Durata</span>
                <span className="detail-value">{reportData.duration} minuti</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Stato</span>
                <span className={`status-badge ${(reportData.status || '').toLowerCase().replace('_', '-')}`}>
                  {reportData.status}
                </span>
              </div>
            </div>
          </div>

          <hr className="separator" />

          {/* Risk Assessment Section */}
          <div className="report-section">
            <h3 className="report-section-title">Valutazione del Rischio</h3>
            <div className="risk-assessment">
              <div className="risk-level">
                <span className="risk-label">Livello Rischio:</span>
                <span className={`risk-badge ${getRiskLevelConfig(reportData.summary?.riskLevel).class}`}>
                  {getRiskLevelConfig(reportData.summary?.riskLevel).label}
                </span>
              </div>
              <div className="situation-level">
                <span className="situation-label">Situazione:</span>
                <span className={`situation-badge ${getSituationConfig(reportData.situation).class}`}>
                  {getSituationConfig(reportData.situation).label}
                </span>
              </div>
            </div>
          </div>

          {/* Analysis Section */}
          {reportData.analysis && (
            <div className="report-section">
              <h3 className="report-section-title">Analisi Conversazione</h3>
              <div className="analysis-grid">
                <div className="analysis-item">
                  <h4 className="analysis-title">Temi Principali</h4>
                  <p className="analysis-content">
                    {(reportData.analysis.keyTopics || []).join(', ') || 'Nessun tema identificato'}
                  </p>
                </div>
                <div className="analysis-item">
                  <h4 className="analysis-title">Tono Emotivo</h4>
                  <p className="analysis-content">{reportData.analysis.emotionalTone || 'N/A'}</p>
                </div>
                <div className="analysis-item">
                  <h4 className="analysis-title">Fattori di Rischio</h4>
                  <p className="analysis-content">
                    {(reportData.analysis.riskFactors || []).join(', ') || 'Nessun fattore di rischio identificato'}
                  </p>
                </div>
                <div className="analysis-item">
                  <h4 className="analysis-title">Aspetti Positivi</h4>
                  <p className="analysis-content">
                    {(reportData.analysis.positiveAspects || []).join(', ') || 'Nessun aspetto positivo identificato'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Events Timeline Section */}
          <div className="report-section">
            <h3 className="report-section-title">Cronologia Eventi</h3>
            <div className="events-timeline">
              {reportData.events && reportData.events.length > 0 ? (
                reportData.events.map((event, index) => (
                  <div key={index} className="timeline-item">
                    <div className="event-header">
                      <span className="event-type">{event.type}</span>
                      <span className="event-timestamp">{formatDateTime(event.timestamp)}</span>
                    </div>
                    <div className="event-description">
                      {event.description || 'Nessuna descrizione'}
                    </div>
                    {event.details && (
                      <div className="event-details">
                        {event.details}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="timeline-item">
                  <div className="event-description">Nessun evento registrato</div>
                </div>
              )}
            </div>
          </div>

          {/* Summary Section */}
          <div className="report-section">
            <h3 className="report-section-title">Riepilogo</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <div className="summary-label">Eventi Totali</div>
                <div className="summary-value">{reportData.summary?.totalEvents || 0}</div>
              </div>
              <div className="summary-item">
                <div className="summary-label">Avvisi</div>
                <div className="summary-value warning">{reportData.summary?.warningEvents || 0}</div>
              </div>
              <div className="summary-item">
                <div className="summary-label">Allarmi</div>
                <div className="summary-value danger">{reportData.summary?.alertEvents || 0}</div>
              </div>
            </div>
          </div>

          {/* Metadata Section */}
          <div className="metadata-section">
            <div className="metadata-grid">
              <div className="metadata-item">
                <span className="metadata-label">ID Conversazione</span>
                <span className="metadata-value">#{reportData.id}</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">Versione Report</span>
                <span className="metadata-value">1.0</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">Generato il</span>
                <span className="metadata-value">{formatDateTime(reportData.generatedAt)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-close" onClick={onClose}>
            Chiudi
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConversationReportModal;