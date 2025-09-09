import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { qk } from "@/utils/queryKeys";
import { listModels, createApiKey, enableModels } from "@/services/providers";
import { formatMoney } from "@/utils/format";
import { Key, Bot, DollarSign } from "lucide-react";
import type { ModelInfo, Provider } from "@/types/backend";

export default function ConfigureProviderDialog({
  open,
  onOpenChange,
  provider,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  provider: Provider | null;
}) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [label, setLabel] = useState("");
  const [apiKey, setApiKey] = useState("");

  const provKey = provider?.name; // Use provider name instead of ID for backend filtering
  const { data: models, isLoading } = useQuery({
    queryKey: ["cfg-models", provKey],
    queryFn: () => listModels({ provider: provKey! }),
    enabled: !!provKey && open,
  });

  const [selected, setSelected] = useState<Record<string, boolean>>({});
  useEffect(() => {
    // reset selections when dialog opens
    if (open) {
      setSelected({});
    }
  }, [open]);

  const selectedIds = useMemo(
    () => Object.keys(selected).filter((k) => selected[k]),
    [selected]
  );

  // Select All functionality
  const toggleSelectAll = () => {
    if (!models?.length) return;
    const allSelected = models.every((m: ModelInfo) => selected[m.id]);
    if (allSelected) {
      // Deselect all
      setSelected({});
    } else {
      // Select all
      const newSelected: Record<string, boolean> = {};
      models.forEach((m: ModelInfo) => {
        newSelected[m.id] = true;
      });
      setSelected(newSelected);
    }
  };

  const allSelected = models?.length
    ? models.every((m: ModelInfo) => selected[m.id])
    : false;
  const someSelected = models?.length
    ? models.some((m: ModelInfo) => selected[m.id])
    : false;

  const mCreateKey = useMutation({
    mutationFn: async () => {
      if (!provider) throw new Error("No provider selected");
      // 1) create API key/connection
      await createApiKey({ provider: provider.id, label, api_key: apiKey });
      // 2) enable models (optional)
      if (selectedIds.length) {
        await enableModels({ provider: provider.id, model_ids: selectedIds });
      }
    },
    onSuccess: async () => {
      toast({
        title: "Provider configured",
        description: `${provider?.name} connected`,
      });
      await Promise.all([
        qc.invalidateQueries({ queryKey: qk.providers }),
        qc.invalidateQueries({ queryKey: qk.apiKeys }),
        qc.invalidateQueries({ queryKey: qk.models(provider?.id) }),
      ]);
      onOpenChange(false);
      setLabel("");
      setApiKey("");
    },
    onError: (e: Error) =>
      toast({
        title: "Configuration failed",
        description: e.message,
        variant: "destructive",
      }),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Setup {provider?.name} account and manage models
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* API Key Configuration */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Key className="h-4 w-4 text-gray-500" />
              <Label className="text-base font-medium">API Configuration</Label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="Enter Name"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="collaborators">Collaborators</Label>
                <div className="text-sm text-gray-600">
                  List of users who have access to this provider account
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="api-key" className="flex items-center gap-2">
                {provider?.name === "openai" && "OpenAI API Key Auth"}
                {provider?.name === "anthropic" && "Anthropic API Key Auth"}
                {provider?.name !== "openai" &&
                  provider?.name !== "anthropic" &&
                  "API Key Auth"}
                <span className="text-red-500">*</span>
              </Label>
              <Input
                id="api-key"
                type="password"
                placeholder="Enter API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
          </div>

          <Separator />

          {/* Models Selection */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-gray-500" />
                <Label className="text-base font-medium">Models</Label>
              </div>
              {models && models.length > 0 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={toggleSelectAll}
                  className="h-8 px-3 text-xs"
                >
                  {allSelected ? "Deselect All" : "Select All"}
                </Button>
              )}
            </div>

            <div className="rounded-lg border bg-white">
              <ScrollArea className="h-64">
                <div className="divide-y">
                  {isLoading ? (
                    <div className="p-4 text-center text-sm text-slate-500">
                      Loading models…
                    </div>
                  ) : models?.length ? (
                    <>
                      {/* Select All option at the top */}
                      <label className="flex items-center gap-3 p-4 cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                        <Checkbox
                          checked={allSelected}
                          ref={(el) => {
                            if (el && "indeterminate" in el) {
                              (el as HTMLInputElement).indeterminate =
                                someSelected && !allSelected;
                            }
                          }}
                          onCheckedChange={toggleSelectAll}
                        />
                        <div className="flex-1">
                          <div className="font-medium text-sm">
                            {allSelected
                              ? "All Models Selected"
                              : someSelected
                                ? "Some Models Selected"
                                : "Select All Models"}
                          </div>
                          <div className="text-xs text-slate-500">
                            {selectedIds.length} of {models.length} models
                            selected
                          </div>
                        </div>
                      </label>

                      {/* Individual models */}
                      {models.map((m: ModelInfo) => (
                        <label
                          key={m.id}
                          className="flex items-start gap-3 p-4 cursor-pointer hover:bg-slate-50 transition-colors"
                        >
                          <Checkbox
                            checked={!!selected[m.id]}
                            onCheckedChange={(v: boolean) =>
                              setSelected((s) => ({ ...s, [m.id]: !!v }))
                            }
                            className="mt-0.5"
                          />
                          <div className="min-w-0 flex-1">
                            <div className="font-medium text-sm">
                              {m.display_name}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              <div className="flex items-center gap-4 flex-wrap">
                                <span>{m.id}</span>
                                <span>
                                  • Context:{" "}
                                  {m.context_window?.toLocaleString() || "N/A"}{" "}
                                  tokens
                                </span>
                                {m.pricing && (
                                  <span className="flex items-center gap-1">
                                    <DollarSign className="h-3 w-3" />
                                    {m.pricing.input
                                      ? formatMoney(
                                          m.pricing.input.price,
                                          m.pricing.input.currency as
                                            | "USD"
                                            | "INR"
                                        )
                                      : "N/A"}
                                    /1K in,
                                    {m.pricing.output
                                      ? formatMoney(
                                          m.pricing.output.price,
                                          m.pricing.output.currency as
                                            | "USD"
                                            | "INR"
                                        )
                                      : "N/A"}
                                    /1K out
                                  </span>
                                )}
                              </div>
                            </div>
                            {m.capabilities &&
                              Object.keys(m.capabilities).some(
                                (k) =>
                                  m.capabilities?.[
                                    k as keyof typeof m.capabilities
                                  ]
                              ) && (
                                <div className="flex gap-1 mt-2 flex-wrap">
                                  {m.capabilities?.supports_streaming && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700 border border-blue-200">
                                      Streaming
                                    </span>
                                  )}
                                  {m.capabilities
                                    ?.supports_function_calling && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-green-50 text-green-700 border border-green-200">
                                      Tools
                                    </span>
                                  )}
                                  {m.capabilities?.vision && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-purple-50 text-purple-700 border border-purple-200">
                                      Vision
                                    </span>
                                  )}
                                </div>
                              )}
                          </div>
                        </label>
                      ))}
                    </>
                  ) : (
                    <div className="p-4 text-center text-sm text-slate-500">
                      No models found for this provider.
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>

            {selectedIds.length > 0 && (
              <div className="text-sm text-slate-600 bg-blue-50 p-3 rounded-lg">
                ✓ {selectedIds.length} model
                {selectedIds.length === 1 ? "" : "s"} selected for enablement
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => mCreateKey.mutate()}
            disabled={!label || !apiKey || mCreateKey.isPending}
            className="min-w-[140px]"
          >
            {mCreateKey.isPending
              ? "Connecting..."
              : `Add ${provider?.name || "Provider"} Account`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
