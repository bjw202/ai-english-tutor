import React, { useState, useRef, DragEvent, ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { DEFAULT_SETTINGS } from "@/lib/constants";

const MAX_FILE_SIZE = DEFAULT_SETTINGS.maxFileSize; // 10MB

interface ImageUploadProps {
  onFileSelect: (file: File) => void;
  className?: string;
}

/**
 * Image upload component with drag & drop support
 */
export function ImageUpload({ onFileSelect, className }: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

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
