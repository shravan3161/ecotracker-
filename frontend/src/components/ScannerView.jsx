import React, { useState } from 'react';

export default function ScannerView({ userId, onRefreshDashboard, onShowToast }) {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const runScan = async () => {
    if (!selectedFile) {
      onShowToast('⚠️ Please select or take a photo of a receipt or utility bill first.');
      return;
    }

    setIsScanning(true);
    try {
      const reader = new FileReader();
      reader.readAsDataURL(selectedFile);
      reader.onload = async () => {
        const base64Data = reader.result.split(',')[1];
        const res = await fetch('/api/scan-receipt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_base64: base64Data,
            mime_type: selectedFile.type || 'image/jpeg',
            user_id: userId
          })
        });
        const data = await res.json();
        setScanResult(data);
        onShowToast('✅ Document analyzed successfully!');
        onRefreshDashboard();
      };
    } catch (err) {
      console.error(err);
      onShowToast('⚠️ Error analyzing document.');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">📸 Receipt & Utility Bill Multimodal Scanner</div>
          <span className="brand-badge">Gemini 2.5 Flash Vision OCR</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Upload or capture a grocery receipt, supermarket docket, or electricity utility bill. EcoTracker's vision
          pipeline extracts line items, computes CO2e emissions, and identifies eco-swap savings.
        </p>

        <div
          style={{
            border: '2px dashed var(--border-subtle)',
            borderRadius: '16px',
            padding: '36px 20px',
            textAlign: 'center',
            background: 'var(--bg-surface-elevated)',
            marginBottom: '20px'
          }}
        >
          {previewUrl ? (
            <div style={{ marginBottom: '16px' }}>
              <img
                src={previewUrl}
                alt="Document Preview"
                style={{ maxHeight: '200px', borderRadius: '10px', objectFit: 'contain' }}
              />
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                {selectedFile?.name} ({(selectedFile?.size / 1024).toFixed(1)} KB)
              </p>
            </div>
          ) : (
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>📄</div>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
              📂 Choose File
              <input type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFileChange} />
            </label>
            <label className="btn btn-cyan" style={{ cursor: 'pointer' }}>
              📷 Take Photo
              <input
                type="file"
                accept="image/*"
                capture="environment"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
            </label>
            {selectedFile && (
              <button className="btn btn-primary" onClick={runScan} disabled={isScanning}>
                {isScanning ? '⏳ Extracting Line Items...' : '🚀 Analyze Footprint'}
              </button>
            )}
          </div>
        </div>

        {scanResult && (
          <div style={{ marginTop: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: 700 }}>Extraction Results</h3>
              <div style={{ display: 'flex', gap: '12px' }}>
                <span className="status-badge" style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171' }}>
                  Total: {scanResult.total_co2e_kg} kg CO2e
                </span>
                <span className="status-badge" style={{ background: 'rgba(16,185,129,0.15)', color: '#34d399' }}>
                  Potential Savings: {scanResult.total_saved_co2e_kg} kg CO2e
                </span>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table className="modern-table">
                <thead>
                  <tr>
                    <th>Item / Description</th>
                    <th>Category</th>
                    <th>Emissions</th>
                    <th>Eco-Swap Alternative</th>
                    <th>Savings</th>
                  </tr>
                </thead>
                <tbody>
                  {scanResult.items?.map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{item.description}</td>
                      <td>
                        <span className="status-badge">{item.category}</span>
                      </td>
                      <td style={{ color: '#f87171', fontWeight: 700 }}>{item.co2e_kg} kg</td>
                      <td style={{ color: '#34d399' }}>{item.recommended_swap || 'N/A'}</td>
                      <td style={{ color: '#34d399', fontWeight: 700 }}>
                        {item.saved_co2e_kg ? `+${item.saved_co2e_kg} kg` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
