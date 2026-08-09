import React, { useState, useEffect } from "react";
import api from "../services/api";
import type { User, Role } from "../types";
import { ShieldAlert, UserMinus, UserCheck, Key, Loader2 } from "lucide-react";

export const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  const fetchUsersAndRoles = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [usersRes, rolesRes] = await Promise.all([
        api.get("/users?limit=100"),
        api.get("/roles?limit=100"),
      ]);

      if (usersRes.data && usersRes.data.data) {
        setUsers(usersRes.data.data);
      }
      if (rolesRes.data && rolesRes.data.data) {
        setRoles(rolesRes.data.data);
      }
    } catch (err: any) {
      console.error(err);
      setErrorMessage("Access Denied: Missing administrative permissions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndRoles();
  }, []);

  const handleToggleActiveStatus = async (user: User) => {
    setUpdatingUserId(user.id);
    try {
      const endpoint = user.is_active ? "deactivate" : "activate";
      const res = await api.put(`/users/${user.id}/${endpoint}`);
      if (res.data && res.data.success) {
        setUsers(users.map((u) => (u.id === user.id ? { ...u, is_active: !u.is_active } : u)));
      }
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.message || "Operation failed.");
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleRoleChange = async (userId: string, roleId: string) => {
    setUpdatingUserId(userId);
    try {
      const res = await api.put(`/users/${userId}/role`, { role_id: roleId });
      if (res.data && res.data.success) {
        const updatedUser = res.data.data;
        setUsers(users.map((u) => (u.id === userId ? { ...u, role_id: roleId, role_name: updatedUser.role_name } : u)));
      }
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.message || "Role assignment failed.");
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
        <span className="text-xs text-slate-400">Syncing user database...</span>
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
          {errorMessage} Please verify you are logged in as an administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="space-y-1">
        <h1 className="text-xl font-bold tracking-tight text-white">Operator Registry</h1>
        <p className="text-xs text-slate-400">Configure roles and permissions for system terminals.</p>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden shadow-xl border border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02] text-xs font-bold text-slate-400 uppercase tracking-widest">
                <th className="p-4 pl-6">Operator Name</th>
                <th className="p-4">Official Email</th>
                <th className="p-4">Assigned Role</th>
                <th className="p-4">Account Status</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-slate-200">
              {users.map((item) => (
                <tr key={item.id} className="hover:bg-white/[0.01] transition-colors">
                  <td className="p-4 pl-6 font-semibold">{item.full_name}</td>
                  <td className="p-4 text-slate-400">{item.email}</td>
                  <td className="p-4">
                    {item.is_superuser ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 border border-amber-500/15 px-2 py-0.5 rounded-md">
                        <Key className="w-3 h-3" /> Root Admin
                      </span>
                    ) : (
                      <select
                        value={item.role_id || ""}
                        onChange={(e) => handleRoleChange(item.id, e.target.value)}
                        disabled={updatingUserId === item.id}
                        className="bg-slate-900 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-white/30"
                      >
                        <option value="">Unassigned</option>
                        {roles.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="p-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                        item.is_active
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/15"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/15"
                      }`}
                    >
                      {item.is_active ? "Active" : "Deactivated"}
                    </span>
                  </td>
                  <td className="p-4 pr-6 text-right">
                    {!item.is_superuser && (
                      <button
                        onClick={() => handleToggleActiveStatus(item)}
                        disabled={updatingUserId === item.id}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                          item.is_active
                            ? "bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/10"
                            : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/10"
                        }`}
                      >
                        {item.is_active ? (
                          <>
                            <UserMinus className="w-3.5 h-3.5" /> Deactivate
                          </>
                        ) : (
                          <>
                            <UserCheck className="w-3.5 h-3.5" /> Activate
                          </>
                        )}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default UsersPage;
