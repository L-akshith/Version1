import React, { useState, useEffect } from "react";
import api from "../services/api";
import type { Role } from "../types";
import { KeyRound, ShieldAlert, Loader2 } from "lucide-react";

export const RolesPage: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchRoles = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const res = await api.get("/roles?limit=100");
        if (res.data && res.data.data) {
          setRoles(res.data.data);
        }
      } catch (err: any) {
        console.error(err);
        setErrorMessage("Access Denied: Missing permissions to read roles database.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchRoles();
  }, []);

  if (isLoading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
        <span className="text-xs text-slate-400">Loading RBAC matrix...</span>
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
        <p className="text-sm text-slate-400">{errorMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="space-y-1">
        <h1 className="text-xl font-bold tracking-tight text-white">Access Control Matrix</h1>
        <p className="text-xs text-slate-400">Default roles and privilege boundaries seeded on system initialization.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {roles.map((role) => (
          <div key={role.id} className="glass-panel rounded-2xl p-6 space-y-4 flex flex-col justify-between border border-white/5">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">{role.name}</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{role.description}</p>
            </div>

            <div className="space-y-2.5">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-white/5 pb-1">
                Assigned Privileges ({role.permissions.length})
              </h4>
              <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                {role.permissions.map((perm) => (
                  <span
                    key={perm.id}
                    title={perm.description}
                    className="inline-block text-[9.5px] font-bold text-slate-300 bg-white/5 border border-white/5 px-2 py-0.5 rounded-md hover:border-white/10 transition-colors cursor-help"
                  >
                    {perm.name}
                  </span>
                ))}
                {role.permissions.length === 0 && (
                  <span className="text-[10px] text-slate-500 italic">No direct permissions mapped</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
export default RolesPage;
