import React, { useState, useEffect } from "react";
import { centerService } from "../services/centerService";
import type { ExaminationCenter } from "../types";
import { ShieldAlert, Loader2, Building2, Key, CheckCircle2, XCircle, Plus, X } from "lucide-react";

export const CentersPage: React.FC = () => {
  const [centers, setCenters] = useState<ExaminationCenter[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [updatingCenterId, setUpdatingCenterId] = useState<string | null>(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCenterCode, setNewCenterCode] = useState("");
  const [newCenterName, setNewCenterName] = useState("");
  const [newCenterPubKey, setNewCenterPubKey] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchCenters = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await centerService.getCenters();
      setCenters(data);
    } catch (err: any) {
      console.error(err);
      setErrorMessage("Access Denied: Missing system:manage permissions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCenters();
  }, []);

  const handleDeactivate = async (centerId: string) => {
    if (!window.confirm("Are you sure you want to revoke this center? They will no longer be able to execute releases.")) return;
    
    setUpdatingCenterId(centerId);
    try {
      await centerService.deactivateCenter(centerId);
      // Optimistic update
      setCenters(centers.map((c) => (c.id === centerId ? { ...c, status: "revoked" } : c)));
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.message || "Operation failed.");
    } finally {
      setUpdatingCenterId(null);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRegistering(true);
    setModalError(null);
    
    try {
      // 1. Create the center
      const center = await centerService.registerCenter({
        center_code: newCenterCode,
        name: newCenterName,
      });
      
      // 2. Provision its public key
      const keyIdentifier = `key-${center.center_code}-${Date.now()}`;
      const updatedCenter = await centerService.provisionKey(center.id, {
        public_key_pem: newCenterPubKey,
        key_identifier: keyIdentifier
      });
      
      setCenters([...centers, updatedCenter]);
      setIsModalOpen(false);
      
      // Reset form
      setNewCenterCode("");
      setNewCenterName("");
      setNewCenterPubKey("");
    } catch (err: any) {
      console.error(err);
      setModalError(err.response?.data?.message || "Registration failed. Ensure the public key is a valid PEM format.");
    } finally {
      setIsRegistering(false);
    }
  };

  if (isLoading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
        <span className="text-xs text-slate-400">Syncing examination centers...</span>
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
          {errorMessage} Please verify you have administrative permissions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-xl font-bold tracking-tight text-white">Examination Centers</h1>
          <p className="text-xs text-slate-400">Manage participating centers and their public cryptographic keys.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-4 py-2 rounded-xl text-sm font-bold hover:bg-emerald-500/30 transition-all shadow-lg"
        >
          <Plus className="w-4 h-4" />
          Register Center
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {centers.map((center) => (
          <div key={center.id} className="glass-panel rounded-2xl p-6 border border-white/5 space-y-4 relative overflow-hidden group">
            {/* Status indicator strip */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${center.status === 'active' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
            
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${center.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-200">{center.name}</h3>
                  <span className="text-xs text-slate-400 font-mono">{center.center_code}</span>
                </div>
              </div>
              <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider border ${
                center.status === 'active' 
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              }`}>
                {center.status}
              </span>
            </div>

            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-slate-500" />
                <span className="text-xs text-slate-400">Public Key Provisioned:</span>
                {center.public_key_pem ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-auto" />
                ) : (
                  <XCircle className="w-4 h-4 text-amber-500 ml-auto" />
                )}
              </div>
              <div className="text-[10px] text-slate-500 font-mono truncate">
                {center.key_identifier || "No Key Identifier"}
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              {center.status === 'active' && (
                <button
                  onClick={() => handleDeactivate(center.id)}
                  disabled={updatingCenterId === center.id}
                  className="text-xs font-bold text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500 px-3 py-1.5 rounded-lg border border-rose-500/20 transition-all flex items-center gap-2"
                >
                  {updatingCenterId === center.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
                  Revoke Node
                </button>
              )}
            </div>
          </div>
        ))}

        {centers.length === 0 && (
          <div className="col-span-full py-12 text-center text-slate-500">
            <Building2 className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No examination centers registered yet.</p>
          </div>
        )}
      </div>

      {/* Registration Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center p-5 border-b border-slate-800">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Building2 className="w-5 h-5 text-indigo-400" />
                Register New Center
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleRegister} className="p-6 space-y-4">
              {modalError && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl text-xs flex gap-2 items-start">
                  <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{modalError}</span>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Center Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CTR001"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50"
                    value={newCenterCode}
                    onChange={(e) => setNewCenterCode(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Center Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Central High School"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50"
                    value={newCenterName}
                    onChange={(e) => setNewCenterName(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex justify-between">
                  <span>Public Key (PEM format)</span>
                  <span className="text-slate-500 normal-case">Required for Hybrid Encryption</span>
                </label>
                <textarea
                  required
                  rows={6}
                  placeholder="-----BEGIN PUBLIC KEY-----\n..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs text-emerald-400 font-mono focus:outline-none focus:border-emerald-500/50 resize-none"
                  value={newCenterPubKey}
                  onChange={(e) => setNewCenterPubKey(e.target.value)}
                />
              </div>

              <div className="pt-4 flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-bold text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRegistering}
                  className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-5 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                >
                  {isRegistering ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  Complete Registration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default CentersPage;
