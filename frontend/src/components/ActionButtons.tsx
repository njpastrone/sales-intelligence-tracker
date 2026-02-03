import { useState } from 'react';

interface ActionButtonsProps {
  companyId: string;
  companyName: string;
  onMarkContacted: (companyId: string) => void;
  onSnooze: (companyId: string) => void;
  onAddNote: (companyId: string, note: string) => void;
  onDelete: (companyId: string) => void;
}

export function ActionButtons({
  companyId,
  companyName,
  onMarkContacted,
  onSnooze,
  onAddNote,
  onDelete,
}: ActionButtonsProps) {
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [note, setNote] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleAddNote = () => {
    if (note.trim()) {
      onAddNote(companyId, note.trim());
      setNote('');
      setShowNoteInput(false);
    }
  };

  // Note input expanded state
  if (showNoteInput) {
    return (
      <div className="flex items-center gap-1">
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Add note..."
          className="px-2 py-1 text-xs border border-gray-300 rounded w-32 focus:outline-none focus:ring-1 focus:ring-blue-500"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleAddNote();
            if (e.key === 'Escape') setShowNoteInput(false);
          }}
          autoFocus
        />
        <button
          onClick={handleAddNote}
          className="px-2 py-1 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded"
        >
          Save
        </button>
        <button
          onClick={() => setShowNoteInput(false)}
          className="px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-800"
        >
          Cancel
        </button>
      </div>
    );
  }

  // Delete confirmation state
  if (showDeleteConfirm) {
    return (
      <div className="flex items-center gap-1">
        <span className="text-xs text-red-600">Delete {companyName}?</span>
        <button
          onClick={() => {
            onDelete(companyId);
            setShowDeleteConfirm(false);
          }}
          className="px-2 py-1 text-xs font-medium text-white bg-red-500 hover:bg-red-600 rounded"
        >
          Yes
        </button>
        <button
          onClick={() => setShowDeleteConfirm(false)}
          className="px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-800"
        >
          No
        </button>
      </div>
    );
  }

  // Default 2x2 grid layout
  return (
    <div className="grid grid-cols-2 gap-1">
      <button
        onClick={() => onMarkContacted(companyId)}
        className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 hover:bg-green-200 rounded transition-colors"
        title="Mark as contacted"
      >
        Contacted
      </button>
      <button
        onClick={() => onSnooze(companyId)}
        className="px-2 py-1 text-xs font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded transition-colors"
        title="Snooze for 7 days"
      >
        Snooze
      </button>
      <button
        onClick={() => setShowNoteInput(true)}
        className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded transition-colors"
        title="Add a note"
      >
        Note
      </button>
      <button
        onClick={() => setShowDeleteConfirm(true)}
        className="px-2 py-1 text-xs font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded transition-colors"
        title="Delete company"
      >
        Delete
      </button>
    </div>
  );
}
