import React, { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";
import { Subject, SubjectStatistics } from "../types";
import { 
  BookOpen, 
  Search, 
  Plus, 
  Filter, 
  MoreVertical,
  CheckCircle2,
  Clock,
  Archive,
  AlertCircle
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const subjectSchema = z.object({
  exam_id: z.string().uuid("Please select a valid exam"),
  subject_code: z.string().min(2).max(50),
  subject_name: z.string().min(2).max(255),
  language: z.string().min(2).max(50),
  description: z.string().max(2000).optional().or(z.literal("")),
});

type SubjectFormData = z.infer<typeof subjectSchema>;

export const SubjectsPage: React.FC = () => {
  const { user } = useAuth();
  
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [stats, setStats] = useState<SubjectStatistics>({ total: 0, draft: 0, active: 0, archived: 0 });
  const [exams, setExams] = useState<{id: string, exam_name: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [examFilter, setExamFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  
  // Permissions
  const canCreate = user?.is_superuser || ["Admin", "Controller"].includes(user?.role_name || "");
  const canUpdate = user?.is_superuser || ["Admin", "Controller"].includes(user?.role_name || "");
  const canDelete = user?.is_superuser || ["Admin"].includes(user?.role_name || "");

  const { register, handleSubmit, reset, formState: { errors }, setValue } = useForm<SubjectFormData>({
    resolver: zodResolver(subjectSchema)
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch stats
      const statsRes = await api.get("/subjects/statistics");
      if (statsRes.data.success) {
        setStats(statsRes.data.data);
      }

      // Fetch exams for dropdowns
      const examsRes = await api.get("/exams?limit=100");
      if (examsRes.data.success) {
        setExams(examsRes.data.data);
      }

      // Fetch subjects
      let url = `/subjects?limit=100`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      if (examFilter !== "all") url += `&exam_id=${examFilter}`;
      if (searchQuery) url += `&search=${searchQuery}`;
      
      const res = await api.get(url);
      if (res.data.success) {
        setSubjects(res.data.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load subjects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter, examFilter, searchQuery]);

  const onCreateSubmit = async (data: SubjectFormData) => {
    try {
      await api.post("/subjects", data);
      setIsCreateModalOpen(false);
      reset();
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to create subject");
    }
  };

  const onDeleteConfirm = async () => {
    if (!selectedSubject) return;
    try {
      await api.delete(`/subjects/${selectedSubject.id}`);
      setIsDeleteModalOpen(false);
      setSelectedSubject(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete subject");
    }
  };

  const onUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubject) return;
    
    try {
      await api.put(`/subjects/${selectedSubject.id}`, {
        subject_name: selectedSubject.subject_name,
        language: selectedSubject.language,
        description: selectedSubject.description,
        status: selectedSubject.status,
      });
      setIsUpdateModalOpen(false);
      setSelectedSubject(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update subject");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      case "draft": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      case "archived": return "text-slate-400 bg-slate-500/10 border-slate-500/20";
      default: return "text-blue-400 bg-blue-500/10 border-blue-500/20";
    }
  };

  const statCards = [
    { title: "Total Subjects", value: stats.total, icon: BookOpen, color: "text-blue-400", bg: "bg-blue-500/5" },
    { title: "Draft", value: stats.draft, icon: Clock, color: "text-amber-400", bg: "bg-amber-500/5" },
    { title: "Active", value: stats.active, icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/5" },
    { title: "Archived", value: stats.archived, icon: Archive, color: "text-slate-400", bg: "bg-slate-500/5" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header & Stats */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Subject Management</h1>
          <p className="text-sm text-slate-400 mt-1">Configure subjects and link them to parent examinations.</p>
        </div>
        {canCreate && (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-colors shadow-lg shadow-indigo-500/20"
          >
            <Plus className="w-4 h-4" />
            New Subject
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((c, i) => (
          <div key={i} className={`glass-card rounded-2xl p-6 ${c.bg}`}>
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{c.title}</span>
              <c.icon className={`w-5 h-5 ${c.color}`} />
            </div>
            <span className="text-2xl font-black tracking-tight text-white block mt-4">{c.value}</span>
          </div>
        ))}
      </div>

      {/* Filters & Table */}
      <div className="glass-panel rounded-2xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-white/5 flex flex-col md:flex-row gap-4 justify-between items-center bg-slate-900/50">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative w-full md:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search subject code or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-950/50 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative">
              <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-9 pr-8 py-2 bg-slate-950/50 border border-white/10 rounded-xl text-sm text-slate-200 appearance-none focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            
            <select
                value={examFilter}
                onChange={(e) => setExamFilter(e.target.value)}
                className="px-4 py-2 bg-slate-950/50 border border-white/10 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500 max-w-[200px] truncate"
              >
                <option value="all">All Exams</option>
                {exams.map(ex => (
                  <option key={ex.id} value={ex.id}>{ex.exam_name}</option>
                ))}
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-900/80 text-slate-400 font-semibold border-b border-white/5">
              <tr>
                <th className="px-6 py-4">Subject Code</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Language</th>
                <th className="px-6 py-4">Parent Exam</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">Loading subjects...</td></tr>
              ) : subjects.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">No subjects found matching your criteria.</td></tr>
              ) : (
                subjects.map((s) => (
                  <tr key={s.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4 font-mono text-white font-medium">{s.subject_code}</td>
                    <td className="px-6 py-4 font-semibold text-slate-200">{s.subject_name}</td>
                    <td className="px-6 py-4">{s.language}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-white/5 rounded-md text-xs border border-white/5">
                        {s.exam_name}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(s.status)}`}>
                        {s.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        {canUpdate && (
                          <button
                            onClick={() => { setSelectedSubject(s); setIsUpdateModalOpen(true); }}
                            className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors"
                          >
                            Edit
                          </button>
                        )}
                        {canDelete && s.status !== "archived" && (
                          <button
                            onClick={() => { setSelectedSubject(s); setIsDeleteModalOpen(true); }}
                            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
              <h2 className="text-lg font-bold text-white">Create New Subject</h2>
              <button onClick={() => { setIsCreateModalOpen(false); reset(); }} className="text-slate-400 hover:text-white">✕</button>
            </div>
            
            <form onSubmit={handleSubmit(onCreateSubmit)} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Parent Exam</label>
                <select
                  {...register("exam_id")}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">-- Select Exam --</option>
                  {exams.map(ex => (
                    <option key={ex.id} value={ex.id}>{ex.exam_name}</option>
                  ))}
                </select>
                {errors.exam_id && <p className="text-red-400 text-xs mt-1">{errors.exam_id.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Subject Code</label>
                  <input
                    {...register("subject_code")}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none uppercase font-mono"
                    placeholder="e.g. PHY"
                  />
                  {errors.subject_code && <p className="text-red-400 text-xs mt-1">{errors.subject_code.message}</p>}
                </div>
                
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Language</label>
                  <input
                    {...register("language")}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                    placeholder="English"
                  />
                  {errors.language && <p className="text-red-400 text-xs mt-1">{errors.language.message}</p>}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Subject Name</label>
                <input
                  {...register("subject_name")}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  placeholder="Physics"
                />
                {errors.subject_name && <p className="text-red-400 text-xs mt-1">{errors.subject_name.message}</p>}
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Description (Optional)</label>
                <textarea
                  {...register("description")}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none min-h-[80px]"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => { setIsCreateModalOpen(false); reset(); }} className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors">
                  Create Subject
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {isUpdateModalOpen && selectedSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
              <h2 className="text-lg font-bold text-white">Edit Subject: {selectedSubject.subject_code}</h2>
              <button onClick={() => { setIsUpdateModalOpen(false); setSelectedSubject(null); }} className="text-slate-400 hover:text-white">✕</button>
            </div>
            
            <form onSubmit={onUpdateSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Subject Name</label>
                  <input
                    value={selectedSubject.subject_name}
                    onChange={(e) => setSelectedSubject({...selectedSubject, subject_name: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                    required minLength={2}
                  />
                </div>
                
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Language</label>
                  <input
                    value={selectedSubject.language}
                    onChange={(e) => setSelectedSubject({...selectedSubject, language: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                    required minLength={2}
                  />
                </div>
              </div>
              
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Status</label>
                <select
                  value={selectedSubject.status}
                  onChange={(e) => setSelectedSubject({...selectedSubject, status: e.target.value})}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Description (Optional)</label>
                <textarea
                  value={selectedSubject.description || ""}
                  onChange={(e) => setSelectedSubject({...selectedSubject, description: e.target.value})}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none min-h-[80px]"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setIsUpdateModalOpen(false)} className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {isDeleteModalOpen && selectedSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl">
            <div className="p-6 flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Delete Subject?</h2>
                <p className="text-sm text-slate-400 mt-2">
                  Are you sure you want to delete <span className="text-white font-bold">{selectedSubject.subject_code}</span>? This action cannot be undone.
                </p>
              </div>
              <div className="w-full flex gap-3 mt-4">
                <button onClick={() => setIsDeleteModalOpen(false)} className="flex-1 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-sm font-medium transition-colors">
                  Cancel
                </button>
                <button onClick={onDeleteConfirm} className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-bold transition-colors">
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubjectsPage;
