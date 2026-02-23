/**
 * Reading training result - Korean Markdown content
 */
export interface ReadingResult {
  content: string;
}

/**
 * Grammar analysis result - Korean Markdown content
 */
export interface GrammarResult {
  content: string;
}

/**
 * Individual vocabulary word with Korean etymology explanation
 */
export interface VocabularyWordEntry {
  word: string;
  content: string;
}

/**
 * Vocabulary etymology result
 */
export interface VocabularyResult {
  words: VocabularyWordEntry[];
}

/**
 * Complete analysis response from the backend
 */
export interface AnalyzeResponse {
  reading: ReadingResult | null;
  grammar: GrammarResult | null;
  vocabulary: VocabularyResult | null;
  sessionId: string;
}
