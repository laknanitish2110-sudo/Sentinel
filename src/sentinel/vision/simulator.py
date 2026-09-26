"""
Mock Vision Simulator for Sentinel.
Simulates object detection (YOLO/pipe detection) over site photos without requiring heavyweight ML frameworks.
Generates structured bounding box telemetry and physical measurements.
"""
import uuid
from typing import Dict, Any, List, Optional


class MockVisionSimulator:
    """Simulates computer vision analysis over drone/site inspection photographs."""

    def analyze_site_photo(
        self,
        image_uri: str,
        detected_class: str = "installed_pipe",
        detected_length_meters: float = 180.0,
        staged_pipe_count: int = 22,
        confidence: float = 0.92,
        location: Optional[Dict[str, Any]] = None,
        exif_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulates running an object detection model over a site photograph.
        Returns a raw vision detection payload.
        """
        loc = location or {
            "latitude": 12.9720,
            "longitude": 77.5950,
            "address": "Ward 7 Trench Section B"
        }
        exif = exif_info or {
            "camera": "iPhone 14 Pro",
            "focal_length": "24mm",
            "iso": 100,
            "timestamp": "2026-09-18T09:15:00Z"
        }

        # Simulated bounding box telemetry
        bounding_boxes = [
            {
                "class": "installed_pipe",
                "confidence": confidence,
                "box": [120, 340, 580, 410],
                "measurement_meters": detected_length_meters
            },
            {
                "class": "staged_pipe_uninstalled",
                "confidence": 0.89,
                "box": [50, 60, 210, 180],
                "count": staged_pipe_count
            }
        ]

        observation_text = (
            f"Computer vision model (mock-yolov8-drainage-v1) detected {detected_length_meters:.1f} meters "
            f"of laid {detected_class} inside active trench, plus {staged_pipe_count} uninstalled pipes in staging yard."
        )

        return {
            "raw_image_uri": image_uri,
            "vision_model": "mock-yolov8-drainage-v1",
            "observation": observation_text,
            "primary_detected_value": detected_length_meters,
            "unit": "meters",
            "confidence": confidence,
            "location": loc,
            "exif": exif,
            "bounding_boxes": bounding_boxes,
            "staged_pipe_count": staged_pipe_count
        }
