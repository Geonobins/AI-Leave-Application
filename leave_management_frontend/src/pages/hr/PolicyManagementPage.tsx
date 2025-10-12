import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, Eye, AlertCircle, CheckCircle, XCircle, Search, Shield, TrendingUp } from 'lucide-react';

// Mock API types
interface CompanyPolicy {
  id: number;
  filename: string;
  policy_type: string;
  upload_date: string;
  embedding_status: string;
  is_active: boolean;
}

interface PolicyStats {
  total_policies: number;
  active_policies: number;
  policy_types: string[];
  total_chunks: number;
}

interface PolicyQueryResult {
  section_title?: string;
  content: string;
  similarity: number;
  policy_name: string;
}

interface PolicyDetails {
  id: number;
  filename: string;
  policy_type: string;
  upload_date: string;
  chunks_count: number;
  preview?: string;
}

const PolicyManagementPage: React.FC = () => {
  const [policies, setPolicies] = useState<CompanyPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [policyType, setPolicyType] = useState('LEAVE');
  const [stats, setStats] = useState<PolicyStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PolicyQueryResult[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading
    setTimeout(() => {
      setPolicies([
        {
          id: 1,
          filename: 'Company_Leave_Policy.pdf',
          policy_type: 'LEAVE',
          upload_date: '2025-01-15T10:30:00Z',
          embedding_status: 'COMPLETED',
          is_active: true
        },
        {
          id: 2,
          filename: 'Code_of_Conduct_2025.docx',
          policy_type: 'CODE_OF_CONDUCT',
          upload_date: '2025-02-01T14:20:00Z',
          embedding_status: 'COMPLETED',
          is_active: true
        }
      ]);
      setStats({
        total_policies: 2,
        active_policies: 2,
        policy_types: ['LEAVE', 'CODE_OF_CONDUCT'],
        total_chunks: 156
      });
      setLoading(false);
    }, 1000);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(file.type)) {
        setError('Only PDF, DOCX, and TXT files are allowed');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setTimeout(() => {
      setUploading(false);
      setSelectedFile(null);
      setError(null);
    }, 2000);
  };

  const handleDelete = async (policyId: number) => {
    setPolicies(policies.filter(p => p.id !== policyId));
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchResults([
      {
        section_title: 'Annual Leave Policy',
        content: 'Full-time employees are entitled to 21 days of annual leave per year. Employees with 5+ years of service receive 25 days per year.',
        similarity: 0.92,
        policy_name: 'Company_Leave_Policy.pdf'
      }
    ]);
  };

  const viewPolicyDetails = async (policyId: number) => {
    setSelectedPolicy({
      id: policyId,
      filename: 'Company_Leave_Policy.pdf',
      policy_type: 'LEAVE',
      upload_date: '2025-01-15T10:30:00Z',
      chunks_count: 78,
      preview: 'This document outlines the company leave policy including annual leave, sick leave, casual leave...'
    });
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, React.ReactNode> = {
      COMPLETED: (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-950/20 border border-emerald-900/30 rounded-full">
          <CheckCircle className="w-3 h-3 text-emerald-400/70" />
          <span className="text-xs font-light text-emerald-300/80">Completed</span>
        </div>
      ),
      PROCESSING: (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-950/20 border border-amber-900/30 rounded-full">
          <div className="w-3 h-3 border-2 border-amber-400/30 border-t-amber-400/70 rounded-full animate-spin" />
          <span className="text-xs font-light text-amber-300/80">Processing</span>
        </div>
      ),
      FAILED: (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-950/20 border border-red-900/30 rounded-full">
          <XCircle className="w-3 h-3 text-red-400/70" />
          <span className="text-xs font-light text-red-300/80">Failed</span>
        </div>
      ),
      PENDING: (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-white/10 rounded-full">
          <span className="text-xs font-light text-white/60">Pending</span>
        </div>
      )
    };
    return badges[status] || badges.PENDING;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-8">
      <div className='h-[80px]'>

      </div>
      {/* Animated background */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.03),transparent_50%)] pointer-events-none" />
      
      <div className="relative max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-6 md:p-8 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-2xl">
              <Shield className="w-8 h-8 text-white/80" />
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-light text-white tracking-wide">Policy Management</h1>
              <p className="text-white/60 text-sm md:text-base font-light mt-1">Upload and manage company policies</p>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="backdrop-blur-xl bg-red-950/20 border border-red-900/30 rounded-2xl p-4 flex items-center gap-3 shadow-lg">
            <AlertCircle className="w-5 h-5 text-red-400/70 flex-shrink-0" />
            <span className="text-red-300/80 text-sm font-light">{error}</span>
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl hover:bg-white/8 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl" />
              <div className="relative flex items-center justify-between">
                <div>
                  <p className="text-white/50 text-xs font-light tracking-wider uppercase mb-2">Total Policies</p>
                  <p className="text-3xl font-light text-white">{stats.total_policies}</p>
                </div>
                <FileText className="w-10 h-10 text-blue-400/60" />
              </div>
            </div>

            <div className="relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl hover:bg-white/8 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-2xl" />
              <div className="relative flex items-center justify-between">
                <div>
                  <p className="text-white/50 text-xs font-light tracking-wider uppercase mb-2">Active Policies</p>
                  <p className="text-3xl font-light text-white">{stats.active_policies}</p>
                </div>
                <CheckCircle className="w-10 h-10 text-emerald-400/60" />
              </div>
            </div>

            <div className="relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl hover:bg-white/8 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent rounded-2xl" />
              <div className="relative flex items-center justify-between">
                <div>
                  <p className="text-white/50 text-xs font-light tracking-wider uppercase mb-2">Policy Types</p>
                  <p className="text-3xl font-light text-white">{stats.policy_types?.length || 0}</p>
                </div>
                <TrendingUp className="w-10 h-10 text-purple-400/60" />
              </div>
            </div>

            <div className="relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl hover:bg-white/8 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent rounded-2xl" />
              <div className="relative flex items-center justify-between">
                <div>
                  <p className="text-white/50 text-xs font-light tracking-wider uppercase mb-2">Total Chunks</p>
                  <p className="text-3xl font-light text-white">{stats.total_chunks}</p>
                </div>
                <FileText className="w-10 h-10 text-orange-400/60" />
              </div>
            </div>
          </div>
        )}

        {/* Upload Section */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-6 md:p-8 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <Upload className="w-5 h-5 text-white/80" />
            <h2 className="text-xl md:text-2xl font-light text-white tracking-wide">Upload New Policy</h2>
          </div>
          
          <div className="space-y-5">
            <div>
              <label className="block text-xs font-light text-white/50 mb-3 uppercase tracking-wider">
                Policy Type
              </label>
              <select
                value={policyType}
                onChange={(e) => setPolicyType(e.target.value)}
                className="w-full px-4 py-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl text-white text-sm font-light focus:border-white/30 focus:outline-none transition-all"
              >
                <option value="LEAVE" className="bg-slate-800">Leave Policy</option>
                <option value="GENERAL" className="bg-slate-800">General Policy</option>
                <option value="ATTENDANCE" className="bg-slate-800">Attendance Policy</option>
                <option value="CODE_OF_CONDUCT" className="bg-slate-800">Code of Conduct</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-light text-white/50 mb-3 uppercase tracking-wider">
                Select File (PDF, DOCX, TXT - Max 10MB)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileSelect}
                  className="w-full px-4 py-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl text-white text-sm font-light focus:border-white/30 focus:outline-none transition-all file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-white/10 file:text-white/70 file:text-xs file:font-light hover:file:bg-white/15"
                />
              </div>
              {selectedFile && (
                <p className="mt-3 text-sm text-white/60 font-light">
                  Selected: <span className="text-white/80">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(2)} KB)
                </p>
              )}
            </div>

            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className="px-6 py-3 bg-white/10 backdrop-blur-md text-white rounded-xl text-sm font-light border border-white/20 hover:bg-white/15 hover:border-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 shadow-lg flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload Policy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Policy Search */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-6 md:p-8 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <Search className="w-5 h-5 text-white/80" />
            <h2 className="text-xl md:text-2xl font-light text-white tracking-wide">Search Policies</h2>
          </div>
          
          <div className="flex gap-3">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search for policy information..."
              className="flex-1 px-4 py-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl text-white text-sm font-light placeholder-white/30 focus:border-white/30 focus:outline-none transition-all"
            />
            <button
              onClick={handleSearch}
              className="px-6 py-3 bg-white/10 backdrop-blur-md text-white rounded-xl text-sm font-light border border-white/20 hover:bg-white/15 hover:border-white/30 transition-all duration-300 shadow-lg"
            >
              Search
            </button>
          </div>

          {searchResults.length > 0 && (
            <div className="mt-6 space-y-4">
              <h3 className="text-sm font-light text-white/60 uppercase tracking-wider">Search Results</h3>
              {searchResults.map((result, idx) => (
                <div key={idx} className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/8 transition-all duration-300">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-light text-white">{result.section_title || 'Policy Section'}</h4>
                    <span className="text-xs text-white/40 font-light">
                      {(result.similarity * 100).toFixed(1)}% match
                    </span>
                  </div>
                  <p className="text-sm text-white/70 font-light leading-relaxed mb-3">{result.content}</p>
                  <p className="text-xs text-white/40 font-light">From: {result.policy_name}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Policies List */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl shadow-2xl overflow-hidden">
          <div className="p-6 md:p-8 border-b border-white/10">
            <h2 className="text-xl md:text-2xl font-light text-white tracking-wide">All Policies</h2>
          </div>
          
          {loading ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-white/40 text-sm font-light">Loading policies...</p>
            </div>
          ) : policies.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-white/20" />
              <p className="text-white/40 text-sm font-light">No policies uploaded yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5 border-b border-white/10">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-light text-white/50 uppercase tracking-wider">Filename</th>
                    <th className="px-6 py-4 text-left text-xs font-light text-white/50 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-4 text-left text-xs font-light text-white/50 uppercase tracking-wider">Upload Date</th>
                    <th className="px-6 py-4 text-left text-xs font-light text-white/50 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-light text-white/50 uppercase tracking-wider">Active</th>
                    <th className="px-6 py-4 text-left text-xs font-light text-white/50 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {policies.map((policy) => (
                    <tr key={policy.id} className="hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 text-sm text-white font-light">{policy.filename}</td>
                      <td className="px-6 py-4 text-sm text-white/60 font-light">{policy.policy_type}</td>
                      <td className="px-6 py-4 text-sm text-white/60 font-light">
                        {new Date(policy.upload_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">{getStatusBadge(policy.embedding_status)}</td>
                      <td className="px-6 py-4">
                        {policy.is_active ? (
                          <span className="text-emerald-400/70 font-light text-sm">Active</span>
                        ) : (
                          <span className="text-white/30 font-light text-sm">Inactive</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-3">
                          <button
                            onClick={() => viewPolicyDetails(policy.id)}
                            className="text-white/60 hover:text-white transition-colors"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(policy.id)}
                            className="text-red-400/60 hover:text-red-400 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Policy Details Modal */}
        {selectedPolicy && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="backdrop-blur-xl bg-slate-900/95 border border-white/10 rounded-3xl p-6 md:p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl">
              <div className="flex justify-between items-start mb-6">
                <h3 className="text-2xl font-light text-white tracking-wide">{selectedPolicy.filename}</h3>
                <button
                  onClick={() => setSelectedPolicy(null)}
                  className="text-white/40 hover:text-white text-3xl font-light leading-none transition-colors"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-5">
                <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-4">
                  <label className="text-xs font-light text-white/40 uppercase tracking-wider block mb-2">Policy Type</label>
                  <p className="text-white font-light">{selectedPolicy.policy_type}</p>
                </div>
                <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-4">
                  <label className="text-xs font-light text-white/40 uppercase tracking-wider block mb-2">Upload Date</label>
                  <p className="text-white font-light">{new Date(selectedPolicy.upload_date).toLocaleString()}</p>
                </div>
                <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-4">
                  <label className="text-xs font-light text-white/40 uppercase tracking-wider block mb-2">Total Chunks</label>
                  <p className="text-white font-light">{selectedPolicy.chunks_count}</p>
                </div>
                {selectedPolicy.preview && (
                  <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-4">
                    <label className="text-xs font-light text-white/40 uppercase tracking-wider block mb-2">Preview</label>
                    <p className="text-white/70 text-sm font-light leading-relaxed">{selectedPolicy.preview}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PolicyManagementPage;