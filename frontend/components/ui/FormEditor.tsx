import React, { useState } from 'react';
import { Plus, Trash2, X, ArrowUp, ArrowDown } from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { Textarea } from './Textarea';
import { Label } from './Label';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { FormConfig, FormStep } from '../../types';
import { cn } from '../../utils';

interface FormEditorProps {
  forms: { [key: string]: FormConfig };
  onChange: (forms: { [key: string]: FormConfig }) => void;
}

export const FormEditor: React.FC<FormEditorProps> = ({ forms, onChange }) => {
  const [selectedForm, setSelectedForm] = useState<string>(
    Object.keys(forms)[0] || ''
  );
  const [newFormName, setNewFormName] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const currentForm = selectedForm ? forms[selectedForm] : null;

  const handleAddForm = () => {
    if (!newFormName.trim()) return;
    onChange({
      ...forms,
      [newFormName]: {
        name: newFormName,
        steps: [],
      },
    });
    setSelectedForm(newFormName);
    setNewFormName('');
    setShowAddForm(false);
  };

  const handleDeleteForm = (name: string) => {
    const newForms = { ...forms };
    delete newForms[name];
    onChange(newForms);
    if (selectedForm === name) {
      const remainingKeys = Object.keys(newForms);
      setSelectedForm(remainingKeys[0] || '');
    }
  };

  const handleFormChange = (field: keyof FormConfig, value: any) => {
    if (!selectedForm) return;
    onChange({
      ...forms,
      [selectedForm]: {
        ...forms[selectedForm],
        [field]: value,
      },
    });
  };

  const handleAddStep = () => {
    if (!selectedForm) return;
    const updated = {
      ...forms,
      [selectedForm]: {
        ...forms[selectedForm],
        steps: [
          ...forms[selectedForm].steps,
          {
            field: `field_${forms[selectedForm].steps.length + 1}`,
            type: 'text',
            prompt: 'Enter value:',
            required: false,
          },
        ],
      },
    };
    onChange(updated);
  };

  const handleDeleteStep = (stepIndex: number) => {
    if (!selectedForm) return;
    const updated = {
      ...forms,
      [selectedForm]: {
        ...forms[selectedForm],
        steps: forms[selectedForm].steps.filter((_, i) => i !== stepIndex),
      },
    };
    onChange(updated);
  };

  const handleMoveStep = (stepIndex: number, direction: 'up' | 'down') => {
    if (!selectedForm) return;
    const steps = [...forms[selectedForm].steps];
    const newIndex = direction === 'up' ? stepIndex - 1 : stepIndex + 1;
    if (newIndex < 0 || newIndex >= steps.length) return;
    [steps[stepIndex], steps[newIndex]] = [steps[newIndex], steps[stepIndex]];
    onChange({
      ...forms,
      [selectedForm]: {
        ...forms[selectedForm],
        steps,
      },
    });
  };

  const handleStepChange = (
    stepIndex: number,
    field: keyof FormStep,
    value: any
  ) => {
    if (!selectedForm) return;
    const updated = {
      ...forms,
      [selectedForm]: {
        ...forms[selectedForm],
        steps: forms[selectedForm].steps.map((step, i) =>
          i === stepIndex ? { ...step, [field]: value } : step
        ),
      },
    };
    onChange(updated);
  };

  const handleValidationChange = (
    stepIndex: number,
    field: string,
    value: number | undefined
  ) => {
    if (!selectedForm) return;
    const step = forms[selectedForm].steps[stepIndex];
    const validation = step.validation || {};
    const updatedValidation = value !== undefined
      ? { ...validation, [field]: value }
      : Object.fromEntries(Object.entries(validation).filter(([k]) => k !== field));
    
    handleStepChange(stepIndex, 'validation', updatedValidation);
  };

  return (
    <div className="space-y-4">
      {/* Form Selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {Object.keys(forms).map((name) => (
          <div key={name} className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setSelectedForm(name)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                selectedForm === name
                  ? 'bg-primary text-white'
                  : 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-200 border border-black/10 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10'
              )}
            >
              {name}
            </button>
            <button
              type="button"
              onClick={() => handleDeleteForm(name)}
              className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
        {showAddForm ? (
          <div className="flex items-center gap-2">
            <Input
              value={newFormName}
              onChange={(e) => setNewFormName(e.target.value)}
              placeholder="Form name"
              className="w-32 h-8 text-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddForm();
                if (e.key === 'Escape') {
                  setShowAddForm(false);
                  setNewFormName('');
                }
              }}
            />
            <Button size="sm" onClick={handleAddForm}>
              Add
            </Button>
            <Button variant="ghost" size="sm" onClick={() => {
              setShowAddForm(false);
              setNewFormName('');
            }}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowAddForm(true)}
            icon={<Plus className="w-3 h-3" />}
          >
            Add Form
          </Button>
        )}
      </div>

      {/* Form Editor */}
      {currentForm && (
        <Card>
          <CardHeader>
            <CardTitle>{currentForm.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Input
              label="Form Name"
              value={currentForm.name}
              onChange={(e) => handleFormChange('name', e.target.value)}
            />
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Form Steps</Label>
                <Button variant="secondary" onClick={handleAddStep} icon={<Plus className="w-4 h-4" />}>
                  Add Step
                </Button>
              </div>
              
              {currentForm.steps.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No steps yet. Add a step to start building your form.</p>
                </div>
              ) : (
                currentForm.steps.map((step, stepIndex) => (
                  <div
                    key={stepIndex}
                    className="border border-black/10 dark:border-white/10 rounded-lg p-4 space-y-4"
                  >
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">Step {stepIndex + 1}</Label>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveStep(stepIndex, 'up')}
                          disabled={stepIndex === 0}
                          icon={<ArrowUp className="w-3 h-3" />}
                        >
                          Up
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveStep(stepIndex, 'down')}
                          disabled={stepIndex === currentForm.steps.length - 1}
                          icon={<ArrowDown className="w-3 h-3" />}
                        >
                          Down
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteStep(stepIndex)}
                          icon={<Trash2 className="w-3 h-3 text-red-500" />}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="Field Name"
                        value={step.field}
                        onChange={(e) => handleStepChange(stepIndex, 'field', e.target.value)}
                        placeholder="name"
                      />
                      <div className="space-y-1.5">
                        <Label>Field Type</Label>
                        <select
                          className="block w-full rounded-lg border px-3 py-2 text-sm bg-white dark:bg-white/5 border-black/10 dark:border-white/10 text-gray-900 dark:text-gray-100"
                          value={step.type}
                          onChange={(e) => handleStepChange(stepIndex, 'type', e.target.value)}
                        >
                          <option value="text">Text</option>
                          <option value="textarea">Textarea</option>
                          <option value="number">Number</option>
                          <option value="email">Email</option>
                          <option value="phone">Phone</option>
                          <option value="choice">Choice</option>
                        </select>
                      </div>
                    </div>
                    
                    <Textarea
                      label="Prompt"
                      value={step.prompt}
                      onChange={(e) => handleStepChange(stepIndex, 'prompt', e.target.value)}
                      placeholder="Enter your name:"
                      rows={2}
                    />
                    
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={step.required || false}
                          onChange={(e) => handleStepChange(stepIndex, 'required', e.target.checked)}
                          className="rounded border-black/10 dark:border-white/10"
                        />
                        <span className="text-sm">Required</span>
                      </label>
                    </div>
                    
                    {step.type === 'choice' && (
                      <div className="space-y-2">
                        <Label>Options</Label>
                        <Textarea
                          value={step.options?.join(', ') || ''}
                          onChange={(e) =>
                            handleStepChange(
                              stepIndex,
                              'options',
                              e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                            )
                          }
                          placeholder="Option 1, Option 2, Option 3"
                          rows={2}
                        />
                        <p className="text-xs text-gray-500">Separate options with commas</p>
                      </div>
                    )}
                    
                    {(step.type === 'text' || step.type === 'textarea') && (
                      <div className="grid grid-cols-2 gap-4">
                        <Input
                          label="Min Length"
                          type="number"
                          value={step.validation?.min_length || ''}
                          onChange={(e) =>
                            handleValidationChange(
                              stepIndex,
                              'min_length',
                              e.target.value ? parseInt(e.target.value) : undefined
                            )
                          }
                          placeholder="0"
                        />
                        <Input
                          label="Max Length"
                          type="number"
                          value={step.validation?.max_length || ''}
                          onChange={(e) =>
                            handleValidationChange(
                              stepIndex,
                              'max_length',
                              e.target.value ? parseInt(e.target.value) : undefined
                            )
                          }
                          placeholder="100"
                        />
                      </div>
                    )}
                    
                    {step.type === 'number' && (
                      <div className="grid grid-cols-2 gap-4">
                        <Input
                          label="Min Value"
                          type="number"
                          value={step.validation?.min_value || ''}
                          onChange={(e) =>
                            handleValidationChange(
                              stepIndex,
                              'min_value',
                              e.target.value ? parseFloat(e.target.value) : undefined
                            )
                          }
                          placeholder="0"
                        />
                        <Input
                          label="Max Value"
                          type="number"
                          value={step.validation?.max_value || ''}
                          onChange={(e) =>
                            handleValidationChange(
                              stepIndex,
                              'max_value',
                              e.target.value ? parseFloat(e.target.value) : undefined
                            )
                          }
                          placeholder="100"
                        />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

