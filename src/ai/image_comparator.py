# src/ai/image_comparator.py

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ChangeRegion:
    """Represents a region where change was detected."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    zone: str
    change_type: str  # 'addition' or 'removal'


class ImageComparator:
    """
    Compares before/after images to detect changes in fridge inventory.
    Uses computer vision techniques to identify regions of interest.
    """

    def __init__(
        self,
        diff_threshold: int = 30,
        min_contour_area: int = 500,
        blur_kernel_size: int = 21
    ):
        """
        Initialize image comparator.

        Args:
            diff_threshold: Threshold for pixel difference (0-255)
            min_contour_area: Minimum area for detected changes (pixels)
            blur_kernel_size: Gaussian blur kernel size (reduces noise)
        """
        self.diff_threshold = diff_threshold
        self.min_contour_area = min_contour_area
        self.blur_kernel_size = blur_kernel_size

        print("🔍 Image Comparator initialized")

    def compare_images(
        self,
        before_image: np.ndarray,
        after_image: np.ndarray,
        zone: str = "unknown"
    ) -> Tuple[List[ChangeRegion], np.ndarray]:
        """
        Compare two images and detect regions of change.

        Args:
            before_image: Image captured before door closed
            after_image: Image captured after door closed
            zone: Camera zone name for context

        Returns:
            Tuple of (list of ChangeRegions, visualization image)
        """
        if before_image.shape != after_image.shape:
            print(f"⚠️  Image size mismatch in zone {zone}, resizing...")
            height, width = before_image.shape[:2]
            after_image = cv2.resize(after_image, (width, height))

        # Convert to grayscale
        gray_before = cv2.cvtColor(before_image, cv2.COLOR_BGR2GRAY)
        gray_after = cv2.cvtColor(after_image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blur_before = cv2.GaussianBlur(
            gray_before,
            (self.blur_kernel_size, self.blur_kernel_size),
            0
        )
        blur_after = cv2.GaussianBlur(
            gray_after,
            (self.blur_kernel_size, self.blur_kernel_size),
            0
        )

        # Compute absolute difference
        diff = cv2.absdiff(blur_before, blur_after)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(
            diff,
            self.diff_threshold,
            255,
            cv2.THRESH_BINARY
        )

        # Morphological operations to clean up noise
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Find contours of changed regions
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract change regions
        changes = []
        visualization = after_image.copy()

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.min_contour_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # Determine if addition or removal by comparing brightness
            before_roi = gray_before[y:y+h, x:x+w]
            after_roi = gray_after[y:y+h, x:x+w]

            before_brightness = np.mean(before_roi)
            after_brightness = np.mean(after_roi)

            change_type = "addition" if after_brightness > before_brightness else "removal"

            # Calculate confidence based on change magnitude
            brightness_diff = abs(after_brightness - before_brightness)
            confidence = min(brightness_diff / 255.0, 1.0)

            change = ChangeRegion(
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                zone=zone,
                change_type=change_type
            )

            changes.append(change)

            # Draw on visualization
            color = (0, 255, 0) if change_type == "addition" else (0, 0, 255)
            cv2.rectangle(visualization, (x, y), (x+w, y+h), color, 2)
            label = f"{change_type} ({confidence*100:.0f}%)"
            cv2.putText(
                visualization,
                label,
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        print(f"🔍 Detected {len(changes)} changes in zone {zone}")
        return changes, visualization

    def compare_all_zones(
        self,
        before_images: Dict[str, np.ndarray],
        after_images: Dict[str, np.ndarray]
    ) -> Dict[str, Tuple[List[ChangeRegion], np.ndarray]]:
        """
        Compare before/after images from all camera zones.

        Args:
            before_images: Dict mapping zone names to before images
            after_images: Dict mapping zone names to after images

        Returns:
            Dict mapping zone names to (changes, visualization)
        """
        results = {}

        for zone in before_images.keys():
            if zone not in after_images:
                print(f"⚠️  Missing after image for zone: {zone}")
                continue

            changes, viz = self.compare_images(
                before_images[zone],
                after_images[zone],
                zone
            )

            results[zone] = (changes, viz)

        total_changes = sum(len(changes) for changes, _ in results.values())
        print(f"🔍 Total changes detected across all zones: {total_changes}")

        return results

    def filter_significant_changes(
        self,
        changes: List[ChangeRegion],
        min_confidence: float = 0.5
    ) -> List[ChangeRegion]:
        """
        Filter changes by confidence threshold.

        Args:
            changes: List of detected changes
            min_confidence: Minimum confidence (0.0 - 1.0)

        Returns:
            Filtered list of changes
        """
        filtered = [c for c in changes if c.confidence >= min_confidence]
        print(f"🔍 Filtered {len(filtered)}/{len(changes)} significant changes")
        return filtered

    def merge_overlapping_regions(
        self,
        changes: List[ChangeRegion],
        overlap_threshold: float = 0.5
    ) -> List[ChangeRegion]:
        """
        Merge overlapping change regions from different zones.

        Args:
            changes: List of changes from all zones
            overlap_threshold: Minimum overlap ratio to merge

        Returns:
            Merged list of changes
        """
        if not changes:
            return []

        # Sort by area (largest first)
        sorted_changes = sorted(
            changes,
            key=lambda c: c.width * c.height,
            reverse=True
        )

        merged = []

        for change in sorted_changes:
            should_merge = False

            for existing in merged:
                if self._calculate_overlap(change, existing) > overlap_threshold:
                    # Merge into existing
                    existing.confidence = max(existing.confidence, change.confidence)
                    should_merge = True
                    break

            if not should_merge:
                merged.append(change)

        print(f"🔍 Merged {len(changes)} changes into {len(merged)} regions")
        return merged

    def _calculate_overlap(self, region1: ChangeRegion, region2: ChangeRegion) -> float:
        """Calculate overlap ratio between two regions."""
        x1 = max(region1.x, region2.x)
        y1 = max(region1.y, region2.y)
        x2 = min(region1.x + region1.width, region2.x + region2.width)
        y2 = min(region1.y + region1.height, region2.y + region2.height)

        if x2 < x1 or y2 < y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = region1.width * region1.height
        area2 = region2.width * region2.height

        return intersection / min(area1, area2)

    def create_difference_heatmap(
        self,
        before_image: np.ndarray,
        after_image: np.ndarray
    ) -> np.ndarray:
        """
        Create a heatmap visualization of differences.

        Args:
            before_image: Before image
            after_image: After image

        Returns:
            Heatmap image
        """
        gray_before = cv2.cvtColor(before_image, cv2.COLOR_BGR2GRAY)
        gray_after = cv2.cvtColor(after_image, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray_before, gray_after)

        # Apply colormap
        heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)

        # Blend with original image
        blended = cv2.addWeighted(after_image, 0.6, heatmap, 0.4, 0)

        return blended
