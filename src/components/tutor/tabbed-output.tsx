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
  /** Raw vocabulary content as fallback display */
  vocabularyRawContent?: string;
  className?: string;
}

/**
 * Tabbed output component for displaying analysis results
 */
export function TabbedOutput({
  reading,
  grammar,
  vocabulary,
  vocabularyRawContent,
  className,
}: TabbedOutputProps) {
  const [activeTab, setActiveTab] = useState("reading");

  const hasContent = reading || grammar || vocabulary || (vocabularyRawContent && vocabularyRawContent.length > 0);

  if (!hasContent) {
    return (
      <div className="p-6 text-center text-muted-foreground h-full flex items-center justify-center">
        Submit text or upload an image to see analysis results
      </div>
    );
  }

  return (
    <div className={`h-full ${className || ""}`}>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
        <TabsList className="grid w-full grid-cols-3 flex-shrink-0">
          <TabsTrigger value="reading">Reading</TabsTrigger>
          <TabsTrigger value="grammar">Grammar</TabsTrigger>
          <TabsTrigger value="vocabulary">Vocabulary</TabsTrigger>
        </TabsList>

        <TabsContent value="reading" className="mt-4 flex-1 overflow-y-auto">
          <ReadingPanel result={reading} />
        </TabsContent>

        <TabsContent value="grammar" className="mt-4 flex-1 overflow-y-auto">
          <GrammarPanel result={grammar} />
        </TabsContent>

        <TabsContent value="vocabulary" className="mt-4 flex-1 overflow-y-auto">
          <VocabularyPanel result={vocabulary} rawContent={vocabularyRawContent} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
