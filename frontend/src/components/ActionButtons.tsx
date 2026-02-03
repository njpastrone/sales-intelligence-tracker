import { useState } from 'react';

interface ActionButtonsProps {
  companyId: string;
  onMarkContacted: (companyId: string) => void;
  onSnooze: (companyId: string) => void;
  onAddNote: (companyId: string, note: string) => void;
}

export function ActionButtons({
  companyId,
  onMarkContacted,
  onSnooze,
  onAddNote,
}: ActionButtonsProps) {
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [note, setNote] = useState('');

  const handleAddNote = () => {
    if (note.trim()) {
      onAddNote(companyId, note.trim());
      setNote('');
      setShowNoteInput(false);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => onMarkContacted(companyId)}
        className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 hover:bg-green-200 rounded transition-colors"
        title="Mark as contacted"
      >
        ✅ Contacted
      </button>
      <button
        onClick={() => onSnooze(companyId)}
        className="px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 hover:bg-orange-200 rounded transition-colors"
        title="Snooze for 7 days"
      >
        😴 Snooze
      </button>
      {showNoteInput ? (
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
            ✕
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowNoteInput(true)}
          className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded transition-colors"
          title="Add a note"
        >
          📝 Note
        </button>
      )}
    </div>
  );
}
