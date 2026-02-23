import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReadingPanel } from "./reading-panel";
import { GrammarPanel } from "./grammar-panel";
import { VocabularyPanel } from "./vocabulary-panel";
import type { ReadingResult, GrammarResult, VocabularyResult } from "@/types/tutor";

interface TabbedOutputProps {
  reading: ReadingResult | null;
  grammar: GrammarResult | null;
  vocabulary: VocabularyResult | null;
  className?: string;
}

/**
 * Tabbed output component for displaying analysis results
 */
export function TabbedOutput({
  reading,
  grammar,
  vocabulary,
  className,
}: TabbedOutputProps) {
  const [activeTab, setActiveTab] = useState("reading");

  const hasContent = reading || grammar || vocabulary;

  if (!hasContent) {
    return (
      <div className="p-6 text-center text-muted-foreground h-full flex items-center justify-center">
        텍스트를 입력하거나 이미지를 업로드하면 분석 결과가 여기에 표시됩니다
      </div>
    );
  }

  return (
    <div className={`h-full ${className || ""}`}>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
        <TabsList className="grid w-full grid-cols-3 flex-shrink-0">
          <TabsTrigger value="reading">독해</TabsTrigger>
          <TabsTrigger value="grammar">문법</TabsTrigger>
          <TabsTrigger value="vocabulary">어휘</TabsTrigger>
        </TabsList>

        <TabsContent value="reading" className="mt-4 flex-1 overflow-y-auto">
          <ReadingPanel result={reading} />
        </TabsContent>

        <TabsContent value="grammar" className="mt-4 flex-1 overflow-y-auto">
          <GrammarPanel result={grammar} />
        </TabsContent>

        <TabsContent value="vocabulary" className="mt-4 flex-1 overflow-y-auto">
          <VocabularyPanel result={vocabulary} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
