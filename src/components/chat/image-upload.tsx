import React, { useState, useRef, DragEvent, ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { DEFAULT_SETTINGS } from "@/lib/constants";

const MAX_FILE_SIZE = DEFAULT_SETTINGS.maxFileSize; // 10MB

interface ImageUploadProps {
  onFileSelect: (file: File) => void;
  className?: string;
  /** Variant: "default" shows drag & drop, "camera-buttons" shows camera + gallery buttons */
  variant?: "default" | "camera-buttons";
  /** When true, shows a camera capture button (uses device camera) */
  enableCapture?: boolean;
}

/**
 * Image upload component with drag & drop support
 *
 * Variants:
 * - default: Drag & drop area with select button
 * - camera-buttons: Two buttons for camera capture and gallery selection (mobile-friendly)
 */
export function ImageUpload({
  onFileSelect,
  className,
  variant = "default",
  enableCapture = false,
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`);
      return;
    }

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.error("Only image files are allowed");
      return;
    }

    // Create preview
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);

    // Notify parent
    onFileSelect(file);
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    e.target.value = "";
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleButtonClick = () => {
    inputRef.current?.click();
  };

  const handleCameraClick = () => {
    cameraInputRef.current?.click();
  };

  // Camera-buttons variant: mobile-friendly camera + gallery buttons
  if (variant === "camera-buttons") {
    return (
      <div className={cn("space-y-3", className)}>
        {/* Hidden input for gallery selection */}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          className="hidden"
          data-testid="gallery-input"
        />

        {/* Hidden input for camera capture */}
        {enableCapture && (
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleInputChange}
            className="hidden"
            data-testid="camera-input"
          />
        )}

        {/* Image preview */}
        {preview && (
          <div className="relative">
            <img
              src={preview}
              alt="Preview"
              className="w-full h-auto rounded-md max-h-[200px] object-contain border"
            />
          </div>
        )}

        {/* Camera buttons */}
        <div className="flex gap-2">
          {enableCapture && (
            <Button
              onClick={handleCameraClick}
              variant="default"
              className="flex-1 gap-2"
              aria-label="카메라로 사진 촬영"
            >
              {/* Camera icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
                <circle cx="12" cy="13" r="3" />
              </svg>
              카메라 촬영
            </Button>
          )}

          <Button
            onClick={handleButtonClick}
            variant="outline"
            className="flex-1 gap-2"
            aria-label="갤러리에서 사진 선택"
          >
            {/* Gallery/image icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
              <circle cx="9" cy="9" r="2" />
              <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
            사진 선택
          </Button>
        </div>
      </div>
    );
  }

  // Default variant: drag & drop area
  return (
    <div
      data-testid="drop-zone"
      className={cn(
        "relative border-2 border-dashed rounded-lg p-4 transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border",
        className
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleInputChange}
        className="hidden"
        data-testid="file-input"
      />

      {preview ? (
        <div className="space-y-2">
          <img
            src={preview}
            alt="Preview"
            className="w-full h-auto rounded-md max-h-[300px] object-contain"
          />
          <Button onClick={handleButtonClick} variant="outline" className="w-full">
            Choose Different Image
          </Button>
        </div>
      ) : (
        <div className="text-center space-y-2">
          <Button onClick={handleButtonClick} variant="outline" className="w-full">
            Select Image
          </Button>
          <p className="text-xs text-muted-foreground">
            or drag and drop
          </p>
          <p className="text-xs text-muted-foreground">
            Max {MAX_FILE_SIZE / 1024 / 1024}MB
          </p>
        </div>
      )}
    </div>
  );
}
