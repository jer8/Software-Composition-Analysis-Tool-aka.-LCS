import React, { useState } from 'react';
import { Upload, Github, Search, AlertCircle, CheckCircle, XCircle, FileText, BarChart3, Shield } from 'lucide-react';

const LicenseScanner = () => {
  const [activeTab, setActiveTab] = useState('scan');
  const [scanType, setScanType] = useState('github');
  const [repoUrl, setRepoUrl] = useState('');
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleScan = async () => {
    setScanning(true);
    setResults(null); // Clear previous results

    const API_BASE_URL = 'http://127.0.0.1:8000';
    let endpoint = '';
    let options = {};

    try {
      // Configure request based on scan type
      if (scanType === 'github') {
        endpoint = `${API_BASE_URL}/scan/github`;
        options = {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ repo_url: repoUrl }),
        };
      } else if (scanType === 'upload') {
        const formData = new FormData();
        uploadedFiles.forEach(file => {
          formData.append('files', file);
        });

        endpoint = `${API_BASE_URL}/scan/upload`;
        options = {
          method: 'POST',
          body: formData,
        };
      }

      const response = await fetch(endpoint, options);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An API error occurred.');
      }

      const data = await response.json();
      setResults(data);
      setActiveTab('results');

    } catch (error) {
      console.error('Scan failed:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setScanning(false);
    }
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    setUploadedFiles(files);
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'high': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'low': return '✓ Low Risk';
      case 'medium': return '⚠ Medium Risk';
      case 'high': return '✗ High Risk';
      default: return '? Unknown';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="w-12 h-12 text-indigo-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">License Compliance Scanner</h1>
          </div>
          <p className="text-lg text-gray-600">
            Automatically detect and analyze licenses across all your dependencies
          </p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-6">
          <div className="bg-white rounded-lg shadow-md p-1 inline-flex">
            <button
              onClick={() => setActiveTab('scan')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${activeTab === 'scan'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              <Search className="w-4 h-4 inline mr-2" />
              Scan Project
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${activeTab === 'results'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
              disabled={!results}
            >
              <BarChart3 className="w-4 h-4 inline mr-2" />
              Results
            </button>
          </div>
        </div>

        {/* Scan Tab */}
        {activeTab === 'scan' && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Start New Scan</h2>
            
            {/* Scan Type Selector */}
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setScanType('github')}
                className={`flex-1 p-4 rounded-lg border-2 transition-all ${scanType === 'github'
                    ? 'border-indigo-600 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }`}
              >
                <Github className="w-8 h-8 mx-auto mb-2 text-gray-700" />
                <div className="font-semibold">GitHub Repository</div>
                <div className="text-sm text-gray-600">Scan from repo URL</div>
              </button>
              
              <button
                onClick={() => setScanType('upload')}
                className={`flex-1 p-4 rounded-lg border-2 transition-all ${scanType === 'upload'
                    ? 'border-indigo-600 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }`}
              >
                <Upload className="w-8 h-8 mx-auto mb-2 text-gray-700" />
                <div className="font-semibold">Upload Files</div>
                <div className="text-sm text-gray-600">Upload manifest files</div>
              </button>
            </div>

            {/* GitHub Input */}
            {scanType === 'github' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Repository URL
                  </label>
                  <input
                    type="text"
                    placeholder="https://github.com/username/repository"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                  />
                </div>
                
                <button
                  onClick={handleScan}
                  disabled={!repoUrl || scanning}
                  className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {scanning ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Scanning...
                    </span>
                  ) : (
                    'Start Scan'
                  )}
                </button>
              </div>
            )}

            {/* File Upload */}
            {scanType === 'upload' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload Dependency Files
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors">
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <input
                      type="file"
                      multiple
                      onChange={handleFileUpload}
                      className="hidden"
                      id="file-upload"
                      accept=".json,.txt,.xml,.toml,.lock,.gradle"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="text-indigo-600 font-semibold">Click to upload</span>
                      <span className="text-gray-600"> or drag and drop</span>
                    </label>
                    <p className="text-sm text-gray-500 mt-2">
                      package.json, requirements.txt, pom.xml, Cargo.toml, go.mod, etc.
                    </p>
                  </div>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold mb-2">Uploaded Files:</h3>
                    <ul className="space-y-1">
                      {uploadedFiles.map((file, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-center">
                          <FileText className="w-4 h-4 mr-2 text-gray-500" />
                          {file.name}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  onClick={handleScan}
                  disabled={uploadedFiles.length === 0 || scanning}
                  className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {scanning ? 'Scanning...' : 'Analyze Files'}
                </button>
              </div>
            )}

            {/* Supported Languages */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-3">Supported Languages:</h3>
              <div className="flex flex-wrap gap-2">
                {['JavaScript', 'Python', 'Java', 'Rust', 'Go', 'Ruby', '.NET', 'PHP'].map(lang => (
                  <span key={lang} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && results && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-gray-600 text-sm font-medium mb-1">Total Dependencies</div>
                <div className="text-3xl font-bold text-gray-900">{results.total_dependencies}</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-gray-600 text-sm font-medium mb-1">Unique Licenses</div>
                <div className="text-3xl font-bold text-gray-900">{results.unique_licenses}</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-gray-600 text-sm font-medium mb-1">Languages</div>
                <div className="text-3xl font-bold text-gray-900">{results.languages.length}</div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-gray-600 text-sm font-medium mb-1">Risk Level</div>
                <div className={`text-2xl font-bold ${
                  results.risk_level === 'low' ? 'text-green-600' :
                  results.risk_level === 'medium' ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {results.risk_level.toUpperCase()}
                </div>
              </div>
            </div>

            {/* Issues */}
            {results.issues.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                  <AlertCircle className="w-6 h-6 mr-2 text-red-600" />
                  Critical Issues
                </h3>
                <div className="space-y-4">
                  {results.issues.map((issue, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border-l-4 ${
                      issue.severity === 'high' ? 'border-red-500 bg-red-50' :
                      issue.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                      'border-blue-500 bg-blue-50'
                    }`}>
                      <div className="flex items-start">
                        {issue.severity === 'high' ?
                          <XCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5" /> :
                          <AlertCircle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
                        }
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900">{issue.title}</div>
                          <div className="text-sm text-gray-700 mt-1">
                            Package: <code className="bg-white px-2 py-0.5 rounded">{issue.package}</code>
                          </div>
                          <div className="text-sm text-gray-600 mt-2">{issue.description}</div>
                          <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                            <div className="text-sm font-medium text-gray-700">💡 Recommendation:</div>
                            <div className="text-sm text-gray-600 mt-1">{issue.recommendation}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* License Distribution */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">License Distribution</h3>
              <div className="space-y-3">
                {Object.entries(results.license_distribution).map(([license, count]) => {
                  const percentage = ((count / results.total_dependencies) * 100).toFixed(1);
                  const isRisky = license.includes('GPL') || license === 'Unknown';
                  return (
                    <div key={license}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700">{license}</span>
                        <span className="text-gray-600">{count} ({percentage}%)</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            isRisky ? 'bg-red-500' : 'bg-indigo-600'
                          }`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Dependencies Table */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">All Dependencies</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Package</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Version</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">License</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Language</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.dependencies.map((dep, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 font-medium text-gray-900">{dep.name}</td>
                        <td className="py-3 px-4 text-gray-600">{dep.version}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                            {dep.license}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-600">{dep.language}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-sm font-medium ${getRiskColor(dep.risk)}`}>
                            {getRiskBadge(dep.risk)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Export Button */}
            <div className="flex justify-center">
              <button className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Export Report (PDF)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LicenseScanner;