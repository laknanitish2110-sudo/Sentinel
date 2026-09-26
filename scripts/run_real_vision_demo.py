"""
SENTINEL Phase 3A.1 Demo — Real Pretrained Ultralytics YOLO Vision Inference.

Demonstrates genuine local YOLO model inference against a real JPEG image file,
passing raw detections through the perception-only VisionEvidenceAdapter
and Evidence Contract into SentinelDB.
"""
import os
import sys
from PIL import Image, ImageDraw

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.vision.yolo_detector import YOLODetector, ULTRALYTICS_AVAILABLE
from sentinel.vision.adapter import VisionEvidenceAdapter
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim


def main():
    print("===============================================================")
    print(" SENTINEL PHASE 3A.1 — REAL PRETRAINED YOLO VISION INFERENCE")
    print("===============================================================\n")

    # 1. Verify Ultralytics availability
    if not ULTRALYTICS_AVAILABLE:
        print("[ERROR] Ultralytics is not installed in the active environment!")
        sys.exit(1)

    print("[1] Environment check passed: Ultralytics module is available.")

    # 2. Generate a real test JPEG image
    demo_image_path = os.path.abspath("test_real_scene.jpg")
    img = Image.new("RGB", (640, 480), color=(200, 220, 240))
    draw = ImageDraw.Draw(img)
    # Draw simple shapes representing objects in scene
    draw.rectangle([100, 150, 300, 350], fill=(50, 100, 200), outline=(0, 0, 0))
    draw.ellipse([400, 100, 550, 250], fill=(220, 80, 50), outline=(0, 0, 0))
    img.save(demo_image_path, "JPEG")
    print(f"[2] Created real test image: {demo_image_path} (640x480 JPEG)")

    # 3. Instantiate YOLODetector with real pretrained model checkpoint
    model_checkpoint = "yolov8n.pt"
    print(f"[3] Loading pretrained Ultralytics YOLO checkpoint: {model_checkpoint}...")
    detector = YOLODetector(model_name=model_checkpoint, confidence_threshold=0.25)

    # 4. Run real inference
    print("[4] Executing real tensor inference on image...")
    raw_detection = detector.detect_image(
        image_path_or_uri=demo_image_path,
        location_override={
            "latitude": 12.9716,
            "longitude": 77.5946,
            "address": "Stormwater Drain Construction Site, Block B"
        }
    )

    print("\n--- RAW MODEL DETECTION PAYLOAD ---")
    print(f"Vision Model:    {raw_detection['vision_model']}")
    print(f"Inference Type:  {raw_detection['inference_type']}")
    print(f"Image Size:      {raw_detection['image_width']}x{raw_detection['image_height']}")
    print(f"Observation:     {raw_detection['observation']}")
    print(f"Confidence:      {raw_detection['confidence']}")
    print(f"Detections Count:{len(raw_detection['bounding_boxes'])}")
    for idx, box in enumerate(raw_detection['bounding_boxes'], 1):
        print(f"  Box {idx}: class='{box['class']}', conf={box['confidence']}, bbox={box['box']}")

    # 5. Initialize DB and save parent records for FK integrity
    db = SentinelDB()
    project = Project(
        id="proj_drainage_2026",
        code="PRJ-DRN-2026",
        name="Ward 7 Stormwater Drain Pipeline Construction",
        description="Drainage infrastructure project",
        sanctioned_amount=5000000.0,
        released_amount=2500000.0
    )
    db.save_project(project)

    claim = Claim(
        id="clm_drainage_sec3",
        project_id=project.id,
        claim_ref="CLM-DRAINAGE-003",
        claimed_by="Contractor Corp",
        claim_type="PHYSICAL_QUANTITY",
        description="Installed 400m RCC pipeline",
        claimed_value=400.0,
        unit="meters",
        claim_date="2026-09-15"
    )
    db.save_claim(claim)

    # 6. Pass detections through perception-only VisionEvidenceAdapter
    print("\n[5] Passing raw perception through VisionEvidenceAdapter...")
    adapter = VisionEvidenceAdapter(db=db)
    
    evidence_item = adapter.adapt_vision_payload(
        project_id=project.id,
        claim=claim,
        vision_payload=raw_detection,
        source_id="YOLOv8n-REAL-INFERENCE-001"
    )

    print("\n--- NORMALIZED SENTINEL EVIDENCE CONTRACT ---")
    print(f"Evidence ID:   {evidence_item.id}")
    print(f"Project ID:    {evidence_item.project_id}")
    print(f"Claim ID:      {evidence_item.claim_id}")
    print(f"Source Type:   {evidence_item.source_type}")
    print(f"Source ID:     {evidence_item.source_id}")
    print(f"Relationship:  {evidence_item.relationship} (PERCEPTION-ONLY INVARIANT ENFORCED)")
    print(f"Confidence:    {evidence_item.confidence}")
    print(f"Reliability:   {evidence_item.reliability}")
    print(f"Observation:   {evidence_item.observation}")

    # 7. Invariant Verification
    if evidence_item.relationship == "NEUTRAL":
        print("\n[SUCCESS] Invariant verified: Vision evidence relationship is strictly NEUTRAL!")
    else:
        print(f"\n[FAILURE] Perception invariant violated! Relationship is {evidence_item.relationship}")
        sys.exit(1)

    # Cleanup demo image file
    if os.path.exists(demo_image_path):
        os.remove(demo_image_path)

    print("\n===============================================================")
    print(" DEMO COMPLETE — REAL YOLO INFERENCE INTEGRATED SUCCESSFULLY")
    print("===============================================================")


if __name__ == "__main__":
    main()
