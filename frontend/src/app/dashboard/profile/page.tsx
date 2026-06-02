"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";
import { formatDate } from "@/lib/utils";
import { User, Mail, Calendar, Shield } from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuthStore();

  if (!user) return null;

  const profileItems = [
    { label: "Username", value: user.username, icon: User },
    { label: "Email", value: user.email, icon: Mail },
    { label: "Role", value: user.role, icon: Shield },
    { label: "Member Since", value: formatDate(user.created_at), icon: Calendar },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Profile</h2>
        <p className="text-sm text-muted-foreground">
          Your account information
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Account Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {profileItems.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {item.label}
                    </p>
                    <p className="font-medium">{item.value}</p>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Account Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Active</span>
              <span
                className={`text-sm font-medium ${user.is_active ? "text-green-600" : "text-red-600"}`}
              >
                {user.is_active ? "Yes" : "No"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Last Updated</span>
              <span className="text-sm font-medium">
                {formatDate(user.updated_at)}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
