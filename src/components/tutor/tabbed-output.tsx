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
      <div className="p-6 text-center text-muted-foreground">
        Submit text or upload an image to see analysis results
      </div>
    );
  }

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className={className}>
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="reading">Reading</TabsTrigger>
        <TabsTrigger value="grammar">Grammar</TabsTrigger>
        <TabsTrigger value="vocabulary">Vocabulary</TabsTrigger>
      </TabsList>

      <TabsContent value="reading" className="mt-4">
        <ReadingPanel result={reading} />
      </TabsContent>

      <TabsContent value="grammar" className="mt-4">
        <GrammarPanel result={grammar} />
      </TabsContent>

      <TabsContent value="vocabulary" className="mt-4">
        <VocabularyPanel result={vocabulary} />
      </TabsContent>
    </Tabs>
  );
}
