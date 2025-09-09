import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/utils/queryKeys";
import { useModels } from "@/hooks/useProviders";
import { listApiKeys, deleteApiKey, enableModels } from "@/services/providers";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { formatMoney } from "@/utils/format";
import { EmptyState } from "@/components/shared/EmptyState";
import { SkeletonList } from "@/components/shared/SkeletonList";
import type { ModelInfo } from "@/types/backend";

export default function ProviderManage() {
  const { providerId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const qc = useQueryClient();

  // providerId is now the provider name (e.g., "anthropic", "openai")
  const { data: models, isLoading, error } = useModels(providerId);
  const { data: apiKeys } = useQuery({
    queryKey: qk.apiKeys,
    queryFn: listApiKeys,
  });

  // Enabled set (derived from backend "enabled" flag if provided)
  const initialEnabled = useMemo(
    () => new Set((models ?? []).filter((m) => m.enabled).map((m) => m.id)),
    [models]
  );
  const [enabledSet, setEnabledSet] = useState<Set<string>>(new Set());

  useEffect(() => {
    setEnabledSet(new Set(initialEnabled));
  }, [initialEnabled]);

  const onToggle = (id: string, checked: boolean) => {
    setEnabledSet((prev) => {
      const next = new Set(prev);
      checked ? next.add(id) : next.delete(id);
      return next;
    });
  };

  const mSave = useMutation({
    mutationFn: async () => {
      await enableModels({
        provider: providerId!,
        model_ids: Array.from(enabledSet),
      });
    },
    onSuccess: async () => {
      toast({ title: "Models updated" });
      await qc.invalidateQueries({ queryKey: qk.models(providerId) });
    },
    onError: (e: any) =>
      toast({
        title: "Update failed",
        description: e.message,
        variant: "destructive",
      }),
  });

  const keyForProvider = useMemo(
    () => apiKeys?.find((k) => k.provider === providerId),
    [apiKeys, providerId]
  );

  const mRemoveKey = useMutation({
    mutationFn: async () => {
      if (!keyForProvider) throw new Error("No key found for this provider");
      await deleteApiKey(keyForProvider.id);
    },
    onSuccess: async () => {
      toast({ title: "Provider disconnected" });
      await Promise.all([
        qc.invalidateQueries({ queryKey: qk.apiKeys }),
        qc.invalidateQueries({ queryKey: qk.providers }),
        qc.invalidateQueries({ queryKey: qk.models(providerId) }),
      ]);
      navigate("/models");
    },
    onError: (e: any) =>
      toast({
        title: "Disconnect failed",
        description: e.message,
        variant: "destructive",
      }),
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          Manage: {providerId?.charAt(0).toUpperCase() + providerId?.slice(1)}
        </h1>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => navigate("/models")}>
            Back
          </Button>
          <Button
            variant="destructive"
            onClick={() => mRemoveKey.mutate()}
            disabled={!keyForProvider}
          >
            Disconnect
          </Button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <SkeletonList rows={8} />
        ) : error ? (
          <div className="p-6 text-red-500">Failed to load</div>
        ) : !(models && models.length) ? (
          <EmptyState
            title="No models available"
            description="Connect this provider or refresh catalog to see models."
          />
        ) : (
          <>
            <div className="p-4 flex items-center justify-between">
              <div className="text-sm text-slate-600">
                Toggle which models are **enabled** for this provider. Only
                enabled models are available in the Playground and Unified API.
              </div>
              <Button onClick={() => mSave.mutate()} disabled={mSave.isPending}>
                Save changes
              </Button>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]">Enable</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Model Type</TableHead>
                  <TableHead>Input Cost (per 1M tokens)</TableHead>
                  <TableHead>Output Cost (per 1M tokens)</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(models ?? []).map((m: ModelInfo) => {
                  const enabled = enabledSet.has(m.id);
                  const currency = m.pricing?.currency || "USD";
                  return (
                    <TableRow key={m.id}>
                      <TableCell>
                        <Checkbox
                          checked={enabled}
                          onCheckedChange={(v: boolean) => onToggle(m.id, !!v)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{m.display_name}</div>
                        <div className="text-xs text-slate-500">{m.id}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="capitalize">
                          {m.type || "chat"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {m.pricing?.input_per_1k
                          ? formatMoney(m.pricing.input_per_1k * 1000, currency)
                          : "N/A"}
                      </TableCell>
                      <TableCell className="text-xs">
                        {m.pricing?.output_per_1k
                          ? formatMoney(
                              m.pricing.output_per_1k * 1000,
                              currency
                            )
                          : "N/A"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          onClick={() =>
                            navigate(
                              `/playground?model=${encodeURIComponent(m.id)}`
                            )
                          }
                          disabled={!enabled}
                          title={
                            enabled
                              ? "Open in Playground"
                              : "Enable model to use in Playground"
                          }
                        >
                          Open in Playground
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </>
        )}
      </Card>
    </div>
  );
}
