import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/utils/queryKeys";
import {
  listTokens,
  createToken,
  revokeToken,
} from "@/services/userManagement";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import DataTable, { Column } from "@/components/shared/DataTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { SkeletonList } from "@/components/shared/SkeletonList";
import { Key } from "lucide-react";

export default function PATsTab() {
  const qc = useQueryClient();
  const { toast } = useToast();

  const { data, isLoading, error } = useQuery({
    queryKey: qk.tokens,
    queryFn: listTokens,
  });

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string>("read,write"); // comma-separated for simplicity
  const [expires, setExpires] = useState<string>(""); // ISO date

  const [showToken, setShowToken] = useState<string | null>(null);
  const [revokeId, setRevokeId] = useState<string | null>(null);

  const mCreate = useMutation({
    mutationFn: () =>
      createToken({
        name,
        scopes: scopes
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        expires_at: expires || null,
      }),
    onSuccess: (res) => {
      setOpen(false);
      setName("");
      setScopes("read,write");
      setExpires("");
      setShowToken(res.token); // copy-once
      qc.invalidateQueries({ queryKey: qk.tokens });
    },
    onError: (e: any) =>
      toast({
        title: "Failed to create token",
        description: e.message,
        variant: "destructive",
      }),
  });

  const mRevoke = useMutation({
    mutationFn: (id: string) => revokeToken(id),
    onSuccess: () => {
      toast({ title: "Token revoked" });
      qc.invalidateQueries({ queryKey: qk.tokens });
      setRevokeId(null);
    },
    onError: (e: any) =>
      toast({
        title: "Failed to revoke",
        description: e.message,
        variant: "destructive",
      }),
  });

  const columns: Column<any>[] = [
    { key: "name", header: "Name", sortable: true },
    {
      key: "scopes",
      header: "Scopes",
      accessor: (t) => <span className="text-xs">{t.scopes.join(", ")}</span>,
    },
    {
      key: "expires_at",
      header: "Expires",
      sortable: true,
      accessor: (t) => t.expires_at ?? "—",
    },
    {
      key: "last_used",
      header: "Last used",
      sortable: true,
      accessor: (t) => t.last_used ?? "—",
    },
    {
      key: "actions",
      header: "Actions",
      className: "text-right",
      accessor: (t) => (
        <Button variant="outline" onClick={() => setRevokeId(t.id)}>
          Revoke
        </Button>
      ),
    },
  ];

  if (isLoading) return <SkeletonList rows={6} />;
  if (error) return <div className="text-red-500">Failed to load tokens</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">
            Personal Access Tokens
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Create personal access tokens to authenticate with CLI / API. You'll
            only see the token once.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Key className="h-4 w-4 mr-2" />
              Create PAT
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Personal Access Token</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  placeholder="My PAT"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Scopes (comma-separated)</Label>
                <Input
                  placeholder="read,write"
                  value={scopes}
                  onChange={(e) => setScopes(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Expiry (optional, ISO yyyy-mm-dd)</Label>
                <Input
                  type="date"
                  value={expires}
                  onChange={(e) => setExpires(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => mCreate.mutate()}
                disabled={!name || mCreate.isPending}
              >
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {!data || data.length === 0 ? (
        <EmptyState
          title="No access tokens yet"
          description="Create your first personal access token to authenticate with the API."
        />
      ) : (
        <Card className="p-0">
          <DataTable
            rows={data ?? []}
            columns={columns}
            loading={isLoading}
            emptyText="No tokens found"
            searchableKeys={["name"] as any}
          />
        </Card>
      )}

      {/* Copy-once token reveal */}
      <Dialog open={!!showToken} onOpenChange={(o) => !o && setShowToken(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Copy your token</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              This token will not be shown again.
            </div>
            <div className="rounded-md border p-3 font-mono text-sm break-all bg-gray-50">
              {showToken}
            </div>
            <div className="flex justify-end">
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(showToken || "");
                  setShowToken(null);
                }}
              >
                Copy & Close
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Revoke confirm */}
      <AlertDialog
        open={!!revokeId}
        onOpenChange={(o) => !o && setRevokeId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke this token?</AlertDialogTitle>
          </AlertDialogHeader>
          <div className="text-sm text-gray-600">
            Any scripts/services using it will stop working.
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setRevokeId(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => revokeId && mRevoke.mutate(revokeId)}
              className="bg-red-600 hover:bg-red-700"
            >
              Revoke
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
