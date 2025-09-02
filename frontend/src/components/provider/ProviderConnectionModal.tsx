import React, { useState, useEffect } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { MultiSelect, MultiSelectOption } from "../ui/MultiSelect";
import { UserSelector } from "../ui/UserSelector";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "../../contexts/ToastContext";
import { apiService } from "../../services/api";
import { AIProvider, AIModel } from "../../types";

export interface ProviderConnectionForm {
  name: string;
  apiKey: string;
  collaboratorIds: string[];
  selectedModelIds: string[];
}

export interface ProviderConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  provider: AIProvider | null;
  onSuccess?: () => void;
}

export const ProviderConnectionModal: React.FC<
  ProviderConnectionModalProps
> = ({ isOpen, onClose, provider, onSuccess }) => {
  const { currentOrganization } = useAuth();
  const { showToast } = useToast();

  const [form, setForm] = useState<ProviderConnectionForm>({
    name: "",
    apiKey: "",
    collaboratorIds: [],
    selectedModelIds: [],
  });

  const [models, setModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<
    Partial<Record<keyof ProviderConnectionForm, string>>
  >({});

  // Load models for the selected provider
  useEffect(() => {
    const loadModels = async () => {
      if (!provider || !currentOrganization?.id) return;

      setLoading(true);
      try {
        apiService.setOrganizationContext(currentOrganization.id);

        const response = await apiService.get("/models/");
        if (response.error) {
          throw new Error(response.error);
        }

        // Filter models for the selected provider
        const providerModels = (response.data || []).filter(
          (model: AIModel) => model.provider_id === provider.id
        );

        setModels(providerModels);
      } catch (error) {
        console.error("Failed to load models:", error);
        showToast("error", "Failed to load available models");
        setModels([]);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && provider) {
      loadModels();
    }
  }, [isOpen, provider, currentOrganization?.id, showToast]);

  // Reset form when modal opens/closes or provider changes
  useEffect(() => {
    if (isOpen && provider) {
      setForm({
        name: `${provider.display_name} Connection`,
        apiKey: "",
        collaboratorIds: [],
        selectedModelIds: [],
      });
      setErrors({});
    } else if (!isOpen) {
      setForm({
        name: "",
        apiKey: "",
        collaboratorIds: [],
        selectedModelIds: [],
      });
      setErrors({});
      setModels([]);
    }
  }, [isOpen, provider]);

  // Convert models to MultiSelect options
  const modelOptions: MultiSelectOption[] = models.map((model) => ({
    id: model.id,
    label: model.display_name,
    value: model.id,
    description: `${model.model_type} • ${
      model.description || "No description"
    }`,
  }));

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof ProviderConnectionForm, string>> = {};

    if (!form.name.trim()) {
      newErrors.name = "Connection name is required";
    }

    if (!form.apiKey.trim()) {
      newErrors.apiKey = "API key is required";
    }

    if (form.selectedModelIds.length === 0) {
      newErrors.selectedModelIds = "Please select at least one model";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm() || !provider || !currentOrganization?.id) {
      return;
    }

    setSubmitting(true);

    try {
      // Create API key
      const apiKeyResponse = await apiService.post("/api-keys/", {
        name: form.name,
        provider_id: provider.id,
        project_id: currentOrganization?.id, // Using organization ID as project ID for now
        api_key_value: form.apiKey,
        validate: true,
      });

      if (apiKeyResponse.error) {
        throw new Error(apiKeyResponse.error);
      }

      // TODO: Create provider connection with collaborators and selected models
      // This would require additional backend endpoints

      showToast(
        "success",
        `Successfully connected to ${provider.display_name}`
      );
      onSuccess?.();
      onClose();
    } catch (error: any) {
      console.error("Failed to create provider connection:", error);
      showToast(
        "error",
        error.message || "Failed to create provider connection"
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Handle form field changes
  const updateForm = (field: keyof ProviderConnectionForm, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  if (!provider) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Connect to ${provider.display_name}`}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provider Info */}
        <div className="flex items-center space-x-4 p-4 bg-slate-50 rounded-xl">
          {provider.logo_url ? (
            <img
              src={provider.logo_url}
              alt={provider.display_name}
              className="w-12 h-12 rounded-lg object-cover"
            />
          ) : (
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl">🤖</span>
            </div>
          )}
          <div>
            <h3 className="font-semibold text-slate-900">
              {provider.display_name}
            </h3>
            <p className="text-sm text-slate-600">
              {provider.description || "AI Provider"}
            </p>
          </div>
        </div>

        {/* Connection Name */}
        <Input
          label="Connection Name"
          placeholder="Enter a name for this connection"
          value={form.name}
          onChange={(value) => updateForm("name", value)}
          error={errors.name}
          required
        />

        {/* API Key */}
        <Input
          label="API Key"
          type="password"
          placeholder="Enter your API key"
          value={form.apiKey}
          onChange={(value) => updateForm("apiKey", value)}
          error={errors.apiKey}
          required
        />

        {/* Collaborators */}
        <UserSelector
          label="Collaborators"
          placeholder="Select team members to share this connection with"
          selectedUserIds={form.collaboratorIds}
          onChange={(userIds) => updateForm("collaboratorIds", userIds)}
          organizationId={currentOrganization?.id}
          excludeCurrentUser={true}
        />

        {/* Model Selection */}
        <div className="space-y-2">
          <MultiSelect
            label="Available Models"
            placeholder={
              loading ? "Loading models..." : "Select models to enable"
            }
            options={modelOptions}
            selectedValues={form.selectedModelIds}
            onChange={(modelIds) => updateForm("selectedModelIds", modelIds)}
            error={errors.selectedModelIds}
            required
            disabled={loading}
            maxHeight="300px"
            showSelectAll={true}
          />
          {models.length > 0 && (
            <p className="text-xs text-slate-500">
              {models.length} models available • {form.selectedModelIds.length}{" "}
              selected
            </p>
          )}
        </div>

        {/* Security Notice */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg
                className="w-5 h-5 text-blue-600 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-900">
                Security Notice
              </h4>
              <p className="text-sm text-blue-700 mt-1">
                Your API key will be encrypted and stored securely. Only
                selected collaborators will have access to this connection.
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={submitting}
            disabled={loading}
          >
            {submitting ? "Connecting..." : "Connect Provider"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
