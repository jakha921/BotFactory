import React, { useState } from 'react';
import { Plus, Trash2, X, Move } from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { Label } from './Label';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { InlineKeyboardButton } from '../../types';
import { cn } from '../../utils';

interface KeyboardEditorProps {
  keyboards: { [key: string]: InlineKeyboardButton[][] };
  onChange: (keyboards: { [key: string]: InlineKeyboardButton[][] }) => void;
}

export const KeyboardEditor: React.FC<KeyboardEditorProps> = ({ keyboards, onChange }) => {
  const [selectedKeyboard, setSelectedKeyboard] = useState<string>(
    Object.keys(keyboards)[0] || 'main_menu'
  );
  const [newKeyboardName, setNewKeyboardName] = useState('');
  const [showAddKeyboard, setShowAddKeyboard] = useState(false);

  const currentKeyboard = keyboards[selectedKeyboard] || [];

  const handleAddKeyboard = () => {
    if (!newKeyboardName.trim()) return;
    onChange({
      ...keyboards,
      [newKeyboardName]: [],
    });
    setSelectedKeyboard(newKeyboardName);
    setNewKeyboardName('');
    setShowAddKeyboard(false);
  };

  const handleDeleteKeyboard = (name: string) => {
    const newKeyboards = { ...keyboards };
    delete newKeyboards[name];
    onChange(newKeyboards);
    if (selectedKeyboard === name) {
      const remainingKeys = Object.keys(newKeyboards);
      setSelectedKeyboard(remainingKeys[0] || '');
    }
  };

  const handleAddRow = () => {
    const updated = [...currentKeyboard, []];
    onChange({
      ...keyboards,
      [selectedKeyboard]: updated,
    });
  };

  const handleDeleteRow = (rowIndex: number) => {
    const updated = currentKeyboard.filter((_, i) => i !== rowIndex);
    onChange({
      ...keyboards,
      [selectedKeyboard]: updated,
    });
  };

  const handleAddButton = (rowIndex: number) => {
    const updated = [...currentKeyboard];
    updated[rowIndex] = [...(updated[rowIndex] || []), { text: 'Button', callback_data: 'action_' }];
    onChange({
      ...keyboards,
      [selectedKeyboard]: updated,
    });
  };

  const handleDeleteButton = (rowIndex: number, buttonIndex: number) => {
    const updated = [...currentKeyboard];
    updated[rowIndex] = updated[rowIndex].filter((_, i) => i !== buttonIndex);
    onChange({
      ...keyboards,
      [selectedKeyboard]: updated,
    });
  };

  const handleButtonChange = (
    rowIndex: number,
    buttonIndex: number,
    field: keyof InlineKeyboardButton,
    value: any
  ) => {
    const updated = [...currentKeyboard];
    updated[rowIndex] = [...updated[rowIndex]];
    updated[rowIndex][buttonIndex] = {
      ...updated[rowIndex][buttonIndex],
      [field]: value,
    };
    onChange({
      ...keyboards,
      [selectedKeyboard]: updated,
    });
  };

  return (
    <div className="space-y-4">
      {/* Keyboard Selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {Object.keys(keyboards).map((name) => (
          <div key={name} className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setSelectedKeyboard(name)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                selectedKeyboard === name
                  ? 'bg-primary text-white'
                  : 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-200 border border-black/10 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10'
              )}
            >
              {name}
            </button>
            {Object.keys(keyboards).length > 1 && (
              <button
                type="button"
                onClick={() => handleDeleteKeyboard(name)}
                className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
        {showAddKeyboard ? (
          <div className="flex items-center gap-2">
            <Input
              value={newKeyboardName}
              onChange={(e) => setNewKeyboardName(e.target.value)}
              placeholder="Keyboard name"
              className="w-32 h-8 text-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddKeyboard();
                if (e.key === 'Escape') {
                  setShowAddKeyboard(false);
                  setNewKeyboardName('');
                }
              }}
            />
            <Button size="sm" onClick={handleAddKeyboard}>
              Add
            </Button>
            <Button variant="ghost" size="sm" onClick={() => {
              setShowAddKeyboard(false);
              setNewKeyboardName('');
            }}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowAddKeyboard(true)}
            icon={<Plus className="w-3 h-3" />}
          >
            Add Keyboard
          </Button>
        )}
      </div>

      {/* Keyboard Editor */}
      {selectedKeyboard && (
        <Card>
          <CardHeader>
            <CardTitle>{selectedKeyboard}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentKeyboard.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No rows yet. Add a row to start building your keyboard.</p>
              </div>
            ) : (
              currentKeyboard.map((row, rowIndex) => (
                <div key={rowIndex} className="border border-black/10 dark:border-white/10 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs text-gray-500">Row {rowIndex + 1}</Label>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleAddButton(rowIndex)}
                        icon={<Plus className="w-3 h-3" />}
                      >
                        Add Button
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteRow(rowIndex)}
                        icon={<Trash2 className="w-3 h-3 text-red-500" />}
                      >
                        Delete Row
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {row.map((button, buttonIndex) => (
                      <div key={buttonIndex} className="grid grid-cols-1 md:grid-cols-2 gap-2 p-3 bg-gray-50 dark:bg-white/5 rounded border border-black/5 dark:border-white/5">
                        <Input
                          label="Button Text"
                          value={button.text}
                          onChange={(e) =>
                            handleButtonChange(rowIndex, buttonIndex, 'text', e.target.value)
                          }
                          placeholder="Button text"
                        />
                        <div className="space-y-2">
                          <Label className="text-xs">Button Type</Label>
                          <select
                            className="block w-full rounded-lg border px-3 py-2 text-sm bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100"
                            value={button.callback_data ? 'callback' : button.url ? 'url' : 'callback'}
                            onChange={(e) => {
                              const type = e.target.value;
                              if (type === 'callback') {
                                handleButtonChange(rowIndex, buttonIndex, 'callback_data', button.callback_data || 'action_');
                                handleButtonChange(rowIndex, buttonIndex, 'url', undefined);
                              } else if (type === 'url') {
                                handleButtonChange(rowIndex, buttonIndex, 'url', button.url || 'https://');
                                handleButtonChange(rowIndex, buttonIndex, 'callback_data', undefined);
                              }
                            }}
                          >
                            <option value="callback">Callback Data</option>
                            <option value="url">URL</option>
                          </select>
                        </div>
                        {button.callback_data !== undefined ? (
                          <Input
                            label="Callback Data"
                            value={button.callback_data}
                            onChange={(e) =>
                              handleButtonChange(rowIndex, buttonIndex, 'callback_data', e.target.value)
                            }
                            placeholder="action_start_chat"
                          />
                        ) : (
                          <Input
                            label="URL"
                            value={button.url || ''}
                            onChange={(e) =>
                              handleButtonChange(rowIndex, buttonIndex, 'url', e.target.value)
                            }
                            placeholder="https://example.com"
                          />
                        )}
                        <div className="flex items-end">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteButton(rowIndex, buttonIndex)}
                            icon={<Trash2 className="w-3 h-3 text-red-500" />}
                          >
                            Delete
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
            <Button variant="secondary" onClick={handleAddRow} icon={<Plus className="w-4 h-4" />}>
              Add Row
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};


