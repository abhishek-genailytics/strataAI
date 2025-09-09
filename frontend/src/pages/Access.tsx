import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import UsersTab from "@/pages/access/UsersTab";
import PATsTab from "@/pages/access/PATsTab";

export default function Access() {
  const [tab, setTab] = useState<"users" | "pats">("users");
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">
          Access Management
        </h1>
        <p className="text-gray-600 mt-1">
          Manage user access and personal access tokens for your organization
        </p>
      </div>

      <Card className="p-0 overflow-hidden">
        <Tabs
          value={tab}
          onValueChange={(v: string) => setTab(v as "users" | "pats")}
        >
          <div className="border-b px-6 pt-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="users">User Management</TabsTrigger>
              <TabsTrigger value="pats">Personal Access Tokens</TabsTrigger>
            </TabsList>
          </div>
          <div className="p-6">
            <TabsContent value="users" className="m-0">
              <UsersTab />
            </TabsContent>
            <TabsContent value="pats" className="m-0">
              <PATsTab />
            </TabsContent>
          </div>
        </Tabs>
      </Card>
    </div>
  );
}
