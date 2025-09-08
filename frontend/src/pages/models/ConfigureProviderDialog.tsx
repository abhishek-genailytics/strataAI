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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { qk } from "@/utils/queryKeys";
import { listModels, createApiKey, enableModels } from "@/services/providers";
import { listOrgMembers } from "@/services/userManagement";
import { formatMoney } from "@/utils/format";
import type { ModelInfo, Provider, Profile } from "@/types/backend";

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
  const [collaborator, setCollaborator] = useState("");

  const provKey = provider?.name; // Use provider name instead of ID for backend filtering
  const { data: models, isLoading } = useQuery({
    queryKey: ["cfg-models", provKey],
    queryFn: () => listModels({ provider: provKey! }),
    enabled: !!provKey && open,
  });

  // Fetch organization members for collaborator dropdown
  const { data: orgMembers } = useQuery({
    queryKey: ["org-members"],
    queryFn: listOrgMembers,
    enabled: open,
  });

  const [selected, setSelected] = useState<Record<string, boolean>>({});
  useEffect(() => {
    // reset selections when dialog opens
    if (open) {
      setSelected({});
      setCollaborator("");
    }
  }, [open]);

  const selectedIds = useMemo(
    () => Object.keys(selected).filter((k) => selected[k]),
    [selected]
  );

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
    onError: (e: any) =>
      toast({
        title: "Configuration failed",
        description: e.message,
        variant: "destructive",
      }),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Configure {provider?.name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Connection label</Label>
            <Input
              placeholder="e.g. Production key"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>API key</Label>
            <Input
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Collaborators</Label>
            <Select value={collaborator} onValueChange={setCollaborator}>
              <SelectTrigger>
                <SelectValue placeholder="Select a collaborator" />
              </SelectTrigger>
              <SelectContent>
                {orgMembers?.map((member: Profile) => (
                  <SelectItem key={member.id} value={member.id}>
                    {member.name || member.email}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-slate-500">
              List of users who have access to this provider account
            </p>
          </div>

          <div className="space-y-2">
            <Label>Select models to enable (optional)</Label>
            <div className="rounded-md border">
              <ScrollArea className="h-56">
                <div className="divide-y">
                  {isLoading ? (
                    <div className="p-3 text-sm text-slate-500">
                      Loading models…
                    </div>
                  ) : models?.length ? (
                    models.map((m: ModelInfo) => (
                      <label
                        key={m.id}
                        className="flex items-center gap-3 p-3 cursor-pointer"
                      >
                        <Checkbox
                          checked={!!selected[m.id]}
                          onCheckedChange={(v: boolean) =>
                            setSelected((s) => ({ ...s, [m.id]: !!v }))
                          }
                        />
                        <div className="min-w-0">
                          <div className="font-medium truncate">
                            {m.display_name}
                          </div>
                          <div className="text-xs text-slate-500 truncate">
                            {m.id} • ctx {m.context_window} •
                            {` ${formatMoney(m.pricing?.input_per_1k, m.pricing?.currency || "USD")} / 1K in • ${formatMoney(m.pricing?.output_per_1k, m.pricing?.currency || "USD")} / 1K out`}
                          </div>
                        </div>
                      </label>
                    ))
                  ) : (
                    <div className="p-3 text-sm text-slate-500">
                      No models found for this provider.
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => mCreateKey.mutate()}
            disabled={!label || !apiKey || mCreateKey.isPending}
          >
            Add {provider?.name || "Provider"} Account
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
