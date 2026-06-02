"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Activity,
  CheckCircle2,
  Languages,
  MessageSquare,
  Phone,
  PhoneMissed,
  PhoneOff,
  Send,
  Smartphone,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import { resolveWebSocketUrl } from "@/lib/ws-url";
import { conversationsService } from "@/services/conversations.service";
import type { Conversation, ConversationMessage } from "@/types";

interface LiveCallEvent {
  event_type: string;
  device_id: number | null;
  caller_number?: string | null;
  caller_name?: string | null;
  caller_type?: string | null;
  serial?: string;
  timestamp: string;
  duration?: number;
  data?: Record<string, unknown>;
}

interface ConversationSnapshot {
  call_id: number;
  call_session_id: number;
  device_id: number;
  caller_number: string | null;
  caller_name: string | null;
  language: string | null;
  call_status: string;
  conversation_id: number;
  conversation_status: string;
  completion_percentage: number;
  question_progress: { current: number; total: number };
  conversation: Array<{
    speaker: string;
    message_type: string;
    content: string;
    language: string | null;
    question_index: number | null;
    timestamp: string | null;
  }>;
  transcript: string | null;
}

const callEventTypes = [
  "incoming_call",
  "call_answered",
  "call_missed",
  "call_ended",
  "call_state_changed",
];

function snapshotFromConversation(conversation: Conversation): ConversationSnapshot {
  return {
    call_id: conversation.call_session_id,
    call_session_id: conversation.call_session_id,
    device_id: 0,
    caller_number: null,
    caller_name: null,
    language: conversation.language,
    call_status: conversation.status,
    conversation_id: conversation.id,
    conversation_status: conversation.status,
    completion_percentage: conversation.completion_percentage,
    question_progress: {
      current: conversation.current_question_index,
      total: conversation.total_questions,
    },
    conversation: conversation.messages.map((message: ConversationMessage) => ({
      speaker: message.speaker,
      message_type: message.message_type,
      content: message.content,
      language: message.language,
      question_index: message.question_index,
      timestamp: message.created_at,
    })),
    transcript: conversation.transcript,
  };
}

export default function LiveCallsPage() {
  const [events, setEvents] = useState<LiveCallEvent[]>([]);
  const [snapshot, setSnapshot] = useState<ConversationSnapshot | null>(null);
  const [answer, setAnswer] = useState("");
  const [wsState, setWsState] = useState<"Connected" | "Disconnected">("Disconnected");

  const { data: currentConversation } = useQuery({
    queryKey: ["conversation", "current"],
    queryFn: async () => (await conversationsService.getCurrent()).data,
  });

  useEffect(() => {
    if (currentConversation && !snapshot) {
      setSnapshot(snapshotFromConversation(currentConversation));
    }
  }, [currentConversation, snapshot]);

  useEffect(() => {
    const socket = new WebSocket(resolveWebSocketUrl());

    socket.onopen = () => setWsState("Connected");
    socket.onclose = () => setWsState("Disconnected");
    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "ping") {
        socket.send("ping");
        return;
      }

      if (msg.type === "conversation_updated") {
        setSnapshot(msg.data as ConversationSnapshot);
        return;
      }

      if (callEventTypes.includes(msg.type)) {
        setEvents((prev) => [
          {
            event_type: msg.type,
            device_id: msg.data?.device_id ?? null,
            caller_number: msg.data?.caller_number,
            caller_name: msg.data?.caller_name,
            caller_type: msg.data?.caller_type,
            serial: msg.data?.data?.serial ?? msg.data?.serial,
            timestamp: msg.timestamp,
            duration: msg.data?.duration,
            data: msg.data,
          },
          ...prev,
        ].slice(0, 100));
      }
    };

    return () => socket.close();
  }, []);

  const languageMutation = useMutation({
    mutationFn: (language: "english" | "hindi" | "gujarati") =>
      conversationsService.selectLanguage(snapshot!.call_session_id, language),
    onSuccess: (response) => setSnapshot(snapshotFromConversation(response.data)),
  });

  const answerMutation = useMutation({
    mutationFn: () => conversationsService.recordAnswer(snapshot!.call_session_id, answer),
    onSuccess: (response) => {
      setAnswer("");
      setSnapshot(snapshotFromConversation(response.data));
    },
  });

  const latestCall = events[0];
  const messages = snapshot?.conversation ?? [];
  const currentQuestion = useMemo(
    () => [...messages].reverse().find((message) => message.message_type === "question"),
    [messages],
  );

  const eventBadge = (eventType: string) => {
    if (eventType === "incoming_call") return <Badge variant="warning">Incoming</Badge>;
    if (eventType === "call_answered") return <Badge variant="success">Answered</Badge>;
    if (eventType === "call_missed") return <Badge variant="destructive">Missed</Badge>;
    if (eventType === "call_ended") return <Badge variant="secondary">Ended</Badge>;
    return <Badge variant="outline">State</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">AI Reception Console</h2>
          <p className="text-sm text-muted-foreground">
            Incoming calls, language selection, and fixed-question progress
          </p>
        </div>
        <Badge variant={wsState === "Connected" ? "success" : "destructive"}>
          {wsState}
        </Badge>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Phone className="h-4 w-4" />
                Current Call
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-muted-foreground">Caller</div>
                  <div className="font-medium">
                    {snapshot?.caller_name || latestCall?.caller_name || "Unknown"}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground">Number</div>
                  <div className="font-mono text-xs">
                    {snapshot?.caller_number || latestCall?.caller_number || "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground">Status</div>
                  <div className="font-medium">
                    {snapshot?.call_status || latestCall?.event_type || "Idle"}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground">Device</div>
                  <div className="flex items-center gap-1 font-medium">
                    <Smartphone className="h-3 w-3" />
                    {snapshot?.device_id || latestCall?.device_id || "-"}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Languages className="h-4 w-4" />
                Language
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm font-medium capitalize">
                {snapshot?.language || "Awaiting selection"}
              </div>
              <div className="grid grid-cols-3 gap-2">
                {(["english", "hindi", "gujarati"] as const).map((language) => (
                  <Button
                    key={language}
                    size="sm"
                    variant={snapshot?.language === language ? "default" : "outline"}
                    disabled={!snapshot || languageMutation.isPending}
                    onClick={() => languageMutation.mutate(language)}
                  >
                    {language === "english" ? "EN" : language === "hindi" ? "HI" : "GU"}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <CheckCircle2 className="h-4 w-4" />
                Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span>
                  {snapshot?.question_progress.current ?? 0} /{" "}
                  {snapshot?.question_progress.total ?? 0}
                </span>
                <span>{snapshot?.completion_percentage ?? 0}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${snapshot?.completion_percentage ?? 0}%` }}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="h-4 w-4" />
              Conversation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="min-h-[260px] space-y-2 rounded-md border bg-muted/30 p-3">
              {messages.length === 0 ? (
                <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
                  Waiting for the next call session
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={`${message.timestamp}-${index}`}
                    className={`flex ${message.speaker === "USER" ? "justify-end" : "justify-start"}`}
                  >
                    <div className="max-w-[82%] rounded-md border bg-background px-3 py-2 text-sm">
                      <div className="mb-1 text-[11px] font-medium text-muted-foreground">
                        {message.speaker}
                        {message.question_index ? ` Q${message.question_index}` : ""}
                      </div>
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="rounded-md border p-3">
              <div className="mb-2 text-xs font-medium text-muted-foreground">
                Current Question
              </div>
              <div className="text-sm">{currentQuestion?.content || "No active question"}</div>
            </div>

            <form
              className="flex gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                if (answer.trim() && snapshot) answerMutation.mutate();
              }}
            >
              <Input
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                disabled={!snapshot || snapshot.conversation_status === "completed"}
                placeholder="Caller answer"
              />
              <Button
                type="submit"
                disabled={!answer.trim() || !snapshot || answerMutation.isPending}
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4" />
            Call Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {events.length === 0 ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                Waiting for ADB call-state events
              </div>
            ) : (
              events.map((event, index) => (
                <div
                  key={`${event.timestamp}-${index}`}
                  className="grid gap-2 rounded-md border p-3 text-sm md:grid-cols-[150px_1fr_170px]"
                >
                  <div>{eventBadge(event.event_type)}</div>
                  <div className="min-w-0">
                    <div className="truncate font-medium">
                      {event.caller_name || event.caller_number || event.event_type}
                    </div>
                    <div className="font-mono text-xs text-muted-foreground">
                      {event.caller_number || event.serial || "No number"}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground md:text-right">
                    {formatDate(event.timestamp)}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
