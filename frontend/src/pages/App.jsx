import React, { useState } from 'react';
import {
  uploadFile,
  getProfile,
  runDetection,
  getExplanations,
  getCleaningOperations,
  previewCleaningOperation,
  editSandboxOperation,
  aiSuggestRemediation,
  approveCleaningOperations,
  applyAllLowRisk,
  undoCleaningOperation,
  adaptiveLearn,
  getReportUrl,
  getExportCsvUrl
} from '../services/api';

export default function App() {
  const [step, setStep] = useState(1);
  const [session, setSession] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [primaryKey, setPrimaryKey] = useState('');
  const [entityKey, setEntityKey] = useState('');
  const [findings, setFindings] = useState([]);
  const [scoreBefore, setScoreBefore] = useState(null);
  const [scoreAfter, setScoreAfter] = useState(null);
  const [explanations, setExplanations] = useState({});
  const [cleaningOps, setCleaningOps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [synthesizedRules, setSynthesizedRules] = useState([]);
  const [learningLoading, setLearningLoading] = useState(false);
  const [learningMessage, setLearningMessage] = useState(null);
  const [previewDiffs, setPreviewDiffs] = useState({});
  const [previewLoading, setPreviewLoading] = useState({});
  const [copiedCodeOpId, setCopiedCodeOpId] = useState(null);
  const [aiLoading, setAiLoading] = useState({});
  const [aiRationales, setAiRationales] = useState({});
  const [editedFlags, setEditedFlags] = useState({});

  // 1. Upload User File
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    await processFile(file);
  };

  // 1b. Load Sample E-Commerce Dataset (1-Click Demo)
  const handleLoadSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/sample_orders.csv');
      if (!response.ok) {
        throw new Error('Failed to load sample dataset from server.');
      }
      const blob = await response.blob();
      const file = new File([blob], 'online_store_orders_sample.csv', { type: 'text/csv' });
      await processFile(file);
    } catch (err) {
      setError(err.message || 'Error loading sample dataset.');
      setLoading(false);
    }
  };

  const processFile = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const uploadRes = await uploadFile(file);
      setSession(uploadRes);
      const profRes = await getProfile(uploadRes.session_id);
      const profList = profRes.profiles || [];
      setProfiles(profList);

      // Heuristic initial candidate selection
      const pkCand = profList.find(p => /order|txn|trans|id$/i.test(p.column_name) || p.column_name.toLowerCase().endsWith('_id'));
      const ekCand = profList.find(p => p !== pkCand && /customer|user|email|phone|client/i.test(p.column_name));
      if (pkCand) setPrimaryKey(pkCand.column_name);
      if (ekCand) setEntityKey(ekCand.column_name);

      setStep(2);
      // Smooth scroll to demo section
      const demoEl = document.getElementById('demo');
      if (demoEl) demoEl.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 2. Run Detect with Relational Deduplication
  const handleDetect = async () => {
    setLoading(true);
    setError(null);
    try {
      const detRes = await runDetection(session.session_id, {
        primary_key: primaryKey || undefined,
        entity_key: entityKey || undefined,
        arithmetic_tolerance: 0.01
      });
      setFindings(detRes.findings || []);
      setScoreBefore(detRes.quality_score);
      setStep(3);

      // Async fetch explanations with MCP blueprints & polyglot regex
      getExplanations(session.session_id).then(expRes => {
        setExplanations(expRes.explanations || {});
      });

      // Async fetch proposed cleaning operations
      getCleaningOperations(session.session_id).then(clRes => {
        setCleaningOps(clRes.operations || []);
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Approve Single Cleaning Operation
  const handleApproveOp = async (opId) => {
    setLoading(true);
    try {
      const res = await approveCleaningOperations(session.session_id, [opId]);
      setScoreAfter(res.quality_score_after);
      setCleaningOps(prev => prev.map(o => o.operation_id === opId ? { ...o, approval_status: 'approved' } : o));
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 4. Batch Apply All Low-Risk Operations
  const handleApplyAllLowRisk = async () => {
    setLoading(true);
    try {
      const res = await applyAllLowRisk(session.session_id);
      setScoreAfter(res.quality_score_after);
      const appliedSet = new Set(res.applied_operations || []);
      setCleaningOps(prev => prev.map(o => appliedSet.has(o.operation_id) ? { ...o, approval_status: 'approved' } : o));
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 5. Undo Cleaning Operation
  const handleUndo = async () => {
    setLoading(true);
    try {
      const res = await undoCleaningOperation(session.session_id);
      setScoreAfter(res.quality_score_after);
      setCleaningOps(prev => prev.map(o => o.operation_id === res.undone_operation_id ? { ...o, approval_status: 'pending' } : o));
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 6. Adaptive Rule Discovery & Synthesis (Principle XIII)
  const handleAdaptiveLearn = async () => {
    if (!session) return;
    setLearningLoading(true);
    setLearningMessage(null);
    try {
      const res = await adaptiveLearn(session.session_id);
      setSynthesizedRules(res.synthesized_rules || []);
      if (res.new_findings && res.new_findings.length > 0) {
        setFindings(prev => [...prev, ...res.new_findings]);
        // Refresh cleaning operations to include newly detected novel anomalies
        const clRes = await getCleaningOperations(session.session_id);
        setCleaningOps(clRes.operations || []);
      }
      setLearningMessage(res.message || `Adaptive scan complete. Synthesized ${res.synthesized_rules?.length || 0} zero-FP rule(s).`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLearningLoading(false);
    }
  };

  // 7. Visual Sandbox Diff Preview Toggle (Principle XII)
  const handleTogglePreview = async (opId) => {
    if (previewDiffs[opId]) {
      setPreviewDiffs(prev => {
        const copy = { ...prev };
        delete copy[opId];
        return copy;
      });
      return;
    }
    setPreviewLoading(prev => ({ ...prev, [opId]: true }));
    try {
      const res = await previewCleaningOperation(session.session_id, opId);
      setPreviewDiffs(prev => ({ ...prev, [opId]: res.diff || [] }));
      if (res.pandas_code) {
        setCleaningOps(prev => prev.map(o => o.operation_id === opId ? { ...o, pandas_code: res.pandas_code } : o));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setPreviewLoading(prev => ({ ...prev, [opId]: false }));
    }
  };

  // 8. Always-Code 1-Click Copy Handler
  const handleCopyCode = (opId, code) => {
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCodeOpId(opId);
      setTimeout(() => setCopiedCodeOpId(null), 2500);
    });
  };

  // 9. In-Sandbox Custom Cell Edit Handler
  const handleCellEdit = async (opId, rowIndex, columnName, newValue) => {
    setPreviewDiffs(prev => {
      const opDiffs = (prev[opId] || []).map(d => {
        if (d.row_index === rowIndex && (d.column_name === columnName || d.column === columnName)) {
          return { ...d, after: newValue };
        }
        return d;
      });
      return { ...prev, [opId]: opDiffs };
    });
    setEditedFlags(prev => ({ ...prev, [`${opId}-${rowIndex}`]: 'user' }));

    try {
      const res = await editSandboxOperation(session.session_id, opId, [{
        row_index: rowIndex,
        column_name: columnName,
        after: newValue
      }]);
      if (res.pandas_code) {
        setCleaningOps(prev => prev.map(o => o.operation_id === opId ? { ...o, pandas_code: res.pandas_code } : o));
      }
    } catch (err) {
      console.error('Failed to sync cell edit:', err);
    }
  };

  // 10. In-Sandbox AI Suggest Remediation Handler (Single Cell)
  const handleAISuggest = async (opId, rowIndex, columnName) => {
    const key = `${opId}-${rowIndex}`;
    setAiLoading(prev => ({ ...prev, [key]: true }));
    try {
      const res = await aiSuggestRemediation(session.session_id, opId, rowIndex, columnName);
      if (res.diff) {
        setPreviewDiffs(prev => ({ ...prev, [opId]: res.diff }));
      }
      if (res.suggestions && res.suggestions.length > 0) {
        setAiRationales(prev => ({ ...prev, [key]: res.suggestions[0].rationale }));
      }
      setEditedFlags(prev => ({ ...prev, [key]: 'ai' }));
      if (res.pandas_code) {
        setCleaningOps(prev => prev.map(o => o.operation_id === opId ? { ...o, pandas_code: res.pandas_code } : o));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setAiLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  // 11. In-Sandbox AI Suggest All Remediation Handler (Whole Operation)
  const handleAISuggestAll = async (opId) => {
    setAiLoading(prev => ({ ...prev, [opId]: true }));
    try {
      const res = await aiSuggestRemediation(session.session_id, opId, null, null);
      if (res.diff) {
        setPreviewDiffs(prev => ({ ...prev, [opId]: res.diff }));
      }
      if (res.suggestions) {
        const newRationales = {};
        const newFlags = {};
        res.suggestions.forEach(s => {
          const k = `${opId}-${s.row_index}`;
          newRationales[k] = s.rationale;
          newFlags[k] = 'ai';
        });
        setAiRationales(prev => ({ ...prev, ...newRationales }));
        setEditedFlags(prev => ({ ...prev, ...newFlags }));
      }
      if (res.pandas_code) {
        setCleaningOps(prev => prev.map(o => o.operation_id === opId ? { ...o, pandas_code: res.pandas_code } : o));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setAiLoading(prev => ({ ...prev, [opId]: false }));
    }
  };

  const scrollToDemo = () => {
    const el = document.getElementById('demo');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  // 9. Operation Card Renderer with Visual Sandbox & Always-Code Transparency
  const renderOperationCard = (op) => {
    const isApproved = op.approval_status === 'approved';
    const isNeedsReview = op.bucket === 'needs_review';
    const diffs = previewDiffs[op.operation_id];
    const isLoadingDiff = previewLoading[op.operation_id];

    return (
      <div
        key={op.operation_id}
        style={{
          background: 'var(--linen)',
          border: '1px solid var(--border-color)',
          padding: 16,
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
          gap: 12
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <strong style={{ color: 'var(--navy)', fontSize: 14 }}>{op.operation_type}</strong>
              <span style={{
                fontSize: 10,
                fontWeight: 800,
                padding: '2px 6px',
                borderRadius: 4,
                background: op.risk_level === 'low' ? '#dcfce7' : op.risk_level === 'medium' ? 'var(--peach)' : '#fee2e2',
                color: op.risk_level === 'low' ? '#15803d' : 'var(--navy)'
              }}>
                {op.risk_level.toUpperCase()} RISK
              </span>
              <span style={{
                fontSize: 10,
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: 4,
                background: isNeedsReview ? '#fef3c7' : '#e0f2fe',
                color: isNeedsReview ? '#92400e' : '#0369a1'
              }}>
                {isNeedsReview ? 'NEEDS REVIEW' : 'AUTO-FIXABLE'}
              </span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--navy-light)', marginTop: 4 }}>
              Columns: <code>{op.affected_columns.join(', ')}</code> • Rows Affected: {op.affected_row_indices.length}
            </div>
            {isNeedsReview && (
              <div style={{ fontSize: 12, color: '#b45309', marginTop: 2 }}>
                ⚠️ Flagged for human review. Cell values preserved without destructive truncation.
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {!isApproved ? (
              <button
                onClick={() => handleApproveOp(op.operation_id)}
                style={{
                  background: '#16a34a',
                  color: 'var(--white)',
                  border: 'none',
                  padding: '8px 18px',
                  borderRadius: 6,
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: 'pointer'
                }}
              >
                {isNeedsReview ? 'Approve & Apply (Remediated)' : 'Approve & Apply'}
              </button>
            ) : (
              <span style={{ color: '#16a34a', fontWeight: 700, fontSize: 13 }}>✓ Applied</span>
            )}
          </div>
        </div>

        {/* Principle XII: Always-Code Reproducible Pandas Snippet */}
        {op.pandas_code && (
          <div style={{
            background: '#1e293b',
            borderRadius: 8,
            padding: '10px 14px',
            border: '1px solid #334155'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#38bdf8', letterSpacing: '0.5px' }}>
                🐼 ALWAYS-CODE TRANSPARENCY (Executable Pandas Snippet)
              </span>
              <button
                onClick={() => handleCopyCode(op.operation_id, op.pandas_code)}
                style={{
                  background: copiedCodeOpId === op.operation_id ? '#16a34a' : '#334155',
                  color: '#ffffff',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                {copiedCodeOpId === op.operation_id ? '✓ Copied!' : '📋 Copy Code'}
              </button>
            </div>
            <pre style={{
              margin: 0,
              fontFamily: 'Consolas, Monaco, "Courier New", monospace',
              fontSize: 12,
              color: '#f8fafc',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.45,
              maxHeight: 160,
              overflowY: 'auto'
            }}>
              {op.pandas_code}
            </pre>
          </div>
        )}

        {/* Visual Sandbox Diff Toggle & AI Remediate All */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleTogglePreview(op.operation_id)}
            style={{
              background: 'var(--white)',
              border: '1px solid var(--peach)',
              color: 'var(--navy)',
              padding: '6px 14px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            <span>{diffs ? '▲ Hide Sandbox Diff' : '🔍 Inspect & Edit in Visual Sandbox'}</span>
            {isLoadingDiff && <span>⏳</span>}
          </button>

          {diffs && diffs.length > 0 && (
            <button
              onClick={() => handleAISuggestAll(op.operation_id)}
              disabled={aiLoading[op.operation_id]}
              style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                color: 'var(--white)',
                border: 'none',
                padding: '6px 14px',
                borderRadius: 6,
                fontSize: 12,
                fontWeight: 700,
                cursor: aiLoading[op.operation_id] ? 'not-allowed' : 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                boxShadow: '0 2px 6px rgba(99, 102, 241, 0.3)'
              }}
            >
              <span>{aiLoading[op.operation_id] ? '⏳ AI Reasoning...' : '🤖 AI Remediate All Cells'}</span>
            </button>
          )}
        </div>

        {/* Visual Sandbox Side-by-Side Diff & Interactive Remediation Table */}
        {diffs && (
          <div style={{
            background: 'var(--white)',
            border: '1px solid var(--border-color)',
            borderRadius: 8,
            padding: 14,
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--navy)', marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>🧪 Visual Sandbox Side-by-Side Cell Remediation Preview</span>
                <span style={{ fontSize: 10, background: '#ede9fe', padding: '2px 6px', borderRadius: 4, color: '#6d28d9', border: '1px solid #d8b4fe', fontWeight: 800 }}>
                  Interactive AI & User Editing
                </span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--navy-light)' }}>
                Directly edit cleaned values or click <strong>✨ AI Fill Value</strong> to infer contextually.
              </div>
            </div>
            {diffs.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--navy-light)', fontStyle: 'italic', padding: 6 }}>
                No cells found for this operation.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ background: 'var(--linen)', borderBottom: '2px solid var(--border-color)' }}>
                      <th style={{ padding: '8px 10px', color: 'var(--navy)' }}>Row Index</th>
                      <th style={{ padding: '8px 10px', color: 'var(--navy)' }}>Column</th>
                      <th style={{ padding: '8px 10px', color: '#991b1b' }}>Original (Before)</th>
                      <th style={{ padding: '8px 10px', color: '#15803d' }}>Cleaned Value (Editable)</th>
                      <th style={{ padding: '8px 10px', color: '#6d28d9' }}>AI Agent Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diffs.map((d, dIdx) => {
                      const colName = d.column_name || d.column;
                      const rowIdx = d.row_index;
                      const cellKey = `${op.operation_id}-${rowIdx}`;
                      const editType = editedFlags[cellKey];
                      const rationale = aiRationales[cellKey];
                      const isRowAiLoading = aiLoading[cellKey];
                      const beforeDisplay = (d.before !== null && d.before !== undefined && d.before !== '' && d.before !== 'nan' && d.before !== 'None')
                        ? String(d.before)
                        : '(empty / null)';

                      return (
                        <tr key={dIdx} style={{ borderBottom: '1px solid var(--border-color)', verticalAlign: 'top' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600 }}>#{rowIdx}</td>
                          <td style={{ padding: '8px 10px' }}><code>{colName}</code></td>
                          <td style={{
                            padding: '8px 10px',
                            background: '#fee2e2',
                            color: '#991b1b',
                            textDecoration: d.after === '[DROPPED]' ? 'line-through' : 'none',
                            fontWeight: 600,
                            fontSize: 12
                          }}>
                            {beforeDisplay}
                          </td>
                          <td style={{ padding: '8px 10px', background: editType === 'ai' ? '#f5f3ff' : '#f0fdf4' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <input
                                  type="text"
                                  value={d.after !== null && d.after !== undefined ? d.after : ''}
                                  placeholder="Type remediated value..."
                                  onChange={(e) => handleCellEdit(op.operation_id, rowIdx, colName, e.target.value)}
                                  style={{
                                    padding: '6px 10px',
                                    borderRadius: 6,
                                    border: editType === 'ai' ? '2px solid #8b5cf6' : editType === 'user' ? '2px solid #3b82f6' : '1px solid #10b981',
                                    background: '#ffffff',
                                    color: 'var(--navy)',
                                    fontWeight: 700,
                                    fontSize: 12,
                                    minWidth: '180px'
                                  }}
                                />
                                {editType === 'ai' && (
                                  <span style={{ fontSize: 10, background: '#ede9fe', color: '#6d28d9', padding: '2px 6px', borderRadius: 4, fontWeight: 800 }}>
                                    ✨ AI
                                  </span>
                                )}
                                {editType === 'user' && (
                                  <span style={{ fontSize: 10, background: '#dbeafe', color: '#1d4ed8', padding: '2px 6px', borderRadius: 4, fontWeight: 800 }}>
                                    ✏️ User
                                  </span>
                                )}
                              </div>
                              {rationale && (
                                <div style={{ fontSize: 10, color: '#6d28d9', fontStyle: 'italic', maxWidth: 280, lineHeight: 1.3 }}>
                                  🤖 {rationale}
                                </div>
                              )}
                            </div>
                          </td>
                          <td style={{ padding: '8px 10px' }}>
                            <button
                              onClick={() => handleAISuggest(op.operation_id, rowIdx, colName)}
                              disabled={isRowAiLoading}
                              style={{
                                background: '#f3e8ff',
                                border: '1px solid #d8b4fe',
                                color: '#6b21a8',
                                padding: '5px 12px',
                                borderRadius: 6,
                                fontSize: 11,
                                fontWeight: 700,
                                cursor: isRowAiLoading ? 'not-allowed' : 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4
                              }}
                            >
                              <span>{isRowAiLoading ? '⏳ Thinking...' : '✨ AI Fill Value'}</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--linen)' }}>
      {/* 1. STICKY NAVBAR */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backdropFilter: 'blur(16px)',
        backgroundColor: 'rgba(248, 244, 233, 0.92)',
        borderBottom: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          {/* Logo Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              background: 'linear-gradient(135deg, var(--navy) 0%, var(--terracotta) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--white)',
              fontWeight: 800,
              fontSize: 20,
              boxShadow: '0 4px 12px rgba(66, 75, 101, 0.25)'
            }}>
              D
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--navy)', letterSpacing: '-0.5px' }}>
                  Datara <span style={{ color: 'var(--terracotta)' }}>AI</span>
                </span>
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 20,
                  background: 'var(--blush)',
                  color: 'var(--navy)',
                  border: '1px solid var(--peach)'
                }}>
                  v1.3 ENTERPRISE
                </span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--navy-light)', fontWeight: 500 }}>
                Data Quality & Adaptive Remediation Agent
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
            <a href="#features" style={{ textDecoration: 'none', color: 'var(--navy)', fontWeight: 600, fontSize: 14 }}>
              Features
            </a>
            <a href="#use-cases" style={{ textDecoration: 'none', color: 'var(--navy)', fontWeight: 600, fontSize: 14 }}>
              Use Cases
            </a>
            <a href="#architecture" style={{ textDecoration: 'none', color: 'var(--navy)', fontWeight: 600, fontSize: 14 }}>
              Architecture
            </a>
            <a href="#team" style={{ textDecoration: 'none', color: 'var(--navy)', fontWeight: 600, fontSize: 14 }}>
              Team
            </a>
            <button
              onClick={scrollToDemo}
              style={{
                backgroundColor: 'var(--terracotta)',
                color: 'var(--white)',
                border: 'none',
                padding: '9px 20px',
                borderRadius: 8,
                fontWeight: 700,
                fontSize: 13,
                boxShadow: '0 4px 14px rgba(249, 174, 108, 0.4)'
              }}
            >
              Launch Live Demo ⚡
            </button>
          </nav>
        </div>
      </header>

      {/* 2. HERO SECTION */}
      <section style={{
        padding: '72px 24px 64px',
        maxWidth: 1200,
        margin: '0 auto',
        textAlign: 'center'
      }}>
        {/* Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 16px',
          borderRadius: 30,
          background: 'var(--blush)',
          border: '1px solid var(--peach)',
          color: 'var(--navy)',
          fontSize: 13,
          fontWeight: 600,
          marginBottom: 24
        }}>
          <span style={{ color: 'var(--terracotta)' }}>●</span>
          Deterministic Tier-1 Precision + Cognitive Tier-2 LLM Remediation
        </div>

        {/* Main Title */}
        <h1 style={{
          fontSize: 'clamp(36px, 5vw, 54px)',
          fontWeight: 900,
          color: 'var(--navy)',
          lineHeight: 1.15,
          letterSpacing: '-1.5px',
          maxWidth: 950,
          margin: '0 auto 20px'
        }}>
          Autonomous Data Quality Auditing for <span style={{ color: 'var(--terracotta)' }}>Mission-Critical</span> Pipelines
        </h1>

        {/* Subtitle */}
        <p style={{
          fontSize: 'clamp(16px, 2vw, 19px)',
          color: 'var(--navy-light)',
          maxWidth: 820,
          margin: '0 auto 36px',
          lineHeight: 1.6
        }}>
          Audit 50,000+ records in milliseconds with two-tier deterministic precision, interactive visual sandbox cell editing,
          reproducible Python/pandas code generation, and adaptive self-evolving anomaly detection with zero PII egress.
        </p>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 54 }}>
          <button
            onClick={scrollToDemo}
            className="animate-pulse-glow"
            style={{
              backgroundColor: 'var(--navy)',
              color: 'var(--white)',
              border: 'none',
              padding: '14px 28px',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            Explore Interactive Studio ↓
          </button>
          <button
            onClick={handleLoadSample}
            style={{
              backgroundColor: 'var(--terracotta)',
              color: 'var(--white)',
              border: 'none',
              padding: '14px 28px',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 4px 18px rgba(249, 174, 108, 0.45)'
            }}
          >
            ⚡ 1-Click Sample Audit
          </button>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            style={{
              backgroundColor: 'var(--white)',
              color: 'var(--navy)',
              border: '1px solid var(--peach)',
              padding: '14px 24px',
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center'
            }}
          >
            OpenAPI Specs ↗
          </a>
        </div>

        {/* Metrics Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 16,
          maxWidth: 1100,
          margin: '0 auto'
        }}>
          {[
            { metric: '100%', title: 'Deterministic Tier 1', desc: 'Zero LLM hallucination on mathematical & statistical anomaly checks' },
            { metric: 'Zero', title: 'Raw PII Egress', desc: 'LLM only consumes sanitized statistical schemas; raw rows never leave local node' },
            { metric: '< 30s', title: 'Single-Node Scan', desc: 'Rapid profiling & relational deduplication for up to 50k records' },
            { metric: 'MCP Ready', title: 'Action Blueprints', desc: 'Standardized Model Context Protocol JSON schemas for autonomous remediation' }
          ].map((item, idx) => (
            <div
              key={idx}
              className="feature-card"
              style={{
                backgroundColor: 'var(--white)',
                border: '1px solid var(--peach)',
                borderRadius: 12,
                padding: '24px 20px',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--terracotta)', marginBottom: 4 }}>
                {item.metric}
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--navy)', marginBottom: 6 }}>
                {item.title}
              </div>
              <div style={{ fontSize: 13, color: 'var(--navy-light)', lineHeight: 1.5 }}>
                {item.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. INTERACTIVE LIVE DEMO SECTION */}
      <section id="demo" style={{
        padding: '72px 24px',
        backgroundColor: 'var(--blush)',
        borderTop: '1px solid var(--peach)',
        borderBottom: '1px solid var(--peach)'
      }}>
        <div style={{ maxWidth: 1150, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <span style={{
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: '1px',
              color: 'var(--terracotta-dark)',
              textTransform: 'uppercase'
            }}>
              Live Interactive Workspace
            </span>
            <h2 style={{ fontSize: 32, fontWeight: 800, color: 'var(--navy)', margin: '8px 0 12px' }}>
              Experience the 5-Step Quality Remediation Studio
            </h2>
            <p style={{ color: 'var(--navy-light)', fontSize: 16, maxWidth: 680, margin: '0 auto' }}>
              Upload your raw CSV or load our curated e-commerce dataset containing realistic multi-date orders,
              impossible values, relational duplicate conflicts, and formatting anomalies.
            </p>
          </div>

          {/* Demo Shell Container */}
          <div style={{
            backgroundColor: 'var(--white)',
            border: '2px solid var(--peach)',
            borderRadius: 16,
            padding: 32,
            boxShadow: 'var(--shadow-lg)'
          }}>
            {/* Step navigation bar */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 28, flexWrap: 'wrap' }}>
              {['Upload & Ingestion', 'Profile & Relational Keys', 'Issues & MCP Blueprints', 'Cleaning Studio', 'Report & Export'].map((name, idx) => (
                <div
                  key={name}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 20,
                    fontSize: 13,
                    fontWeight: 700,
                    backgroundColor: step === idx + 1 ? 'var(--navy)' : 'var(--linen)',
                    color: step === idx + 1 ? 'var(--white)' : 'var(--navy)',
                    border: step === idx + 1 ? '1px solid var(--navy)' : '1px solid var(--border-color)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {idx + 1}. {name}
                </div>
              ))}
            </div>

            {error && (
              <div style={{
                background: '#fee2e2',
                color: '#991b1b',
                padding: '12px 16px',
                borderRadius: 8,
                marginBottom: 20,
                border: '1px solid #fecaca',
                fontWeight: 500
              }}>
                <strong>Error:</strong> {error}
              </div>
            )}

            {loading && (
              <div style={{
                padding: 32,
                textAlign: 'center',
                color: 'var(--terracotta-dark)',
                fontWeight: 700,
                fontSize: 16
              }}>
                <div className="animate-float" style={{ fontSize: 32, marginBottom: 8 }}>⚡</div>
                Processing Deterministic Operations & Cognitive Blueprints...
              </div>
            )}

            {/* STEP 1: Upload / Load Sample */}
            {step === 1 && (
              <div style={{
                border: '2px dashed var(--peach)',
                backgroundColor: 'var(--linen)',
                borderRadius: 12,
                padding: '48px 24px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: 42, marginBottom: 12 }}>📁</div>
                <h3 style={{ fontSize: 22, fontWeight: 800, color: 'var(--navy)', margin: '0 0 8px 0' }}>
                  Upload Dataset for Quality Auditing
                </h3>
                <p style={{ color: 'var(--navy-light)', maxWidth: 500, margin: '0 auto 20px', fontSize: 14 }}>
                  Drag & drop your CSV file (up to 50,000 rows) or launch our preloaded e-commerce benchmark dataset.
                </p>

                <div style={{ display: 'flex', justifyContent: 'center', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
                  <label style={{
                    backgroundColor: 'var(--navy)',
                    color: 'var(--white)',
                    padding: '10px 22px',
                    borderRadius: 8,
                    fontWeight: 700,
                    fontSize: 14,
                    cursor: 'pointer'
                  }}>
                    Browse CSV File
                    <input type="file" accept=".csv" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>
                  <span style={{ color: 'var(--navy-light)', fontWeight: 600 }}>or</span>
                  <button
                    onClick={handleLoadSample}
                    style={{
                      backgroundColor: 'var(--terracotta)',
                      color: 'var(--white)',
                      border: 'none',
                      padding: '10px 22px',
                      borderRadius: 8,
                      fontWeight: 700,
                      fontSize: 14,
                      boxShadow: '0 4px 12px rgba(249, 174, 108, 0.4)'
                    }}
                  >
                    ⚡ Load Sample Orders Dataset
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: Profile & Relational Keys */}
            {step === 2 && session && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 22, color: 'var(--navy)' }}>Dataset Profile: {session.filename}</h3>
                    <div style={{ fontSize: 13, color: 'var(--navy-light)', marginTop: 4 }}>
                      {session.row_count} rows, {session.column_count} columns • Encoding: {session.encoding}
                    </div>
                  </div>
                  <button
                    onClick={handleDetect}
                    style={{
                      background: 'var(--terracotta)',
                      color: 'var(--white)',
                      border: 'none',
                      padding: '11px 24px',
                      borderRadius: 8,
                      fontWeight: 700,
                      fontSize: 14,
                      boxShadow: '0 4px 12px rgba(249, 174, 108, 0.4)'
                    }}
                  >
                    Run Two-Tier Detection →
                  </button>
                </div>

                {/* Relational Deduplication Key Configuration Box */}
                <div style={{
                  background: 'var(--linen)',
                  border: '1px solid var(--peach)',
                  borderRadius: 10,
                  padding: 20,
                  marginBottom: 24,
                  display: 'flex',
                  gap: 24,
                  flexWrap: 'wrap'
                }}>
                  <div style={{ flex: 1, minWidth: 240 }}>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 700, marginBottom: 6, color: 'var(--navy)' }}>
                      🔑 Primary Business Key (e.g., Order ID):
                    </label>
                    <select
                      value={primaryKey}
                      onChange={e => setPrimaryKey(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: 6,
                        border: '1px solid var(--border-color)',
                        background: 'var(--white)',
                        color: 'var(--navy)',
                        fontWeight: 600
                      }}
                    >
                      <option value="">-- Auto-Detect Primary Key --</option>
                      {profiles.map(p => <option key={p.column_name} value={p.column_name}>{p.column_name}</option>)}
                    </select>
                    <div style={{ fontSize: 11, color: 'var(--navy-light)', marginTop: 4 }}>
                      Used to detect duplicate transaction identifiers and conflicting payload states.
                    </div>
                  </div>

                  <div style={{ flex: 1, minWidth: 240 }}>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 700, marginBottom: 6, color: 'var(--navy)' }}>
                      👤 Customer / Entity Key:
                    </label>
                    <select
                      value={entityKey}
                      onChange={e => setEntityKey(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: 6,
                        border: '1px solid var(--border-color)',
                        background: 'var(--white)',
                        color: 'var(--navy)',
                        fontWeight: 600
                      }}
                    >
                      <option value="">-- Auto-Detect Entity Key --</option>
                      {profiles.map(p => <option key={p.column_name} value={p.column_name}>{p.column_name}</option>)}
                    </select>
                    <div style={{ fontSize: 11, color: 'var(--navy-light)', marginTop: 4 }}>
                      Differentiates valid repeat orders across distinct dates from true redundant duplicates.
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
                  {profiles.map(p => (
                    <div key={p.column_name} style={{
                      background: 'var(--white)',
                      border: '1px solid var(--border-color)',
                      padding: 16,
                      borderRadius: 8
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ color: 'var(--navy)', fontSize: 14 }}>{p.column_name}</strong>
                        <span style={{
                          fontSize: 10,
                          background: 'var(--blush)',
                          color: 'var(--navy)',
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontWeight: 700,
                          border: '1px solid var(--peach)'
                        }}>
                          {p.inferred_type.toUpperCase()}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 8, lineHeight: 1.6 }}>
                        <div>Missing: <strong>{p.null_count}</strong> ({p.null_pct}%)</div>
                        <div>Unique: <strong>{p.unique_count}</strong></div>
                        {p.stats && p.stats.min !== undefined && (
                          <div>Range: [{p.stats.min}, {p.stats.max}] | Mean: {p.stats.mean}</div>
                        )}
                        <div style={{ marginTop: 4, wordBreak: 'break-all' }}>
                          Samples: {p.example_values.slice(0, 3).join(', ') || 'N/A'}
                        </div>
                        {/* Mini completeness chart */}
                        <div style={{ marginTop: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--navy-light)', marginBottom: 3 }}>
                            <span>Data Completeness</span>
                            <span style={{ fontWeight: 700 }}>{(100 - p.null_pct).toFixed(1)}%</span>
                          </div>
                          <div style={{ width: '100%', height: 6, background: '#fee2e2', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ width: `${Math.max(0, 100 - p.null_pct)}%`, height: '100%', background: p.null_pct === 0 ? '#10b981' : '#f59e0b', borderRadius: 3 }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* STEP 3: Findings, Score & MCP Blueprints */}
            {step === 3 && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 22, color: 'var(--navy)' }}>
                      Detected Anomaly Findings ({findings.length})
                    </h3>
                    {scoreBefore && (
                      <div style={{ fontSize: 16, marginTop: 4, color: 'var(--navy)' }}>
                        Baseline Quality Score: <strong style={{ color: 'var(--terracotta-dark)', fontSize: 20 }}>{scoreBefore.overall_score} / 100</strong>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setStep(4)}
                    style={{
                      background: 'var(--terracotta)',
                      color: 'var(--white)',
                      border: 'none',
                      padding: '11px 24px',
                      borderRadius: 8,
                      fontWeight: 700,
                      fontSize: 14,
                      boxShadow: '0 4px 12px rgba(249, 174, 108, 0.4)'
                    }}
                  >
                    Proceed to Cleaning Studio →
                  </button>
                </div>

                {/* Calibrated Scoring Weights & Formula Callout */}
                <div style={{
                  background: 'var(--white)',
                  border: '1px solid var(--peach)',
                  borderRadius: 10,
                  padding: 16,
                  marginBottom: 20,
                  boxShadow: 'var(--shadow-sm)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <strong style={{ color: 'var(--navy)', fontSize: 14 }}>📐 Calibrated Scoring Weights Table (Constitution v1.2.0)</strong>
                      <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 2 }}>
                        Overall Score = Average(Column Scores) • Column Score = max(0, 100 − Σ [Affected % × Weight])
                      </div>
                    </div>
                    <span style={{ fontSize: 11, background: '#dcfce7', color: '#15803d', padding: '3px 8px', borderRadius: 4, fontWeight: 700 }}>
                      ✓ Benchmark Verified
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8 }}>
                    {[
                      { name: 'Arithmetic Conflict', weight: '2.0', desc: 'Exact Recalculation' },
                      { name: 'Invalid Value', weight: '1.5', desc: 'Dates, Phone, Range' },
                      { name: 'Missing Value', weight: '1.0', desc: 'Null Preserved' },
                      { name: 'Duplicate (Exact)', weight: '1.0', desc: 'Auto-Droppable' },
                      { name: 'Novel Anomaly', weight: '1.0', desc: 'Self-Synthesized' },
                      { name: 'Inconsistent Text', weight: '0.5', desc: 'Case Normalization' },
                      { name: 'Numeric Outlier', weight: '0.5', desc: 'Flagged for Review' },
                      { name: 'Repeat Customer', weight: '0.0', desc: 'Not an Issue' }
                    ].map(w => (
                      <div key={w.name} style={{ background: 'var(--linen)', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--navy)' }}>{w.name}</div>
                        <div style={{ fontSize: 14, fontWeight: 800, color: w.weight === '0.0' ? '#16a34a' : 'var(--terracotta)' }}>{w.weight} wt</div>
                        <div style={{ fontSize: 10, color: 'var(--navy-light)' }}>{w.desc}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Adaptive Continuous Learning & Novel Pattern Discovery (Principle XIII) */}
                <div style={{
                  background: 'linear-gradient(135deg, rgba(254, 243, 199, 0.45) 0%, rgba(255, 237, 213, 0.45) 100%)',
                  border: '2px solid var(--peach)',
                  borderRadius: 12,
                  padding: 20,
                  marginBottom: 20,
                  boxShadow: 'var(--shadow-sm)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 20 }}>🧠</span>
                        <h4 style={{ margin: 0, fontSize: 16, color: 'var(--navy)', fontWeight: 800 }}>
                          Self-Evolving Adaptive Anomaly Discovery
                        </h4>
                        <span style={{
                          fontSize: 10,
                          background: '#dbeafe',
                          color: '#1e40af',
                          padding: '2px 8px',
                          borderRadius: 12,
                          fontWeight: 800,
                          border: '1px solid #bfdbfe'
                        }}>
                          Principle XIII • Dynamic Rule Engine
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 4, maxWidth: 640 }}>
                        Scans for novel corrupt patterns absent from hardcoded detectors, validates candidate rules against clean rows to guarantee 0 false positives, and permanently synthesizes new detection rules.
                      </div>
                    </div>
                    <button
                      onClick={handleAdaptiveLearn}
                      disabled={learningLoading}
                      style={{
                        background: 'var(--navy)',
                        color: 'var(--white)',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: 8,
                        fontWeight: 700,
                        fontSize: 13,
                        cursor: learningLoading ? 'not-allowed' : 'pointer',
                        boxShadow: '0 4px 12px rgba(66, 75, 101, 0.25)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8
                      }}
                    >
                      <span>{learningLoading ? '⏳ Synthesizing & Verifying Rules...' : '⚡ Discover & Synthesize Novel Rules'}</span>
                    </button>
                  </div>

                  {learningMessage && (
                    <div style={{
                      marginTop: 14,
                      padding: '10px 14px',
                      borderRadius: 6,
                      background: '#dcfce7',
                      border: '1px solid #bbf7d0',
                      color: '#15803d',
                      fontSize: 13,
                      fontWeight: 600
                    }}>
                      {learningMessage}
                    </div>
                  )}

                  {synthesizedRules.length > 0 && (
                    <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--navy)' }}>
                        Synthesized Dynamic Detection Rules ({synthesizedRules.length}):
                      </div>
                      {synthesizedRules.map(rule => (
                        <div
                          key={rule.rule_id}
                          style={{
                            background: 'var(--white)',
                            border: '1px solid var(--border-color)',
                            borderRadius: 8,
                            padding: 12
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <span style={{ fontSize: 12, fontWeight: 800, color: 'var(--navy)' }}>{rule.rule_name}</span>
                              <code style={{ fontSize: 11, background: 'var(--linen)', padding: '2px 6px', borderRadius: 4 }}>
                                {rule.rule_id}
                              </code>
                            </div>
                            <span style={{ fontSize: 11, background: '#dcfce7', color: '#15803d', padding: '2px 8px', borderRadius: 4, fontWeight: 700 }}>
                              ✓ Safety Validated (0 False Positives on Clean Rows)
                            </span>
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 6 }}>
                            Target Columns: <code>{rule.target_columns.join(', ')}</code> • Pattern: <code>{rule.pattern}</code> • Severity: <strong style={{ color: 'var(--terracotta-dark)' }}>{rule.severity}</strong>
                          </div>
                          {rule.remediation_code && (
                            <div style={{ marginTop: 8, background: '#1e293b', borderRadius: 6, padding: '8px 12px' }}>
                              <div style={{ fontSize: 10, color: '#38bdf8', fontWeight: 700, marginBottom: 4 }}>AUTO-GENERATED PANDAS REMEDIATION CODE:</div>
                              <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: 11, color: '#f8fafc' }}>
                                {rule.remediation_code}
                              </pre>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {findings.map(f => {
                    const exp = explanations[f.finding_id];
                    const isNotAnIssue = f.metadata?.status === 'not_an_issue' || f.metadata?.classification === 'repeat_customer';
                    return (
                      <div
                        key={f.finding_id}
                        style={{
                          background: 'var(--white)',
                          border: '1px solid var(--border-color)',
                          borderLeft: isNotAnIssue ? '5px solid #16a34a' : f.severity === 'error' ? '5px solid #ef4444' : '5px solid var(--terracotta)',
                          padding: 18,
                          borderRadius: 8
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                          <div>
                            <span style={{
                              fontSize: 11,
                              padding: '3px 8px',
                              borderRadius: 4,
                              fontWeight: 800,
                              background: isNotAnIssue ? '#dcfce7' : f.severity === 'error' ? '#fee2e2' : 'var(--blush)',
                              color: isNotAnIssue ? '#15803d' : f.severity === 'error' ? '#991b1b' : 'var(--navy)',
                              border: isNotAnIssue ? '1px solid #bbf7d0' : f.severity === 'error' ? '1px solid #fecaca' : '1px solid var(--peach)'
                            }}>
                              {isNotAnIssue ? 'NOT AN ISSUE' : f.severity.toUpperCase()}
                            </span>
                            {f.metadata?.tier && (
                              <span style={{
                                marginLeft: 6,
                                fontSize: 10,
                                fontWeight: 700,
                                padding: '2px 6px',
                                borderRadius: 4,
                                background: f.metadata.tier === 'tier_c' ? '#dcfce7' : f.metadata.tier === 'tier_a' ? '#e0f2fe' : '#fee2e2',
                                color: f.metadata.tier === 'tier_c' ? '#15803d' : f.metadata.tier === 'tier_a' ? '#0369a1' : '#991b1b'
                              }}>
                                {f.metadata.tier.toUpperCase()} {f.metadata.classification ? `(${f.metadata.classification})` : ''}
                              </span>
                            )}
                            <strong style={{ marginLeft: 10, color: 'var(--navy)' }}>{f.issue_family.toUpperCase()}</strong>: <code>{f.affected_columns.join(', ')}</code>
                          </div>
                          <span style={{ fontSize: 12, color: 'var(--navy-light)', fontWeight: 600 }}>
                            {f.affected_row_indices.length} rows impacted
                          </span>
                        </div>

                        {exp ? (
                          <div style={{ marginTop: 12, fontSize: 13, background: 'var(--linen)', padding: 14, borderRadius: 8 }}>
                            <div style={{ color: 'var(--navy)' }}><strong>Executive Synthesis:</strong> {exp.explanation_text}</div>
                            <div style={{ marginTop: 4, color: 'var(--navy)' }}><strong>Business Impact:</strong> {exp.business_impact}</div>
                            <div style={{ marginTop: 4, color: 'var(--navy)' }}><strong>Recommended Fix:</strong> {exp.recommended_action}</div>

                            {/* Polyglot Regex Badge */}
                            {exp.polyglot_regex && (
                              <div style={{
                                marginTop: 10,
                                padding: '8px 12px',
                                background: 'var(--white)',
                                border: '1px solid var(--peach)',
                                borderRadius: 6
                              }}>
                                <span style={{ fontWeight: 700, color: 'var(--terracotta-dark)' }}>
                                  🔤 Polyglot Regex Pattern ({exp.polyglot_regex.domain.toUpperCase()}):
                                </span>{' '}
                                <code style={{ background: 'var(--blush)', padding: '2px 8px', borderRadius: 4, color: 'var(--navy)' }}>
                                  {exp.polyglot_regex.regex_pattern}
                                </code>
                                <div style={{ fontSize: 11, color: 'var(--navy-light)', marginTop: 4 }}>
                                  {exp.polyglot_regex.description} (Target Locales: {exp.polyglot_regex.target_locales.join(', ')})
                                </div>
                              </div>
                            )}

                            {/* Suggested Pandas Remediation Code */}
                            {exp.pandas_code && (
                              <div style={{
                                marginTop: 10,
                                padding: '10px 12px',
                                background: 'var(--navy)',
                                color: '#f8fafc',
                                borderRadius: 6
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                                  <span style={{ fontWeight: 700, color: 'var(--peach)', fontSize: 11 }}>🐼 Suggested Pandas Code:</span>
                                </div>
                                <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: 12, whiteSpace: 'pre-wrap', color: '#e2e8f0', lineHeight: 1.4 }}>{exp.pandas_code}</pre>
                              </div>
                            )}

                            {/* MCP Action Blueprint */}
                            {exp.mcp_action && (
                              <div style={{
                                marginTop: 10,
                                padding: '10px 12px',
                                background: 'var(--white)',
                                border: '1px solid var(--border-color)',
                                borderRadius: 6
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <span style={{ fontWeight: 700, color: 'var(--navy)' }}>⚡ Model Context Protocol (MCP) Blueprint</span>
                                  <span style={{
                                    fontSize: 10,
                                    fontWeight: 800,
                                    padding: '2px 8px',
                                    borderRadius: 4,
                                    background: exp.mcp_action.risk_level === 'low' ? '#dcfce7' : exp.mcp_action.risk_level === 'medium' ? 'var(--peach)' : '#fee2e2',
                                    color: exp.mcp_action.risk_level === 'low' ? '#15803d' : 'var(--navy)'
                                  }}>
                                    RISK: {exp.mcp_action.risk_level.toUpperCase()}
                                  </span>
                                </div>
                                <div style={{ fontSize: 12, marginTop: 6, color: 'var(--navy-light)' }}>
                                  Tool Name: <code>{exp.mcp_action.tool_name}</code> • Parameters: <code>{JSON.stringify(exp.mcp_action.parameters)}</code>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 8 }}>
                            Synthesizing cognitive explanation & MCP blueprint...
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* STEP 4: Cleaning Studio */}
            {step === 4 && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 22, color: 'var(--navy)' }}>Human-in-the-Loop Cleaning Studio</h3>
                    <div style={{ fontSize: 14, color: 'var(--navy-light)', marginTop: 4 }}>
                      Inspect atomic diffs, batch-execute verified low-risk operations, or immediately roll back.
                      {scoreAfter && (
                        <span style={{ marginLeft: 12, color: '#16a34a', fontWeight: 700 }}>
                          Remediated Score: {scoreAfter.overall_score} / 100 (+{(scoreAfter.overall_score - (scoreBefore?.overall_score || 0)).toFixed(1)})
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <button
                      onClick={handleApplyAllLowRisk}
                      style={{
                        background: '#059669',
                        color: 'var(--white)',
                        border: 'none',
                        padding: '10px 18px',
                        borderRadius: 8,
                        fontWeight: 700,
                        fontSize: 13
                      }}
                    >
                      ⚡ Apply All Low-Risk (Safe)
                    </button>
                    <button
                      onClick={handleUndo}
                      style={{
                        background: 'var(--white)',
                        color: 'var(--navy)',
                        border: '1px solid var(--peach)',
                        padding: '10px 18px',
                        borderRadius: 8,
                        fontWeight: 600,
                        fontSize: 13
                      }}
                    >
                      Undo Last Action
                    </button>
                    <button
                      onClick={() => setStep(5)}
                      style={{
                        background: 'var(--terracotta)',
                        color: 'var(--white)',
                        border: 'none',
                        padding: '10px 22px',
                        borderRadius: 8,
                        fontWeight: 700,
                        fontSize: 13
                      }}
                    >
                      Export Deliverables →
                    </button>
                  </div>
                </div>

                {/* Dual Buckets: Auto-Fixable vs Needs Human Review */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                  {/* BUCKET 1: Auto-Fixable Operations */}
                  <div style={{
                    background: 'var(--white)',
                    border: '1px solid var(--peach)',
                    borderRadius: 10,
                    padding: 20,
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 18 }}>⚡</span>
                          <h4 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>
                            Auto-Fixable Operations ({cleaningOps.filter(o => o.bucket === 'auto_fixable').length})
                          </h4>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 2 }}>
                          Deterministic, non-destructive remedies: case normalization, exact duplicate drops, and exact formula recalculation (quantity × price).
                        </div>
                      </div>
                      <span style={{ fontSize: 11, background: '#dcfce7', color: '#15803d', padding: '3px 8px', borderRadius: 4, fontWeight: 700 }}>
                        SAFE TO AUTO-APPLY
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                      {cleaningOps.filter(o => o.bucket === 'auto_fixable').length === 0 ? (
                        <div style={{ fontSize: 13, color: 'var(--navy-light)', fontStyle: 'italic', padding: 8 }}>
                          No pending auto-fixable operations.
                        </div>
                      ) : (
                        cleaningOps.filter(o => o.bucket === 'auto_fixable').map(renderOperationCard)
                      )}
                    </div>
                  </div>

                  {/* BUCKET 2: Needs Human Review */}
                  <div style={{
                    background: 'var(--white)',
                    border: '1px solid #fed7aa',
                    borderRadius: 10,
                    padding: 20,
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 18 }}>🛡️</span>
                          <h4 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>
                            Needs Human Review ({cleaningOps.filter(o => o.bucket === 'needs_review').length})
                          </h4>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--navy-light)', marginTop: 2 }}>
                          Honest Remediation Governance: Outliers, ID collisions, and missing rating/email/phone preserved as null rather than fabricated.
                        </div>
                      </div>
                      <span style={{ fontSize: 11, background: '#fee2e2', color: '#991b1b', padding: '3px 8px', borderRadius: 4, fontWeight: 700 }}>
                        MANUAL REVIEW REQUIRED
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                      {cleaningOps.filter(o => o.bucket === 'needs_review').length === 0 ? (
                        <div style={{ fontSize: 13, color: 'var(--navy-light)', fontStyle: 'italic', padding: 8 }}>
                          No items flagged for manual review.
                        </div>
                      ) : (
                        cleaningOps.filter(o => o.bucket === 'needs_review').map(renderOperationCard)
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 5: Report & Export */}
            {step === 5 && session && (
              <div style={{
                background: 'var(--linen)',
                border: '1px solid var(--peach)',
                borderRadius: 12,
                padding: '40px 24px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: 42, marginBottom: 8 }}>🏆</div>
                <h3 style={{ fontSize: 24, fontWeight: 800, color: 'var(--navy)', margin: '0 0 8px 0' }}>
                  Audited Deliverables Ready
                </h3>
                <p style={{ color: 'var(--navy-light)', maxWidth: 600, margin: '0 auto 24px', fontSize: 14 }}>
                  Download the certified executive HTML report and export sanitized cleaned CSV data (formula-injection protected with Excel DDE neutralization).
                </p>

                <div style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap' }}>
                  <a
                    href={getReportUrl(session.session_id)}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      background: 'var(--navy)',
                      color: 'var(--white)',
                      padding: '13px 28px',
                      borderRadius: 8,
                      textDecoration: 'none',
                      fontWeight: 700,
                      fontSize: 14
                    }}
                  >
                    Download Executive Report (HTML)
                  </a>
                  <a
                    href={getExportCsvUrl(session.session_id)}
                    download
                    style={{
                      background: 'var(--terracotta)',
                      color: 'var(--white)',
                      padding: '13px 28px',
                      borderRadius: 8,
                      textDecoration: 'none',
                      fontWeight: 700,
                      fontSize: 14,
                      boxShadow: '0 4px 14px rgba(249, 174, 108, 0.4)'
                    }}
                  >
                    Export Cleaned CSV
                  </a>
                </div>

                <div style={{ marginTop: 28 }}>
                  <button
                    onClick={() => { setStep(1); setSession(null); setFindings([]); setProfiles([]); }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--navy)',
                      textDecoration: 'underline',
                      fontWeight: 600,
                      fontSize: 13
                    }}
                  >
                    ← Audit Another Dataset
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 4. FEATURES SHOWCASE SECTION */}
      <section id="features" style={{ padding: '80px 24px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 54 }}>
          <span style={{
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: '1px',
            color: 'var(--terracotta-dark)',
            textTransform: 'uppercase'
          }}>
            Engine Capabilities
          </span>
          <h2 style={{ fontSize: 36, fontWeight: 900, color: 'var(--navy)', margin: '8px 0 16px', letterSpacing: '-0.5px' }}>
            Built for Enterprise Precision and Zero-PII Exposure
          </h2>
          <p style={{ color: 'var(--navy-light)', fontSize: 16, maxWidth: 720, margin: '0 auto' }}>
            Engineered around the two-tier architectural standard: deterministic code speed for math and categorical checks,
            coupled with cognitive intelligence for contextual understanding.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 24
        }}>
          {[
            {
              icon: '⚡',
              title: 'Two-Tier Quality Architecture',
              desc: 'Tier 1 runs pure Python Pandas and NumPy deterministic algorithms locally in milliseconds. Tier 2 engages LLMs solely for plain-language executive translation and remediation blueprints without exposing raw records.'
            },
            {
              icon: '🔗',
              title: 'Relational Deduplication Engine',
              desc: 'Disentangles composite business relationships. Intelligently distinguishes legitimate repeated orders by the same customer across dates from true duplicate primary key collisions.'
            },
            {
              icon: '🔤',
              title: 'Polyglot Regex Core Triad',
              desc: 'Multi-locale regular expression engines validating phone numbers, emails, and postal codes across US, UK, EU, India, and APAC standards without requiring rigid single-locale assumptions.'
            },
            {
              icon: '🤖',
              title: 'Model Context Protocol (MCP) Blueprints',
              desc: 'Automatically synthesizes standardized MCP action blueprints containing tool_name, parameters, and risk classifications ready for automated agent execution.'
            },
            {
              icon: '🛡️',
              title: 'Formula Injection Defense',
              desc: 'Protects downstream analytics teams by sanitizing CSV and report exports, neutralizing Excel DDE formula exploits (=, +, -, @) before spreadsheets are opened.'
            },
            {
              icon: '🔄',
              title: 'Human-in-the-Loop Reversible Studio',
              desc: 'Preserves complete dataset auditability with non-destructive delta logging, 1-click batch application for verified low-risk issues, and single-click atomic rollback.'
            }
          ].map((f, i) => (
            <div
              key={i}
              className="feature-card"
              style={{
                backgroundColor: 'var(--white)',
                border: '1px solid var(--peach)',
                borderRadius: 14,
                padding: '28px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12
              }}
            >
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 10,
                backgroundColor: 'var(--blush)',
                border: '1px solid var(--peach)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 22
              }}>
                {f.icon}
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 800, color: 'var(--navy)', margin: 0 }}>
                {f.title}
              </h3>
              <p style={{ fontSize: 14, color: 'var(--navy-light)', lineHeight: 1.6, margin: 0 }}>
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. TARGET ENTERPRISE USE CASES */}
      <section id="use-cases" style={{
        padding: '80px 24px',
        backgroundColor: 'var(--blush)',
        borderTop: '1px solid var(--peach)',
        borderBottom: '1px solid var(--peach)'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 54 }}>
            <span style={{
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: '1px',
              color: 'var(--terracotta-dark)',
              textTransform: 'uppercase'
            }}>
              Business Application
            </span>
            <h2 style={{ fontSize: 36, fontWeight: 900, color: 'var(--navy)', margin: '8px 0 16px', letterSpacing: '-0.5px' }}>
              Where Datara AI Powers High-Stakes Operations
            </h2>
            <p style={{ color: 'var(--navy-light)', fontSize: 16, maxWidth: 680, margin: '0 auto' }}>
              From retail order reconciliation to automated data lake quality gates, audit and remediate anomalies before they impact revenue.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 20
          }}>
            {[
              {
                badge: 'Retail & E-Commerce',
                title: 'Omnichannel Order Auditing',
                desc: 'Detects contradictory line items, tax-total arithmetic mismatches (±0.01 tolerance), and fuzzy customer name variations (e.g. "mumbai" vs "Mumbai") across fragmented POS transactions.'
              },
              {
                badge: 'Data Engineering',
                title: 'Pre-ETL Lake Quality Gates',
                desc: 'Automates screening of incoming partner feeds for impossible numbers, corrupt schemas, and broken date sequences before expensive warehouse ingestion.'
              },
              {
                badge: 'Enterprise Migration',
                title: 'CRM & Legacy ERP Normalization',
                desc: 'Resolves cross-border phone formats, missing customer email addresses, and relational duplicate collisions when merging multi-system records.'
              },
              {
                badge: 'Finance & Accounting',
                title: 'Billing & Transaction Reconciliation',
                desc: 'Flags out-of-bounds outliers, inverted discounts, negative invoice balances, and cross-column formula discrepancies before quarterly financial closing.'
              }
            ].map((uc, i) => (
              <div
                key={i}
                className="feature-card"
                style={{
                  backgroundColor: 'var(--white)',
                  border: '1px solid var(--peach)',
                  borderRadius: 14,
                  padding: 24,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <span style={{
                    fontSize: 11,
                    fontWeight: 700,
                    padding: '3px 10px',
                    borderRadius: 20,
                    background: 'var(--blush)',
                    color: 'var(--navy)',
                    border: '1px solid var(--peach)'
                  }}>
                    {uc.badge}
                  </span>
                  <h3 style={{ fontSize: 18, fontWeight: 800, color: 'var(--navy)', margin: '14px 0 8px' }}>
                    {uc.title}
                  </h3>
                  <p style={{ fontSize: 13, color: 'var(--navy-light)', lineHeight: 1.6, margin: 0 }}>
                    {uc.desc}
                  </p>
                </div>
                <div style={{ marginTop: 20, borderTop: '1px solid var(--border-color)', paddingTop: 12 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--terracotta-dark)' }}>
                    Verified by Deterministic Heuristics ✓
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. HOW IT WORKS / ARCHITECTURE */}
      <section id="architecture" style={{ padding: '80px 24px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 54 }}>
          <span style={{
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: '1px',
            color: 'var(--terracotta-dark)',
            textTransform: 'uppercase'
          }}>
            Technical Architecture
          </span>
          <h2 style={{ fontSize: 36, fontWeight: 900, color: 'var(--navy)', margin: '8px 0 16px', letterSpacing: '-0.5px' }}>
            The Two-Tier Processing Pipeline
          </h2>
          <p style={{ color: 'var(--navy-light)', fontSize: 16, maxWidth: 680, margin: '0 auto' }}>
            How raw unverified datasets transform into formula-protected, certified enterprise data assets.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[
            {
              step: '01',
              name: 'Ingestion & Statistical Profiling',
              detail: 'Parses CSV payload, infers column datatypes (numeric, categorical, datetime, text), computes null distributions and statistical boundaries.'
            },
            {
              step: '02',
              name: 'Tier-1 Deterministic Anomaly Scanners',
              detail: 'Executes 5 local algorithmic engines: Null/Completeness, Outlier Detection (IQR/Z-Score), Relational Key Deduplication, Arithmetic Validation (±0.01 tolerance), and Inconsistency Clustering.'
            },
            {
              step: '03',
              name: 'PII-Shielded Statistical Aggregation',
              detail: 'Aggregates issue metrics, distributions, and column context. Zero raw sensitive rows egress to external networks or models.'
            },
            {
              step: '04',
              name: 'Tier-2 Cognitive LLM Synthesis & MCP Generation',
              detail: 'Transforms mathematical findings into plain-language executive summaries, multi-locale polyglot regex patterns, and structured MCP action schemas.'
            },
            {
              step: '05',
              name: 'Human Studio Governance & Protected Export',
              detail: 'Data stewards review atomic diffs, batch-apply safe low-risk operations, and download certified HTML audits alongside formula-injection-safe CSVs.'
            }
          ].map((pipe, i) => (
            <div
              key={i}
              style={{
                backgroundColor: 'var(--white)',
                border: '1px solid var(--peach)',
                borderRadius: 12,
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 24,
                flexWrap: 'wrap'
              }}
            >
              <div style={{
                fontSize: 24,
                fontWeight: 900,
                color: 'var(--terracotta)',
                minWidth: 48,
                height: 48,
                borderRadius: 8,
                backgroundColor: 'var(--blush)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {pipe.step}
              </div>
              <div style={{ flex: 1, minWidth: 260 }}>
                <h4 style={{ margin: 0, fontSize: 17, fontWeight: 800, color: 'var(--navy)' }}>{pipe.name}</h4>
                <p style={{ margin: '4px 0 0', fontSize: 14, color: 'var(--navy-light)', lineHeight: 1.5 }}>
                  {pipe.detail}
                </p>
              </div>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--navy-light)', padding: '4px 10px', background: 'var(--linen)', borderRadius: 6 }}>
                Sub-Second Execution
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* 7. TEAM MEMBERS SHOWCASE */}
      <section id="team" style={{
        padding: '80px 24px',
        backgroundColor: 'var(--blush)',
        borderTop: '1px solid var(--peach)',
        borderBottom: '1px solid var(--peach)'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 54 }}>
            <span style={{
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: '1px',
              color: 'var(--terracotta-dark)',
              textTransform: 'uppercase'
            }}>
              Engine Leadership
            </span>
            <h2 style={{ fontSize: 36, fontWeight: 900, color: 'var(--navy)', margin: '8px 0 16px', letterSpacing: '-0.5px' }}>
              Meet the Engineering Team
            </h2>
            <p style={{ color: 'var(--navy-light)', fontSize: 16, maxWidth: 650, margin: '0 auto' }}>
              Specialists in distributed data architecture, deterministic verification, cognitive LLM protocols, and enterprise data security.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 24
          }}>
            {[
              {
                name: 'Navadeep Reddy Benjara',
                role: 'Lead AI Systems Architect & Full-Stack Lead',
                focus: 'Two-Tier Detection Pipeline, Adaptive Rule Synthesizer & Sandbox Engine',
                badge: 'System Architecture',
                initials: 'NB'
              },
              {
                name: 'Hemalatha Donapati',
                role: 'Chief Data Quality & ML Research Lead',
                focus: 'Zero-False-Positive Safety Verification & Anomaly Pattern Synthesis',
                badge: 'AI & ML Lead',
                initials: 'HD'
              },
              {
                name: 'Lavanya Jalli',
                role: 'Data Governance & Validation Algorithms Lead',
                focus: '3-Tier Relational Deduplication & Cross-Column Arithmetic Reconciliation',
                badge: 'Core Algorithms',
                initials: 'LJ'
              },
              {
                name: 'Abhishek Magasala',
                role: 'Enterprise Security & Protocols Lead',
                focus: 'Model Context Protocol (MCP), Zero-PII Egress & Formula Injection Defense',
                badge: 'Security & Protocols',
                initials: 'AM'
              }
            ].map((member, i) => (
              <div
                key={i}
                className="feature-card"
                style={{
                  backgroundColor: 'var(--white)',
                  border: '1px solid var(--peach)',
                  borderRadius: 14,
                  padding: '28px 20px',
                  textAlign: 'center'
                }}
              >
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  backgroundColor: 'var(--navy)',
                  color: 'var(--white)',
                  fontSize: 22,
                  fontWeight: 800,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                  border: '3px solid var(--terracotta)'
                }}>
                  {member.initials}
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: 'var(--navy)', margin: '0 0 4px' }}>
                  {member.name}
                </h3>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--terracotta-dark)', marginBottom: 8 }}>
                  {member.role}
                </div>
                <p style={{ fontSize: 12, color: 'var(--navy-light)', margin: '0 0 16px', lineHeight: 1.5 }}>
                  {member.focus}
                </p>
                <span style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '4px 12px',
                  borderRadius: 20,
                  background: 'var(--linen)',
                  color: 'var(--navy)',
                  border: '1px solid var(--peach)'
                }}>
                  {member.badge}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 8. FOOTER */}
      <footer style={{
        backgroundColor: 'var(--navy)',
        color: 'var(--white)',
        padding: '54px 24px 36px',
        marginTop: 'auto'
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 32,
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          paddingBottom: 36
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: 'var(--terracotta)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: 16,
                color: 'var(--white)'
              }}>
                D
              </div>
              <span style={{ fontSize: 18, fontWeight: 800 }}>Datara AI</span>
            </div>
            <p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: 13, maxWidth: 360, margin: 0, lineHeight: 1.6 }}>
              Enterprise data quality auditing, relational deduplication, visual sandbox remediation, and adaptive rule learning agent.
              Certified Spec Kit v1.3.0 Architecture.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 40, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', color: 'var(--peach)', marginBottom: 12 }}>
                Navigation
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13 }}>
                <a href="#features" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>Features</a>
                <a href="#use-cases" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>Use Cases</a>
                <a href="#architecture" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>Architecture</a>
                <a href="#demo" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>Live Studio</a>
                <a href="#team" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>Team</a>
              </div>
            </div>

            <div>
              <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', color: 'var(--peach)', marginBottom: 12 }}>
                Resources
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13 }}>
                <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>FastAPI Swagger</a>
                <a href="http://localhost:8000/redoc" target="_blank" rel="noreferrer" style={{ color: 'rgba(255, 255, 255, 0.8)', textDecoration: 'none' }}>Redoc API Specs</a>
                <span style={{ color: 'rgba(255, 255, 255, 0.5)' }}>Constitution v1.3.0</span>
              </div>
            </div>
          </div>
        </div>

        <div style={{
          maxWidth: 1200,
          margin: '24px auto 0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 12,
          color: 'rgba(255, 255, 255, 0.5)',
          flexWrap: 'wrap',
          gap: 12
        }}>
          <div>
            © {new Date().getFullYear()} Datara AI. All rights reserved. Built for enterprise data integrity.
          </div>
          <div style={{ display: 'flex', gap: 16 }}>
            <span>Zero-PII Compliance</span>
            <span>•</span>
            <span>Deterministic Guarantees</span>
            <span>•</span>
            <span>Model Context Protocol</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
