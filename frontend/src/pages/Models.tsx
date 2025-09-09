import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProviders } from "@/hooks/useProviders";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ConfigureProviderDialog from "@/pages/models/ConfigureProviderDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { SkeletonList } from "@/components/shared/SkeletonList";
import { CheckCircle, AlertCircle, Settings, Unplug } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { disconnectProvider } from "@/services/providers";
import { toast } from "@/hooks/use-toast";
import { qk } from "@/utils/queryKeys";

export default function Models() {
  const { data, isLoading, error } = useProviders();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [openCfg, setOpenCfg] = useState(false);
  const [currentProvider, setCurrentProvider] = useState<any>(null);

  const openConfigure = (p: any) => {
    setCurrentProvider(p);
    setOpenCfg(true);
  };

  const disconnectMutation = useMutation({
    mutationFn: (providerId: string) => disconnectProvider(providerId),
    onSuccess: () => {
      toast({ title: "Provider disconnected successfully" });
      queryClient.invalidateQueries({ queryKey: qk.providers });
      queryClient.invalidateQueries({ queryKey: ["configured-providers"] });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to disconnect provider",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  if (isLoading) return <SkeletonList rows={6} />;
  if (error)
    return <div className="p-6 text-red-500">Failed to load providers</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">
          Models & Providers
        </h1>
        <p className="text-gray-600 mt-1">
          Configure and manage your AI provider integrations
        </p>
      </div>

      {!data || data.length === 0 ? (
        <EmptyState
          title="No providers found"
          description="Your organization doesn't have any providers configured yet. Add your first provider to get started."
        />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.map((p) => (
            <Card key={p.id} className="p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm overflow-hidden">
                    {p.logo_url ? (
                      <img 
                        src={p.logo_url} 
                        alt={p.display_name || p.name} 
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      p.display_name?.charAt(0) || p.name?.charAt(0) || "?"
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {p.display_name || p.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      {p.configured ? (
                        <>
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <Badge
                            variant="secondary"
                            className="bg-green-50 text-green-700 border-green-200"
                          >
                            Connected
                          </Badge>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-4 w-4 text-amber-500" />
                          <Badge
                            variant="secondary"
                            className="bg-amber-50 text-amber-700 border-amber-200"
                          >
                            Not connected
                          </Badge>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                {!p.is_active ? (
                  <Button disabled className="flex-1 opacity-50">
                    Coming Soon
                  </Button>
                ) : p.configured ? (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/models/${p.name}`)}
                      className="flex-1"
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Manage
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => disconnectMutation.mutate(p.id)}
                      disabled={disconnectMutation.isPending}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Unplug className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <Button onClick={() => openConfigure(p)} className="flex-1">
                    Configure
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <ConfigureProviderDialog
        open={openCfg}
        onOpenChange={setOpenCfg}
        provider={currentProvider}
      />
    </div>
  );
}
