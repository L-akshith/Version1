import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";
import { QuestionPaper, QuestionPaperStatistics, QuestionPaperVersion } from "../types";
import { 
  FileText, 
  Search, 
  UploadCloud, 
  Filter, 
  CheckCircle2,
  Clock,
  Archive,
  AlertCircle,
  FileCheck,
  XCircle,
  History,
  Download,
  Trash2,
  Edit
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const uploadSchema = z.object({
  subject_id: z.string().uuid("Please select a subject"),
  paper_code: z.string().min(2).max(50),
  title: z.string().min(2).max(255),
  description: z.string().max(2000).optional().or(z.literal("")),
});

type UploadFormData = z.infer<typeof uploadSchema>;

export const QuestionPapersPage: React.FC = () => {
  const { user } = useAuth();
  
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [stats, setStats] = useState<QuestionPaperStatistics>({ 
    total: 0, draft: 0, uploaded: 0, under_review: 0, approved: 0, rejected: 0, archived: 0 
  });
  const [exams, setExams] = useState<{id: string, exam_name: string}[]>([]);
  const [subjects, setSubjects] = useState<{id: string, subject_name: string, subject_code: string}[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [examFilter, setExamFilter] = useState<string>("all");
  const [subjectFilter, setSubjectFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  
  const [selectedPaper, setSelectedPaper] = useState<QuestionPaper | null>(null);
  const [versions, setVersions] = useState<QuestionPaperVersion[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Permissions
  const canCreate = user?.is_superuser || ["Admin", "Controller", "Question Setter"].includes(user?.role_name || "");
  const canUpdate = user?.is_superuser || ["Admin", "Controller", "Question Setter", "Translation Officer"].includes(user?.role_name || "");
  const canDelete = user?.is_superuser || ["Admin"].includes(user?.role_name || "");

  const { register, handleSubmit, reset, formState: { errors }, watch } = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema)
  });

  const uploadExamId = watch("exam_id" as any); // Temporary watch for cascading dropdown in modal

  const fetchData = async () => {
    setLoading(true);
    try {
      const statsRes = await api.get("/question-papers/statistics");
      if (statsRes.data.success) {
        setStats(statsRes.data.data);
      }

      const examsRes = await api.get("/exams?limit=100");
      if (examsRes.data.success) {
        setExams(examsRes.data.data);
      }

      // Fetch subjects for filter based on selected exam
      if (examFilter !== "all") {
        const subRes = await api.get(`/exams/${examFilter}/subjects?limit=100`);
        if (subRes.data.success) setSubjects(subRes.data.data);
      } else {
        setSubjects([]);
        setSubjectFilter("all");
      }

      let url = `/question-papers?limit=100`;
      if (statusFilter !== "all") url += `&status=${statusFilter}`;
      if (subjectFilter !== "all") url += `&subject_id=${subjectFilter}`;
      if (searchQuery) url += `&search=${searchQuery}`;
      
      const res = await api.get(url);
      if (res.data.success) {
        setPapers(res.data.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load question papers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter, examFilter, subjectFilter, searchQuery]);

  // Load subjects for the upload modal when exam changes
  const [modalSubjects, setModalSubjects] = useState<{id: string, subject_name: string}[]>([]);
  useEffect(() => {
    if (uploadExamId) {
      api.get(`/exams/${uploadExamId}/subjects?limit=100`).then(res => {
        if (res.data.success) setModalSubjects(res.data.data);
      });
    } else {
      setModalSubjects([]);
    }
  }, [uploadExamId]);

  const onUploadSubmit = async (data: UploadFormData) => {
    if (!selectedFile) {
      alert("Please select a PDF file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("subject_id", data.subject_id);
    formData.append("paper_code", data.paper_code);
    formData.append("title", data.title);
    if (data.description) formData.append("description", data.description);
    formData.append("file", selectedFile);

    try {
      await api.post("/question-papers/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setIsUploadModalOpen(false);
      reset();
      setSelectedFile(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || err.response?.data?.detail || "Upload failed");
    }
  };

  const onDeleteConfirm = async () => {
    if (!selectedPaper) return;
    try {
      await api.delete(`/question-papers/${selectedPaper.id}`);
      setIsDeleteModalOpen(false);
      setSelectedPaper(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || "Failed to delete question paper");
    }
  };

  const onUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPaper) return;
    
    try {
      await api.put(`/question-papers/${selectedPaper.id}`, {
        title: selectedPaper.title,
        description: selectedPaper.description,
        status: selectedPaper.status,
      });
      setIsUpdateModalOpen(false);
      setSelectedPaper(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.message || "Failed to update question paper");
    }
  };

  const openHistory = async (paper: QuestionPaper) => {
    setSelectedPaper(paper);
    try {
      const res = await api.get(`/question-papers/${paper.id}/versions`);
      if (res.data.success) {
        setVersions(res.data.data);
        setIsHistoryModalOpen(true);
      }
    } catch (err: any) {
      alert("Failed to load version history");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      case "draft": return "text-slate-400 bg-slate-500/10 border-slate-500/20";
      case "uploaded": return "text-blue-400 bg-blue-500/10 border-blue-500/20";
      case "under_review": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      case "rejected": return "text-red-400 bg-red-500/10 border-red-500/20";
      case "archived": return "text-gray-400 bg-gray-500/10 border-gray-500/20";
      default: return "text-indigo-400 bg-indigo-500/10 border-indigo-500/20";
    }
  };

  const statCards = [
    { title: "Total Papers", value: stats.total, icon: FileText, color: "text-blue-400", bg: "bg-blue-500/5" },
    { title: "Uploaded", value: stats.uploaded, icon: UploadCloud, color: "text-indigo-400", bg: "bg-indigo-500/5" },
    { title: "In Review", value: stats.under_review, icon: Clock, color: "text-amber-400", bg: "bg-amber-500/5" },
    { title: "Approved", value: stats.approved, icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/5" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header & Stats */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Question Papers</h1>
          <p className="text-sm text-slate-400 mt-1">Upload, version, and manage examination question papers.</p>
        </div>
        {canCreate && (
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-colors shadow-lg shadow-indigo-500/20"
          >
            <UploadCloud className="w-4 h-4" />
            Upload Paper
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
                placeholder="Search paper code or title..."
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
                <option value="uploaded">Uploaded</option>
                <option value="under_review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            
            <select
                value={examFilter}
                onChange={(e) => setExamFilter(e.target.value)}
                className="px-4 py-2 bg-slate-950/50 border border-white/10 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500 max-w-[150px] truncate"
              >
                <option value="all">All Exams</option>
                {exams.map(ex => (
                  <option key={ex.id} value={ex.id}>{ex.exam_name}</option>
                ))}
            </select>
            
            {examFilter !== "all" && (
                <select
                value={subjectFilter}
                onChange={(e) => setSubjectFilter(e.target.value)}
                className="px-4 py-2 bg-slate-950/50 border border-white/10 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500 max-w-[150px] truncate"
              >
                <option value="all">All Subjects</option>
                {subjects.map(s => (
                  <option key={s.id} value={s.id}>{s.subject_name}</option>
                ))}
              </select>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-900/80 text-slate-400 font-semibold border-b border-white/5">
              <tr>
                <th className="px-6 py-4">Paper Code</th>
                <th className="px-6 py-4">Title</th>
                <th className="px-6 py-4">Context</th>
                <th className="px-6 py-4">Hash (SHA-256)</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">Loading papers...</td></tr>
              ) : papers.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">No question papers found.</td></tr>
              ) : (
                papers.map((p) => (
                  <tr key={p.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="font-mono text-white font-medium">{p.paper_code}</span>
                        <span className="text-[10px] text-slate-500 font-bold tracking-wider mt-0.5">VERSION {p.version}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-200">{p.title}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <span className="px-2 py-0.5 bg-white/5 rounded-md text-[10px] border border-white/5 truncate max-w-[150px]" title={p.exam_name || ""}>
                          {p.exam_name}
                        </span>
                        <span className="px-2 py-0.5 bg-white/5 rounded-md text-[10px] border border-white/5 truncate max-w-[150px]" title={p.subject_name || ""}>
                          {p.subject_name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                        <span className="font-mono text-[10px] text-slate-400" title={p.sha256_hash}>
                          {p.sha256_hash.substring(0, 12)}...
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(p.status)}`}>
                        {p.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => openHistory(p)}
                          className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors"
                          title="Version History"
                        >
                          <History className="w-4 h-4" />
                        </button>
                        {canUpdate && (
                          <button
                            onClick={() => { setSelectedPaper(p); setIsUpdateModalOpen(true); }}
                            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                            title="Edit Metadata"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
                        {canDelete && p.status !== "approved" && p.status !== "archived" && (
                          <button
                            onClick={() => { setSelectedPaper(p); setIsDeleteModalOpen(true); }}
                            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                            title="Delete Paper"
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

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-indigo-400" />
                Upload Question Paper
              </h2>
              <button onClick={() => { setIsUploadModalOpen(false); reset(); setSelectedFile(null); }} className="text-slate-400 hover:text-white">✕</button>
            </div>
            
            <form onSubmit={handleSubmit(onUploadSubmit)} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Exam</label>
                  <select
                    {...register("exam_id" as any)}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">-- Select Exam --</option>
                    {exams.map(ex => (
                      <option key={ex.id} value={ex.id}>{ex.exam_name}</option>
                    ))}
                  </select>
                </div>
                
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Subject</label>
                  <select
                    {...register("subject_id")}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                    disabled={!uploadExamId}
                  >
                    <option value="">-- Select Subject --</option>
                    {modalSubjects.map(s => (
                      <option key={s.id} value={s.id}>{s.subject_name}</option>
                    ))}
                  </select>
                  {errors.subject_id && <p className="text-red-400 text-xs mt-1">{errors.subject_id.message}</p>}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Paper Code</label>
                  <input
                    {...register("paper_code")}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none uppercase font-mono"
                    placeholder="e.g. PHY-SET-A"
                  />
                  {errors.paper_code && <p className="text-red-400 text-xs mt-1">{errors.paper_code.message}</p>}
                  <p className="text-[10px] text-slate-500 mt-1">If code exists, version will increment.</p>
                </div>
                
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400 uppercase">Title</label>
                  <input
                    {...register("title")}
                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                    placeholder="Physics Set A"
                  />
                  {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title.message}</p>}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">PDF File</label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-700 border-dashed rounded-lg hover:border-indigo-500 transition-colors bg-slate-900/50">
                  <div className="space-y-1 text-center">
                    <FileText className="mx-auto h-10 w-10 text-slate-500" />
                    <div className="flex text-sm text-slate-400">
                      <label className="relative cursor-pointer bg-transparent rounded-md font-medium text-indigo-400 hover:text-indigo-300 focus-within:outline-none">
                        <span>Upload a file</span>
                        <input 
                          type="file" 
                          className="sr-only" 
                          accept=".pdf,application/pdf"
                          onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                              setSelectedFile(e.target.files[0]);
                            }
                          }}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-slate-500">
                      {selectedFile ? (
                        <span className="text-emerald-400 font-semibold">{selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                      ) : (
                        "PDF up to 50MB"
                      )}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Description (Optional)</label>
                <textarea
                  {...register("description")}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none min-h-[60px]"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => { setIsUploadModalOpen(false); reset(); setSelectedFile(null); }} className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors flex items-center gap-2">
                  <UploadCloud className="w-4 h-4" />
                  Upload Securely
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {isUpdateModalOpen && selectedPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
              <h2 className="text-lg font-bold text-white">Edit Paper: {selectedPaper.paper_code} (v{selectedPaper.version})</h2>
              <button onClick={() => { setIsUpdateModalOpen(false); setSelectedPaper(null); }} className="text-slate-400 hover:text-white">✕</button>
            </div>
            
            <form onSubmit={onUpdateSubmit} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Title</label>
                <input
                  value={selectedPaper.title}
                  onChange={(e) => setSelectedPaper({...selectedPaper, title: e.target.value})}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  required minLength={2}
                />
              </div>
              
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Status</label>
                <select
                  value={selectedPaper.status}
                  onChange={(e) => setSelectedPaper({...selectedPaper, status: e.target.value})}
                  className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="draft">Draft</option>
                  <option value="uploaded">Uploaded</option>
                  <option value="under_review">Under Review</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="archived">Archived</option>
                </select>
                <p className="text-[10px] text-amber-500 mt-1">Warning: Invalid transitions will be rejected by the server.</p>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400 uppercase">Description</label>
                <textarea
                  value={selectedPaper.description || ""}
                  onChange={(e) => setSelectedPaper({...selectedPaper, description: e.target.value})}
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

      {/* History Modal */}
      {isHistoryModalOpen && selectedPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[80vh]">
            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-slate-900">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-indigo-400" />
                  Version History
                </h2>
                <p className="text-xs text-slate-400 mt-1">{selectedPaper.paper_code} — {selectedPaper.subject_name}</p>
              </div>
              <button onClick={() => { setIsHistoryModalOpen(false); setSelectedPaper(null); }} className="text-slate-400 hover:text-white">✕</button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              <div className="space-y-4">
                {versions.map((v, idx) => (
                  <div key={v.id} className="relative flex gap-4 p-4 rounded-xl border border-white/10 bg-slate-950/50">
                    <div className="flex flex-col items-center justify-center w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 shrink-0">
                      <span className="text-xs text-indigo-400 font-bold uppercase">Ver</span>
                      <span className="text-lg text-indigo-300 font-black">{v.version}</span>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="text-sm font-bold text-slate-200">{v.original_file_name}</h4>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(v.status)}`}>
                          {v.status.replace("_", " ")}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-y-1 gap-x-4 mt-2">
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                          <span className="font-mono text-[10px] truncate" title={v.sha256_hash}>
                            SHA256: {v.sha256_hash.substring(0, 16)}...
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <FileText className="w-3.5 h-3.5 text-slate-500" />
                          <span>{(v.file_size / 1024).toFixed(1)} KB</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>{new Date(v.upload_time).toLocaleString()}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <span className="w-3.5 h-3.5 rounded-full bg-slate-700 flex items-center justify-center text-[8px] text-white">
                            {v.uploader_name ? v.uploader_name.charAt(0) : "?"}
                          </span>
                          <span className="truncate">{v.uploader_name || "Unknown"}</span>
                        </div>
                      </div>
                    </div>
                    
                    {idx === 0 && (
                      <div className="absolute -top-2 -right-2">
                        <span className="bg-emerald-500 text-white text-[9px] font-bold px-2 py-0.5 rounded-full shadow-lg">LATEST</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {isDeleteModalOpen && selectedPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl">
            <div className="p-6 flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Delete Question Paper?</h2>
                <p className="text-sm text-slate-400 mt-2">
                  Are you sure you want to delete <span className="text-white font-bold">{selectedPaper.paper_code} (v{selectedPaper.version})</span>? This will permanently remove the file and cannot be undone.
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

export default QuestionPapersPage;
