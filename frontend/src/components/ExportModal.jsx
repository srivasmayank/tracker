import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import { Download, FileText, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';

export const ExportModal = ({ isOpen, onClose }) => {
  const [format, setFormat] = useState('CSV');
  const [status, setStatus] = useState('idle'); // idle | queued | processing | completed | failed
  const [jobId, setJobId] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [recordCount, setRecordCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  if (!isOpen) return null;

  const handleStartExport = async () => {
    setStatus('queued');
    setErrorMsg('');
    try {
      // 1. Send asynchronous export request -> Expect 202 Accepted
      const res = await apiClient.post('/exports', { format });
      const job = res.data;
      setJobId(job.job_id);
      setStatus(job.status.toLowerCase());

      // 2. Poll job status
      pollIntervalRef.current = setInterval(async () => {
        try {
          const pollRes = await apiClient.get(`/exports/${job.job_id}`);
          const currentJob = pollRes.data;
          setStatus(currentJob.status.toLowerCase());

          if (currentJob.status === 'COMPLETED') {
            clearInterval(pollIntervalRef.current);
            setRecordCount(currentJob.total_records);
            setDownloadUrl(currentJob.download_url);
          } else if (currentJob.status === 'FAILED') {
            clearInterval(pollIntervalRef.current);
            setErrorMsg(currentJob.error_message || 'Background worker encountered an error.');
          }
        } catch (pollErr) {
          clearInterval(pollIntervalRef.current);
          setStatus('failed');
          setErrorMsg('Failed while checking export status.');
        }
      }, 1000);
    } catch (err) {
      setStatus('failed');
      setErrorMsg(err.response?.data?.detail || 'Failed to submit export job.');
    }
  };

  const handleDownload = async () => {
    if (!jobId) return;
    try {
      const response = await apiClient.get(`/exports/${jobId}/download`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], {
        type: format === 'CSV' ? 'text/csv' : 'application/json',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `expenses_export_${jobId}.${format.toLowerCase()}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Failed to download file.');
    }
  };

  const reset = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setStatus('idle');
    setJobId(null);
    setDownloadUrl(null);
    setErrorMsg('');
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem',
      backdropFilter: 'blur(4px)'
    }}>
      <div style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '480px',
        padding: '1.75rem',
        color: '#f8fafc',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              background: '#312e81',
              color: '#818cf8',
              borderRadius: '8px',
              padding: '8px',
              display: 'flex'
            }}>
              <Download size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>Export Statement</h3>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
                Asynchronous background worker generation
              </p>
            </div>
          </div>
          <button
            onClick={reset}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Format Selector */}
        {status === 'idle' && (
          <div>
            <label style={{ fontSize: '0.85rem', color: '#cbd5e1', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
              Choose Export Format
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '1.5rem' }}>
              <button
                type="button"
                onClick={() => setFormat('CSV')}
                style={{
                  background: format === 'CSV' ? '#4f46e5' : '#0f172a',
                  border: format === 'CSV' ? '2px solid #818cf8' : '1px solid #334155',
                  borderRadius: '10px',
                  padding: '14px',
                  color: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.95rem'
                }}
              >
                <FileText size={22} />
                CSV Spreadsheet
                <span style={{ fontSize: '0.7rem', color: '#c7d2fe', fontWeight: 400 }}>Excel & Google Sheets</span>
              </button>

              <button
                type="button"
                onClick={() => setFormat('JSON')}
                style={{
                  background: format === 'JSON' ? '#4f46e5' : '#0f172a',
                  border: format === 'JSON' ? '2px solid #818cf8' : '1px solid #334155',
                  borderRadius: '10px',
                  padding: '14px',
                  color: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.95rem'
                }}
              >
                <FileText size={22} />
                JSON Payload
                <span style={{ fontSize: '0.7rem', color: '#c7d2fe', fontWeight: 400 }}>Developers & APIs</span>
              </button>
            </div>

            <div style={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '0.8rem',
              color: '#94a3b8',
              marginBottom: '1.5rem',
              lineHeight: 1.5
            }}>
              💡 <strong>Asynchronous Decoupling:</strong> The export request returns a <code>202 Accepted</code> token. Background workers build the dataset out-of-band so your app never freezes.
            </div>

            <button
              onClick={handleStartExport}
              style={{
                width: '100%',
                background: '#6366f1',
                color: '#ffffff',
                border: 'none',
                padding: '12px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.95rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.4)'
              }}
            >
              Start Export Job
            </button>
          </div>
        )}

        {/* Processing State */}
        {(status === 'queued' || status === 'pending' || status === 'processing') && (
          <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
            <Loader2 size={40} color="#818cf8" style={{ animation: 'spin 1s linear infinite', margin: '0 auto 1rem' }} />
            <h4 style={{ margin: '0 0 6px', fontSize: '1.1rem' }}>Generating Statement...</h4>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.85rem' }}>
              Job ID: <code style={{ color: '#38bdf8' }}>{jobId}</code>
            </p>
            <p style={{ margin: '8px 0 0', color: '#64748b', fontSize: '0.75rem' }}>
              Worker status: <strong>{status.toUpperCase()}</strong> (HTTP 202 Polling)
            </p>
          </div>
        )}

        {/* Completed State */}
        {status === 'completed' && (
          <div style={{ textAlign: 'center', padding: '1.5rem 1rem' }}>
            <div style={{
              background: '#064e3b',
              color: '#34d399',
              borderRadius: '50%',
              width: '56px',
              height: '56px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem'
            }}>
              <CheckCircle2 size={32} />
            </div>
            <h4 style={{ margin: '0 0 6px', fontSize: '1.15rem' }}>Statement Ready!</h4>
            <p style={{ margin: '0 0 1.25rem', color: '#94a3b8', fontSize: '0.85rem' }}>
              Successfully exported <strong>{recordCount}</strong> transaction records in {format} format.
            </p>

            <button
              onClick={handleDownload}
              style={{
                width: '100%',
                background: '#10b981',
                color: '#ffffff',
                border: 'none',
                padding: '12px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.95rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                marginBottom: '0.75rem'
              }}
            >
              <Download size={18} />
              Download {format} File
            </button>

            <button
              onClick={reset}
              style={{
                width: '100%',
                background: 'transparent',
                color: '#94a3b8',
                border: '1px solid #334155',
                padding: '10px',
                borderRadius: '8px',
                fontWeight: 500,
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>
        )}

        {/* Failed State */}
        {status === 'failed' && (
          <div style={{ textAlign: 'center', padding: '1.5rem 1rem' }}>
            <div style={{
              background: '#7f1d1d',
              color: '#f87171',
              borderRadius: '50%',
              width: '56px',
              height: '56px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem'
            }}>
              <AlertCircle size={32} />
            </div>
            <h4 style={{ margin: '0 0 6px', fontSize: '1.15rem', color: '#f87171' }}>Export Failed</h4>
            <p style={{ margin: '0 0 1.25rem', color: '#94a3b8', fontSize: '0.85rem' }}>
              {errorMsg}
            </p>

            <button
              onClick={() => setStatus('idle')}
              style={{
                width: '100%',
                background: '#6366f1',
                color: '#ffffff',
                border: 'none',
                padding: '10px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                marginBottom: '0.5rem'
              }}
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
