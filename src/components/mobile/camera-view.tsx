import React from "react";
import { ImageUpload } from "@/components/chat/image-upload";
import { LevelSlider } from "@/components/controls/level-slider";
import { ChatInput } from "@/components/chat/chat-input";

interface CameraViewProps {
  onImageSelect: (file: File) => void;
  onSendMessage: (text: string) => void;
  level: number;
  onLevelChange: (level: number) => void;
  levelLabel: string;
  isStreaming: boolean;
}

/**
 * Camera/upload tab content for mobile
 * Shows camera/gallery buttons, level slider, and text input
 */
export function CameraView({
  onImageSelect,
  onSendMessage,
  level,
  onLevelChange,
  levelLabel,
  isStreaming,
}: CameraViewProps) {
  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      {/* Image upload area with camera support */}
      <ImageUpload
        onFileSelect={onImageSelect}
        variant="camera-buttons"
        enableCapture={true}
        className="flex-shrink-0"
      />

      {/* Compact level slider */}
      <LevelSlider
        level={level}
        onChange={onLevelChange}
        levelLabel={levelLabel}
        variant="compact"
        className="flex-shrink-0"
      />

      {/* Text input area */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="border rounded-lg p-3 flex-1 min-h-[80px]">
          <ChatInput
            onSend={onSendMessage}
            disabled={isStreaming}
          />
        </div>
      </div>
    </div>
  );
}
