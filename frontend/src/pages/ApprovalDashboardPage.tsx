import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { 
  ApprovalTimelineResponse, 
  QuestionPaper, 
  ApprovalWorkflowResponse 
} from '../types';

export default function ApprovalDashboardPage() {
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
        <div className="md:col-span-1 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div className="px-4 py-5 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
              Pending My Approval
            </h3>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700 h-[600px] overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-gray-500">Loading...</div>
            ) : pendingPapers.length === 0 ? (
              <div className="p-4 text-center text-gray-500">No papers pending your approval.</div>
            ) : (
              pendingPapers.map((paper) => (
                <div 
                  key={paper.id} 
                  className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors ${selectedPaper?.paper.id === paper.id ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''}`}
                  onClick={() => fetchTimeline(paper.id)}
                >
                  <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400 truncate">
                    {paper.paper_code} - Version {paper.version}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {paper.title}
                  </p>
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 py-0.5 px-2 rounded-full font-medium">
                      {paper.status.replace('_', ' ')}
                    </span>
                    <span className="text-gray-400">
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
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 h-full flex flex-col">
              <div className="px-4 py-5 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
                  {selectedPaper.paper.title} ({selectedPaper.paper.paper_code})
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Version {selectedPaper.paper.version} • Uploaded by {selectedPaper.paper.uploaded_by}
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
                      {STAGES.map((stageName, stageIdx) => {
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
              <div className="p-4 bg-gray-50 dark:bg-gray-750 border-t border-gray-200 dark:border-gray-700">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Remarks (Optional)</label>
                  <textarea
                    rows={2}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white sm:text-sm"
                    placeholder="Enter approval or rejection remarks..."
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => handleDecision('return')}
                    disabled={decisionLoading}
                    className="inline-flex items-center px-4 py-2 border border-yellow-300 shadow-sm text-sm font-medium rounded-md text-yellow-700 bg-yellow-50 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                  >
                    Return for Revision
                  </button>
                  <button
                    onClick={() => handleDecision('reject')}
                    disabled={decisionLoading}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecision('approve')}
                    disabled={decisionLoading}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    {decisionLoading ? 'Processing...' : 'Approve Paper'}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 h-[600px] flex items-center justify-center text-gray-500">
              Select a paper to view its timeline and make a decision.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
