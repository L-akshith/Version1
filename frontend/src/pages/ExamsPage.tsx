import React, { useState, useEffect } from "react";
import api from "../services/api";
import type { Exam, ExamStatistics } from "../types";
import { 
  FileSignature, 
  Plus, 
  Search, 
  Filter, 
  Pencil,
  Trash2,
  Calendar,
  Building2,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle
} from "lucide-react";

export const ExamsPage: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [stats, setStats] = useState<ExamStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [currentExam, setCurrentExam] = useState<Exam | null>(null);
  const [formData, setFormData] = useState({
    exam_code: "",
    exam_name: "",
    conducting_authority: "",
    year: new Date().getFullYear(),
    exam_date: "",
    description: "",
    status: "draft"
  });
  const [formError, setFormError] = useState("");

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [examsRes, statsRes] = await Promise.all([
        api.get(`/exams?limit=100${statusFilter ? `&status=${statusFilter}` : ""}${search ? `&search=${search}` : ""}`),
        api.get("/exams/statistics")
      ]);
      if (examsRes.data?.success) setExams(examsRes.data.data);
      if (statsRes.data?.success) setStats(statsRes.data.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, statusFilter]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    try {
      const payload = {
        exam_code: formData.exam_code,
        exam_name: formData.exam_name,
        conducting_authority: formData.conducting_authority,
        year: Number(formData.year),
        exam_date: formData.exam_date,
        description: formData.description
      };
      await api.post("/exams", payload);
      setIsCreateModalOpen(false);
      setFormData({ ...formData, exam_code: "", exam_name: "", description: "" });
      fetchData();
    } catch (err: any) {
      setFormError(err.response?.data?.message || "Failed to create exam");
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentExam) return;
    setFormError("");
    try {
      const payload = {
        exam_name: formData.exam_name,
        conducting_authority: formData.conducting_authority,
        year: Number(formData.year),
        exam_date: formData.exam_date,
        description: formData.description,
        status: formData.status
      };
      await api.put(`/exams/${currentExam.id}`, payload);
      setIsEditModalOpen(false);
      setCurrentExam(null);
      fetchData();
    } catch (err: any) {
      setFormError(err.response?.data?.message || "Failed to update exam");
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this exam?")) return;
    try {
      await api.delete(`/exams/${id}`);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || "Failed to delete exam");
    }
  };

  const openEditModal = (exam: Exam) => {
    setCurrentExam(exam);
    setFormData({
      exam_code: exam.exam_code,
      exam_name: exam.exam_name,
      conducting_authority: exam.conducting_authority,
      year: exam.year,
      exam_date: exam.exam_date.toString(),
      description: exam.description || "",
      status: exam.status
    });
    setIsEditModalOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case "draft": return "text-gray-400 border-gray-400 bg-gray-400/10";
      case "scheduled": return "text-blue-400 border-blue-400 bg-blue-400/10";
      case "active": return "text-green-400 border-green-400 bg-green-400/10";
      case "completed": return "text-purple-400 border-purple-400 bg-purple-400/10";
      case "archived": return "text-red-400 border-red-400 bg-red-400/10";
      default: return "text-gray-400 border-gray-400 bg-gray-400/10";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Exam Management</h1>
          <p className="text-sm text-gray-400 mt-1">Manage exam lifecycles and metadata.</p>
        </div>
        <button 
          onClick={() => {
            setFormData({ ...formData, exam_code: "", exam_name: "", description: "" });
            setIsCreateModalOpen(true);
          }}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Exam
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: "Total Exams", value: stats?.total || 0, icon: FileSignature, color: "text-blue-400" },
          { label: "Draft", value: stats?.draft || 0, icon: Pencil, color: "text-gray-400" },
          { label: "Scheduled", value: stats?.scheduled || 0, icon: Calendar, color: "text-yellow-400" },
          { label: "Active", value: stats?.active || 0, icon: Clock, color: "text-green-400" },
          { label: "Completed", value: stats?.completed || 0, icon: CheckCircle2, color: "text-purple-400" }
        ].map((stat, i) => (
          <div key={i} className="glass-panel rounded-xl p-4 flex items-center gap-4">
            <div className={`p-3 rounded-lg bg-white/5 ${stat.color}`}>
              <stat.icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-gray-400 font-medium">{stat.label}</p>
              <h3 className="text-2xl font-bold text-white">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Filters and Search */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-96">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            type="text"
            placeholder="Search by exam code or name..."
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-5 h-5 text-gray-400" />
          <select 
            className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 w-full sm:w-auto"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="scheduled">Scheduled</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-xl border border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-white/5 text-gray-400 text-xs uppercase font-medium">
              <tr>
                <th className="px-6 py-4">Exam Details</th>
                <th className="px-6 py-4">Authority</th>
                <th className="px-6 py-4">Date & Year</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-blue-500 mb-2" />
                    <p className="text-gray-400">Loading exams...</p>
                  </td>
                </tr>
              ) : exams.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                    No examinations found.
                  </td>
                </tr>
              ) : (
                exams.map((exam) => (
                  <tr key={exam.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-white">{exam.exam_code}</div>
                      <div className="text-xs text-gray-400 mt-1">{exam.exam_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-500" />
                        {exam.conducting_authority}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-500" />
                        {exam.exam_date} ({exam.year})
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(exam.status)} capitalize`}>
                        {exam.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => openEditModal(exam)}
                          className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
                          title="Edit Exam"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        {exam.status !== "active" && (
                          <button 
                            onClick={() => handleDelete(exam.id)}
                            className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors"
                            title="Delete Exam"
                          >
                            <Trash2 className="w-4 h-4" />
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

      {/* Create / Edit Modal */}
      {(isCreateModalOpen || isEditModalOpen) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card w-full max-w-lg rounded-2xl border border-white/10 overflow-hidden shadow-2xl animate-fade-in">
            <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">
                {isEditModalOpen ? "Edit Examination" : "Create New Examination"}
              </h3>
              <button 
                onClick={() => { setIsCreateModalOpen(false); setIsEditModalOpen(false); }}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={isEditModalOpen ? handleEditSubmit : handleCreateSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {formError}
                </div>
              )}
              
              {!isEditModalOpen && (
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Exam Code</label>
                  <input 
                    type="text" 
                    required 
                    value={formData.exam_code}
                    onChange={(e) => setFormData({...formData, exam_code: e.target.value.toUpperCase()})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                    placeholder="e.g. NEET-2026"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Exam Name</label>
                <input 
                  type="text" 
                  required 
                  value={formData.exam_name}
                  onChange={(e) => setFormData({...formData, exam_name: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Conducting Authority</label>
                <input 
                  type="text" 
                  required 
                  value={formData.conducting_authority}
                  onChange={(e) => setFormData({...formData, conducting_authority: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Year</label>
                  <input 
                    type="number" 
                    required 
                    min={2000}
                    max={2100}
                    value={formData.year}
                    onChange={(e) => setFormData({...formData, year: parseInt(e.target.value)})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Exam Date</label>
                  <input 
                    type="date" 
                    required 
                    value={formData.exam_date}
                    onChange={(e) => setFormData({...formData, exam_date: e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none [color-scheme:dark]"
                  />
                </div>
              </div>

              {isEditModalOpen && currentExam?.status !== "archived" && (
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Status</label>
                  <select 
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value="draft">Draft</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="active">Active</option>
                    <option value="completed">Completed</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Description (Optional)</label>
                <textarea 
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none resize-none h-24"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => { setIsCreateModalOpen(false); setIsEditModalOpen(false); }}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                >
                  {isEditModalOpen ? "Save Changes" : "Create Exam"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
