"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Save, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { settingsService } from "@/services/settings.service";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Setting } from "@/types";

const settingsCategories = [
  {
    id: "general",
    title: "General",
    description: "System-wide configuration",
    settings: [
      { key: "owner_name", label: "Owner Name", defaultValue: "AI Call Reception", type: "text" },
      { key: "default_language", label: "Default Language", defaultValue: "en-US", type: "text" },
    ],
  },
  {
    id: "greeting",
    title: "Greeting",
    description: "Call greeting configuration",
    settings: [
      { key: "greeting_message", label: "Greeting Message", defaultValue: "Hello, you have reached AI Call Reception. Please leave a message after the tone.", type: "text" },
      { key: "greeting_enabled", label: "Greeting Enabled", defaultValue: "true", type: "text" },
    ],
  },
  {
    id: "recording",
    title: "Recording",
    description: "Call recording settings",
    settings: [
      { key: "recording_enabled", label: "Recording Enabled", defaultValue: "true", type: "text" },
      { key: "recording_format", label: "Recording Format", defaultValue: "wav", type: "text" },
      { key: "max_recording_duration", label: "Max Duration (seconds)", defaultValue: "300", type: "text" },
    ],
  },
  {
    id: "transcription",
    title: "Transcription",
    description: "Speech-to-text configuration",
    settings: [
      { key: "transcription_enabled", label: "Transcription Enabled", defaultValue: "true", type: "text" },
      { key: "transcription_language", label: "Transcription Language", defaultValue: "en-US", type: "text" },
    ],
  },
  {
    id: "device",
    title: "Device",
    description: "Device management settings",
    settings: [
      { key: "device_timeout", label: "Device Timeout (seconds)", defaultValue: "10", type: "text" },
      { key: "heartbeat_interval", label: "Heartbeat Interval (seconds)", defaultValue: "5", type: "text" },
      { key: "auto_answer_enabled", label: "Auto Answer Enabled", defaultValue: "true", type: "text" },
      { key: "auto_answer_delay", label: "Auto Answer Delay (seconds)", defaultValue: "2", type: "text" },
    ],
  },
  {
    id: "system",
    title: "System",
    description: "System configuration",
    settings: [
      { key: "tts_enabled", label: "TTS Enabled", defaultValue: "false", type: "text" },
      { key: "log_level", label: "Log Level", defaultValue: "INFO", type: "text" },
      { key: "max_call_duration", label: "Max Call Duration (seconds)", defaultValue: "600", type: "text" },
    ],
  },
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<Record<string, string>>({});
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");

  // Load settings from backend
  const { data: settingsData, isLoading, error } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const response = await settingsService.getAll();
      return response.data;
    },
  });

  // Initialize values from backend or defaults
  useEffect(() => {
    const initial: Record<string, string> = {};
    
    // First, set defaults
    settingsCategories.forEach((cat) =>
      cat.settings.forEach((s) => (initial[s.key] = s.defaultValue)),
    );

    // Then override with backend values
    if (settingsData) {
      settingsData.forEach((setting: Setting) => {
        initial[setting.key] = setting.value;
      });
    }

    setValues(initial);
  }, [settingsData]);

  // Save mutation - batch all settings into single request
  const saveMutation = useMutation({
    mutationFn: async (settingsToSave: Record<string, string>) => {
      // Build batch payload with all settings
      const batch = Object.entries(settingsToSave).map(([key, value]) => {
        // Find category for this key
        let category = "general";
        for (const cat of settingsCategories) {
          if (cat.settings.some((s) => s.key === key)) {
            category = cat.id;
            break;
          }
        }

        return {
          key,
          value,
          category,
          description: settingsCategories
            .flatMap((c) => c.settings)
            .find((s) => s.key === key)?.label || "",
        };
      });

      // Send all settings in single request (new batch endpoint)
      const response = await settingsService.batchUpsert(batch);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setSaveStatus("success");
      setTimeout(() => setSaveStatus("idle"), 3000);
    },
    onError: (err: Error) => {
      console.error("Settings save failed:", err);
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 5000);
    },
  });

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }));
    setSaveStatus("idle");
  };

  const handleSave = () => {
    saveMutation.mutate(values);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
          <h3 className="mt-4 text-lg font-semibold">Failed to load settings</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
          <p className="text-sm text-muted-foreground">
            Configure your AI Call Reception system
          </p>
        </div>
        <Button 
          onClick={handleSave} 
          disabled={saveMutation.isPending}
        >
          {saveMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : saveStatus === "success" ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Saved!
            </>
          ) : saveStatus === "error" ? (
            <>
              <AlertCircle className="mr-2 h-4 w-4" />
              Error
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {settingsCategories.map((category) => (
          <Card key={category.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{category.title}</CardTitle>
                  <CardDescription>{category.description}</CardDescription>
                </div>
                <Badge variant="outline">{category.id}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {category.settings.map((setting) => (
                <div key={setting.key} className="space-y-1">
                  <label className="text-sm font-medium">
                    {setting.label}
                  </label>
                  <Input
                    value={values[setting.key] || ""}
                    onChange={(e) => handleChange(setting.key, e.target.value)}
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
