import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Algorithm, KeyPurpose, KeyStatus, KeyMetadata } from '../types/security';

export default function SecurityDashboardPage() {
  const [keys, setKeys] = useState<KeyMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const response = await api.get('/security/keys');
      setKeys(response.data.data);
    } catch (error) {
      console.error('Failed to fetch keys:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await api.post('/security/keys', {
        algorithm: Algorithm.AES256_GCM,
        key_purpose: KeyPurpose.ENCRYPTION,
      });
      fetchKeys();
    } catch (error) {
      console.error('Failed to generate key:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAction = async (keyId: string, action: 'activate' | 'deactivate' | 'rotate') => {
    try {
      await api.post(`/security/keys/${keyId}/${action}`);
      fetchKeys();
    } catch (error) {
      console.error(`Failed to ${action} key:`, error);
    }
  };

  const getStatusColor = (status: KeyStatus) => {
    switch (status) {
      case KeyStatus.ACTIVE:
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case KeyStatus.INACTIVE:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
      case KeyStatus.EXPIRED:
      case KeyStatus.REVOKED:
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Security & Cryptography</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage enterprise encryption keys and lifecycle metadata.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {isGenerating ? 'Generating...' : 'Generate New Key'}
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Key Identifier / Algorithm
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Version
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Rotation Due
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    Loading keys...
                  </td>
                </tr>
              ) : keys.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    No keys found. Generate one to get started.
                  </td>
                </tr>
              ) : (
                keys.map((key) => (
                  <tr key={key.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {key.key_identifier}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {key.algorithm} • {key.key_purpose}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-white">v{key.key_version}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(key.status)}`}>
                        {key.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {key.rotation_due ? new Date(key.rotation_due).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {key.status === KeyStatus.INACTIVE && (
                        <button
                          onClick={() => handleAction(key.id, 'activate')}
                          className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 mr-4"
                        >
                          Activate
                        </button>
                      )}
                      {key.status === KeyStatus.ACTIVE && (
                        <>
                          <button
                            onClick={() => handleAction(key.id, 'deactivate')}
                            className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 mr-4"
                          >
                            Deactivate
                          </button>
                          <button
                            onClick={() => handleAction(key.id, 'rotate')}
                            className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                          >
                            Rotate
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
