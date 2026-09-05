import React, { useState, useEffect } from "react";
import api from "../services/api";
import { releaseService } from "../services/releaseService";
import type { ReleaseSchedule, QuestionPaper } from "../types";
import { 
  Rocket, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  ShieldAlert, 
  Loader2, 
  X,
  Lock,
  Play
} from "lucide-react";

export const ReleaseDashboardPage: React.FC = () => {
  const [schedules, setSchedules] = useState<ReleaseSchedule[]>([]);
  const [eligiblePapers, setEligiblePapers] = useState<QuestionPaper[]>([]);
  
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Modal State
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [selectedPaperId, setSelectedPaperId] = useState("");
  const [releaseDate, setReleaseDate] = useState("");
  const [releaseTime, setReleaseTime] = useState("");
  const [isScheduling, setIsScheduling] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const [executingId, setExecutingId] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const schedulesData = await releaseService.getUpcomingSchedules();
      setSchedules(schedulesData);

      // Fetch eligible papers (encrypted or scheduled)
      const papersRes = await api.get("/question-papers?status=encrypted&limit=100");
      if (papersRes.data?.success) {
        setEligiblePapers(papersRes.data.data);
      }
    } catch (err: any) {
      console.error(err);
      setErrorMessage("Access Denied: Missing papers:release permissions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPaperId || !releaseDate || !releaseTime) {
      setModalError("Please fill all required fields.");
      return;
    }
    
    setIsScheduling(true);
    setModalError(null);
    try {
      // Combine local date and time and convert to UTC ISO string
      const localDateTimeString = `${releaseDate}T${releaseTime}`;
      const localDate = new Date(localDateTimeString);
      const isoString = localDate.toISOString();

      await releaseService.scheduleRelease(selectedPaperId, { release_at: isoString });
      setIsScheduleModalOpen(false);
      
      // Reset form
      setSelectedPaperId("");
      setReleaseDate("");
      setReleaseTime("");
      
      fetchDashboardData();
    } catch (err: any) {
      console.error(err);
      setModalError(err.response?.data?.message || err.response?.data?.detail || "Scheduling failed. Ensure the time is in the future.");
    } finally {
      setIsScheduling(false);
    }
  };

  const handleExecute = async (paperId: string) => {
    if (!window.confirm("Are you absolutely sure you want to execute this release now? Cryptographic keys will be dispatched to all authorized centers.")) {
      return;
    }
    
    setExecutingId(paperId);
    try {
      await releaseService.executeRelease(paperId);
      alert("Release executed successfully! Keys have been unwrapped and dispatched.");
      fetchDashboardData();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.message || err.response?.data?.detail || "Execution failed.");
    } finally {
      setExecutingId(null);
    }
  };

  const formatLocalTime = (isoString: string) => {
    const d = new Date(isoString);
    return {
      date: d.toLocaleDateString(),
      time: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  if (isLoading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
        <span className="text-xs text-slate-400">Loading Release Dashboard...</span>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="glass-panel rounded-2xl p-8 max-w-xl mx-auto text-center space-y-4 animate-fade-in mt-12">
        <div className="flex justify-center text-rose-500">
          <ShieldAlert className="w-12 h-12" />
        </div>
        <h3 className="text-lg font-bold text-white uppercase tracking-wider">Access Denied</h3>
        <p className="text-sm text-slate-400">
          {errorMessage} Please verify you are a Controller with release permissions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Rocket className="w-6 h-6 text-indigo-400" />
            Release Dashboard
          </h1>
          <p className="text-xs text-slate-400">Schedule and execute cryptographic unlocks for examination centers.</p>
        </div>
        <button 
          onClick={() => setIsScheduleModalOpen(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-500/20"
        >
          <Calendar className="w-4 h-4" />
          Schedule Release
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {schedules.map((schedule) => {
          const { date, time } = formatLocalTime(schedule.release_at);
          const isPast = new Date(schedule.release_at) <= new Date();
          const isExecuted = schedule.status === 'executed';

          return (
            <div key={schedule.id} className="glass-panel rounded-2xl p-6 border border-white/5 space-y-6 relative overflow-hidden group">
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${isExecuted ? 'bg-emerald-500' : 'bg-sky-500'}`} />
              
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    Paper ID: <span className="font-mono text-indigo-300">{schedule.question_paper_id.substring(0,8)}...</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                    Schedule ID: {schedule.id.substring(0,8)}
                  </p>
                </div>
                <span className={`px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-wider border ${
                  isExecuted 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                    : 'bg-sky-500/10 text-sky-400 border-sky-500/20'
                }`}>
                  {schedule.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-slate-950/50 rounded-xl p-4 border border-white/5">
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span className="text-[10px] uppercase font-bold tracking-wider">Local Date</span>
                  </div>
                  <p className="text-sm font-semibold text-white">{date}</p>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span className="text-[10px] uppercase font-bold tracking-wider">Local Time</span>
                  </div>
                  <p className="text-sm font-semibold text-white">{time}</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-white/5">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Lock className="w-3.5 h-3.5" />
                  <span>Payload Secured</span>
                </div>
                
                {!isExecuted && (
                  <button
                    onClick={() => handleExecute(schedule.question_paper_id)}
                    disabled={executingId === schedule.question_paper_id || !isPast}
                    className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      isPast
                        ? "bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-500/20"
                        : "bg-slate-800 text-slate-500 cursor-not-allowed border border-white/5"
                    }`}
                    title={!isPast ? "Release time not yet reached" : "Execute Release Now"}
                  >
                    {executingId === schedule.question_paper_id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                    {isPast ? "Execute Release" : "Waiting for Time"}
                  </button>
                )}
                {isExecuted && (
                  <div className="flex items-center gap-2 text-xs font-bold text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Keys Dispatched</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {schedules.length === 0 && (
          <div className="col-span-full py-16 text-center text-slate-500">
            <Rocket className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p className="text-sm">No upcoming releases scheduled.</p>
          </div>
        )}
      </div>

      {/* Schedule Modal */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center p-5 border-b border-slate-800 bg-slate-900">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-indigo-400" />
                Schedule New Release
              </h2>
              <button onClick={() => setIsScheduleModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleScheduleSubmit} className="p-6 space-y-5">
              {modalError && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-xs flex gap-2 items-start">
                  <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{modalError}</span>
                </div>
              )}
              
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Select Encrypted Paper</label>
                <select
                  required
                  value={selectedPaperId}
                  onChange={(e) => setSelectedPaperId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50"
                >
                  <option value="">-- Choose a paper --</option>
                  {eligiblePapers.map(p => (
                    <option key={p.id} value={p.id}>{p.paper_code} - {p.title} (v{p.version})</option>
                  ))}
                </select>
                {eligiblePapers.length === 0 && (
                  <p className="text-[10px] text-amber-500 mt-1">No eligible encrypted papers found. Ensure a paper is fully approved and encrypted.</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Local Date</label>
                  <input
                    type="date"
                    required
                    value={releaseDate}
                    onChange={(e) => setReleaseDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Local Time</label>
                  <input
                    type="time"
                    required
                    value={releaseTime}
                    onChange={(e) => setReleaseTime(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50"
                  />
                </div>
              </div>

              <div className="bg-indigo-500/10 border border-indigo-500/20 p-4 rounded-xl flex items-start gap-3 mt-2">
                <Lock className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-indigo-300">Secure Dispatch Target</h4>
                  <p className="text-[10px] text-indigo-200/70">
                    The chosen date and time will be securely converted to UTC. At execution, the central AES key will be wrapped using the public keys of all authorized examination centers and securely dispatched.
                  </p>
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsScheduleModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-bold text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isScheduling || eligiblePapers.length === 0}
                  className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-5 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                >
                  {isScheduling ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
                  Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default ReleaseDashboardPage;
