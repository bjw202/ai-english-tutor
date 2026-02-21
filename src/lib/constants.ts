/**
 * API endpoint constants
 */
export const API_ENDPOINTS = {
  analyze: "/api/tutor/analyze",
  analyzeImage: "/api/tutor/analyze-image",
  chat: "/api/tutor/chat",
} as const;

/**
 * Comprehension level definitions
 */
export const LEVEL_DEFINITIONS = [
  {
    level: 1,
    label: "기초",
    description: "가장 쉬운 설명과 기본 단어만 사용",
  },
  {
    level: 2,
    label: "초급",
    description: "간단한 문장 구조와 일상 어휘 사용",
  },
  {
    level: 3,
    label: "중급",
    description: "표준적인 설명과 일반적인 어휘 사용",
  },
  {
    level: 4,
    label: "고급",
    description: "상세한 설명과 다양한 어휘 사용",
  },
  {
    level: 5,
    label: "심화",
    description: "전문적인 설명과 고급 어휘 사용",
  },
] as const;

/**
 * Default application settings
 */
export const DEFAULT_SETTINGS = {
  level: 3, // Default to intermediate
  maxFileSize: 10 * 1024 * 1024, // 10MB in bytes
} as const;

/**
 * Helper function to get level label by level number
 */
export function getLevelLabel(level: number): string {
  const levelDef = LEVEL_DEFINITIONS.find((l) => l.level === level);
  return levelDef?.label || LEVEL_DEFINITIONS[2].label; // Default to level 3
}
