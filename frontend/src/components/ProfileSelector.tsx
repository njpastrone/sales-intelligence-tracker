import { useState } from 'react';
import type { Profile } from '../types';

interface ProfileSelectorProps {
  profiles: Profile[];
  selectedProfileId: string | null;
  onSelectProfile: (profileId: string) => void;
  onCreateProfile: (name: string) => Promise<void>;
  onDeleteProfile: (profileId: string) => Promise<void>;
}

export function ProfileSelector({
  profiles,
  selectedProfileId,
  onSelectProfile,
  onCreateProfile,
  onDeleteProfile,
}: ProfileSelectorProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreate = async () => {
    const trimmed = newName.trim();
    if (!trimmed) return;
    setIsSubmitting(true);
    try {
      await onCreateProfile(trimmed);
      setNewName('');
      setIsCreating(false);
    } catch {
      // error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCreate();
    if (e.key === 'Escape') {
      setIsCreating(false);
      setNewName('');
    }
  };

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId);

  return (
    <div className="flex items-center gap-2">
      <label className="text-blue-100 text-sm font-medium whitespace-nowrap">Territory:</label>
      <select
        value={selectedProfileId || ''}
        onChange={(e) => onSelectProfile(e.target.value)}
        className="bg-blue-500 text-white text-sm border border-blue-400 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-300"
      >
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>

      {isCreating ? (
        <div className="flex items-center gap-1">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Profile name"
            className="bg-blue-500 text-white text-sm border border-blue-400 rounded px-2 py-1 placeholder-blue-300 focus:outline-none focus:ring-1 focus:ring-blue-300 w-32"
            autoFocus
            disabled={isSubmitting}
          />
          <button
            onClick={handleCreate}
            disabled={isSubmitting || !newName.trim()}
            className="text-white text-sm bg-blue-500 hover:bg-blue-400 border border-blue-400 rounded px-2 py-1 disabled:opacity-50"
          >
            Add
          </button>
          <button
            onClick={() => { setIsCreating(false); setNewName(''); }}
            className="text-blue-200 hover:text-white text-sm px-1"
          >
            x
          </button>
        </div>
      ) : (
        <button
          onClick={() => setIsCreating(true)}
          className="text-white text-sm bg-blue-500 hover:bg-blue-400 border border-blue-400 rounded w-7 h-7 flex items-center justify-center"
          title="Create new territory"
        >
          +
        </button>
      )}

      {selectedProfile && profiles.length > 1 && (
        <button
          onClick={() => {
            if (window.confirm(`Delete territory "${selectedProfile.name}"? Companies will remain in other territories.`)) {
              onDeleteProfile(selectedProfile.id);
            }
          }}
          className="text-blue-300 hover:text-red-300 text-xs px-1"
          title="Delete this territory"
        >
          Delete
        </button>
      )}
    </div>
  );
}
