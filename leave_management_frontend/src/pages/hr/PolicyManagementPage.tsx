// pages/hr/PolicyManagementPage.tsx
import React, { useState, useEffect, type JSX } from 'react';
import { Upload, FileText, Trash2, Eye, AlertCircle, CheckCircle, XCircle, Search, Shield } from 'lucide-react';
import { hrApi, type CompanyPolicy, type PolicyStats, type PolicyQueryResult, type PolicyDetails } from '../../api/endpoints/hr.api';

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
    fetchPolicies();
    fetchStats();
  }, []);

  const fetchPolicies = async () => {
    try {
      const data = await hrApi.getAllPolicies();
      setPolicies(data);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch policies:', error);
      setError('Failed to load policies');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await hrApi.getPolicyStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(file.type)) {
        alert('Only PDF, DOCX, and TXT files are allowed');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const result = await hrApi.uploadPolicy(selectedFile, policyType);
      alert(`Policy uploaded successfully! ${result.chunks_created} chunks created.`);
      setSelectedFile(null);
      fetchPolicies();
      fetchStats();
    } catch (error: any) {
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (policyId: number) => {
    if (!confirm('Are you sure you want to delete this policy?')) return;

    try {
      await hrApi.deletePolicy(policyId);
      alert('Policy deleted successfully');
      fetchPolicies();
      fetchStats();
    } catch (error) {
      alert('Failed to delete policy');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      const data = await hrApi.queryPolicies(searchQuery, 5);
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const viewPolicyDetails = async (policyId: number) => {
    try {
      const data = await hrApi.getPolicyDetails(policyId);
      setSelectedPolicy(data);
    } catch (error) {
      console.error('Failed to fetch policy details:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, JSX.Element> = {
      COMPLETED: <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs flex items-center gap-1"><CheckCircle className="w-3 h-3" />Completed</span>,
      PROCESSING: <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">Processing...</span>,
      FAILED: <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs flex items-center gap-1"><XCircle className="w-3 h-3" />Failed</span>,
      PENDING: <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">Pending</span>
    };
    return badges[status] || badges.PENDING;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-8 h-8 text-blue-600" />
            Policy Management
          </h1>
          <p className="text-gray-600 mt-1">Upload and manage company policies</p>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Policies</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_policies}</p>
              </div>
              <FileText className="w-10 h-10 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Active Policies</p>
                <p className="text-2xl font-bold text-green-600">{stats.active_policies}</p>
              </div>
              <CheckCircle className="w-10 h-10 text-green-500" />
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Policy Types</p>
                <p className="text-2xl font-bold text-gray-900">{stats.policy_types?.length || 0}</p>
              </div>
              <FileText className="w-10 h-10 text-purple-500" />
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Chunks</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_chunks}</p>
              </div>
              <FileText className="w-10 h-10 text-orange-500" />
            </div>
          </div>
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload New Policy
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Policy Type
            </label>
            <select
              value={policyType}
              onChange={(e) => setPolicyType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="LEAVE">Leave Policy</option>
              <option value="GENERAL">General Policy</option>
              <option value="ATTENDANCE">Attendance Policy</option>
              <option value="CODE_OF_CONDUCT">Code of Conduct</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File (PDF, DOCX, TXT - Max 10MB)
            </label>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={handleFileSelect}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploading...' : 'Upload Policy'}
          </button>
        </div>
      </div>

      {/* Policy Search */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Search className="w-5 h-5" />
          Search Policies
        </h2>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for policy information..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <button
            onClick={handleSearch}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="mt-4 space-y-3">
            <h3 className="font-medium text-gray-900">Search Results:</h3>
            {searchResults.map((result, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-gray-900">{result.section_title || 'Policy Section'}</h4>
                  <span className="text-xs text-gray-500">
                    Relevance: {(result.similarity * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm text-gray-700">{result.content}</p>
                <p className="text-xs text-gray-500 mt-2">From: {result.policy_name}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Policies List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">All Policies</h2>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading policies...</div>
        ) : policies.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p>No policies uploaded yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Upload Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Active</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {policies.map((policy) => (
                  <tr key={policy.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{policy.filename}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{policy.policy_type}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(policy.upload_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(policy.embedding_status)}</td>
                    <td className="px-6 py-4">
                      {policy.is_active ? (
                        <span className="text-green-600 font-medium">Yes</span>
                      ) : (
                        <span className="text-gray-400">No</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => viewPolicyDetails(policy.id)}
                          className="text-blue-600 hover:text-blue-800"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(policy.id)}
                          className="text-red-600 hover:text-red-800"
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold">{selectedPolicy.filename}</h3>
              <button
                onClick={() => setSelectedPolicy(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-600">Policy Type:</label>
                <p className="text-gray-900">{selectedPolicy.policy_type}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Upload Date:</label>
                <p className="text-gray-900">{new Date(selectedPolicy.upload_date).toLocaleString()}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Total Chunks:</label>
                <p className="text-gray-900">{selectedPolicy.chunks_count}</p>
              </div>
              {selectedPolicy.preview && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Preview:</label>
                  <p className="text-gray-700 text-sm mt-1 p-3 bg-gray-50 rounded">{selectedPolicy.preview}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyManagementPage;