import { useEffect, useState } from 'react';
import api from '../services/api';
import type { 
  ApprovalTimelineResponse, 
  QuestionPaper 
} from '../types';

export const ApprovalDashboardPage = () => {
  const [pendingPapers, setPendingPapers] = useState<QuestionPaper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<ApprovalTimelineResponse | null>(null);
  const [remarks, setRemarks] = useState('');
  const [loading, setLoading] = useState(false);
  const [decisionLoading, setDecisionLoading] = useState(false);

  const fetchPendingApprovals = async () => {
    setLoading(true);
    try {
      const response = await api.get('/workflows/pending');
      setPendingPapers(response.data.data);
    } catch (error) {
      console.error('Failed to fetch pending approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTimeline = async (paperId: string) => {
    try {
      const response = await api.get(`/workflows/${paperId}`);
      setSelectedPaper(response.data.data);
      setRemarks('');
    } catch (error) {
      console.error('Failed to fetch timeline:', error);
    }
  };

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  const handleDecision = async (decision: 'approve' | 'reject' | 'return') => {
    if (!selectedPaper) return;
    setDecisionLoading(true);
    try {
      await api.post(`/workflows/${selectedPaper.paper.id}/${decision}`, {
        decision,
        remarks
      });
      setSelectedPaper(null);
      fetchPendingApprovals();
    } catch (error) {
      console.error(`Failed to ${decision} paper:`, error);
    } finally {
      setDecisionLoading(false);
    }
  };

  const STAGES = ['Question Setter', 'Moderator', 'Controller', 'Admin'];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Approval Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Review and approve question papers</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: List of pending papers */}
        <div className="md:col-span-1 glass-panel rounded-2xl shadow-xl border border-white/5 flex flex-col h-[700px]">
          <div className="px-4 py-5 border-b border-white/5 bg-slate-900/50">
            <h3 className="text-lg font-bold text-white tracking-tight">
              Pending My Approval
            </h3>
          </div>
          <div className="divide-y divide-white/5 flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-sm">Syncing queue...</div>
            ) : pendingPapers.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">No papers pending your approval.</div>
            ) : (
              pendingPapers.map((paper) => (
                <div 
                  key={paper.id} 
                  className={`p-4 cursor-pointer hover:bg-white/[0.02] transition-colors ${selectedPaper?.paper.id === paper.id ? 'bg-indigo-500/10 border-l-2 border-indigo-500' : 'border-l-2 border-transparent'}`}
                  onClick={() => fetchTimeline(paper.id)}
                >
                  <p className="text-sm font-semibold text-indigo-400 truncate">
                    {paper.paper_code} <span className="text-[10px] text-slate-500 uppercase tracking-wider ml-1">v{paper.version}</span>
                  </p>
                  <p className="text-xs font-medium text-slate-300 mt-1">
                    {paper.title}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 py-0.5 px-2 rounded font-bold tracking-wider uppercase text-[9px]">
                      {paper.status.replace('_', ' ')}
                    </span>
                    <span className="text-slate-500 font-mono text-[10px]">
                      {new Date(paper.upload_time).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Timeline & Actions */}
        <div className="md:col-span-2">
          {selectedPaper ? (
            <div className="glass-panel rounded-2xl shadow-xl border border-white/5 h-[700px] flex flex-col">
              <div className="px-6 py-5 border-b border-white/5 bg-slate-900/50">
                <h3 className="text-lg font-bold text-white">
                  {selectedPaper.paper.title} <span className="text-slate-500 text-base font-normal">({selectedPaper.paper.paper_code})</span>
                </h3>
                <p className="mt-1 text-xs text-slate-400 font-medium tracking-wide uppercase">
                  Version {selectedPaper.paper.version} • Uploaded by <span className="text-indigo-400">{selectedPaper.paper.uploaded_by}</span>
                </p>
              </div>
              
              <div className="p-6 flex-1 overflow-y-auto">
                {/* Timeline Progress */}
                <div className="mb-8">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Approval Progress</h4>
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center" aria-hidden="true">
                      <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                    </div>
                    <div className="relative flex justify-between">
                      {STAGES.map((stageName) => {
                        const historyStage = selectedPaper.history.find(h => h.approval_level === stageName);
                        const isCurrent = selectedPaper.current_stage === stageName;
                        const isApproved = historyStage?.decision === 'approved';
                        const isRejected = historyStage?.decision === 'rejected';
                        
                        let bgColor = 'bg-gray-200 dark:bg-gray-700';
                        let textColor = 'text-gray-500 dark:text-gray-400';
                        
                        if (isApproved) {
                          bgColor = 'bg-green-500';
                          textColor = 'text-green-600 dark:text-green-400 font-medium';
                        } else if (isRejected) {
                          bgColor = 'bg-red-500';
                          textColor = 'text-red-600 dark:text-red-400 font-medium';
                        } else if (isCurrent) {
                          bgColor = 'bg-yellow-400 border-4 border-white dark:border-gray-800';
                          textColor = 'text-indigo-600 dark:text-indigo-400 font-bold';
                        }

                        return (
                          <div key={stageName} className="flex flex-col items-center">
                            <div className={`h-8 w-8 rounded-full flex items-center justify-center shadow ${bgColor}`}>
                              {isApproved && <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>}
                              {isRejected && <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>}
                            </div>
                            <span className={`mt-2 text-xs ${textColor}`}>{stageName}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Workflow History */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Workflow History</h4>
                  <div className="flow-root">
                    <ul className="-mb-8">
                      {selectedPaper.history.map((event, eventIdx) => (
                        <li key={event.id}>
                          <div className="relative pb-8">
                            {eventIdx !== selectedPaper.history.length - 1 ? (
                              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-700" aria-hidden="true"></span>
                            ) : null}
                            <div className="relative flex space-x-3">
                              <div>
                                <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white dark:ring-gray-800 ${
                                  event.decision === 'approved' ? 'bg-green-500' :
                                  event.decision === 'rejected' ? 'bg-red-500' :
                                  event.decision === 'returned' ? 'bg-yellow-500' : 'bg-gray-400'
                                }`}>
                                  {/* Icon omitted for brevity */}
                                </span>
                              </div>
                              <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                                <div>
                                  <p className="text-sm text-gray-500 dark:text-gray-400">
                                    {event.decision.charAt(0).toUpperCase() + event.decision.slice(1)} at <span className="font-medium text-gray-900 dark:text-white">{event.approval_level}</span>
                                    {event.approver_name && ` by ${event.approver_name}`}
                                  </p>
                                  {event.remarks && (
                                    <div className="mt-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-750 p-3 rounded-md">
                                      {event.remarks}
                                    </div>
                                  )}
                                </div>
                                <div className="text-right text-xs whitespace-nowrap text-gray-500 dark:text-gray-400">
                                  {new Date(event.approved_at || event.created_at).toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-6 border-t border-white/5 bg-slate-900/30">
                <div className="mb-4">
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Remarks (Optional)</label>
                  <textarea
                    rows={2}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 resize-none"
                    placeholder="Enter approval or rejection remarks..."
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => handleDecision('return')}
                    disabled={decisionLoading}
                    className="px-4 py-2 bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                  >
                    Return for Revision
                  </button>
                  <button
                    onClick={() => handleDecision('reject')}
                    disabled={decisionLoading}
                    className="px-4 py-2 bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecision('approve')}
                    disabled={decisionLoading}
                    className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-bold transition-all disabled:opacity-50 shadow-lg"
                  >
                    {decisionLoading ? 'Processing...' : 'Approve Paper'}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-2xl shadow-xl border border-white/5 h-[700px] flex items-center justify-center text-slate-500 text-sm">
              Select a paper to view its timeline and make a decision.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
