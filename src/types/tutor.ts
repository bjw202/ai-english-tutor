/**
 * Grammar issue type for individual grammar problems detected
 */
export interface GrammarIssue {
  issue: string;
  type: string;
  suggestion: string;
  position?: {
    start: number;
    end: number;
  };
}

/**
 * Reading comprehension analysis result
 */
export interface ReadingResult {
  summary: string;
  keyPoints: string[];
  comprehensionLevel: number; // 1-5
}

/**
 * Grammar analysis result
 */
export interface GrammarResult {
  issues: GrammarIssue[];
  overallScore: number; // 0-100
  suggestions: string[];
}

/**
 * Individual vocabulary word entry
 */
export interface VocabularyWord {
  word: string;
  definition: string;
  example: string;
  difficulty: "basic" | "intermediate" | "advanced";
}

/**
 * Vocabulary analysis result
 */
export interface VocabularyResult {
  words: VocabularyWord[];
  difficultyLevel: number; // 1-5
}

/**
 * Complete analysis response from the backend
 */
export interface AnalyzeResponse {
  reading: ReadingResult;
  grammar: GrammarResult;
  vocabulary: VocabularyResult;
  sessionId: string; // UUID format
}
