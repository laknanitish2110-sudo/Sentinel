# Genuinely Sourced Construction Site Evaluation Dataset Provenance

This directory (`data/vision_eval_real/`) contains genuinely sourced, un-manipulated real-world construction and infrastructure site photographs for evaluating Sentinel's vision perception layer.

> [!IMPORTANT]
> All images in this directory are real-world photographs sourced from Wikimedia Commons with authentic provenance and explicit individual licenses.
> NO synthetic images, PIL drawings, or AI-generated visual media are contained in this evaluation set.

---

## Provenance Manifest

### 1. `real_eval_01_concrete_pump_truck.jpg`
- **Filename**: `real_eval_01_concrete_pump_truck.jpg`
- **Source**: Wikimedia Commons
- **Canonical Page**: `https://commons.wikimedia.org/wiki/File:Construction_site_with_concrete_pump_truck.JPG`
- **Direct Image URL**: `https://upload.wikimedia.org/wikipedia/commons/4/4c/Construction_site_with_concrete_pump_truck.JPG`
- **Author / Artist**: Steve Pivnick, U.S. Air Force
- **License**: Public Domain (U.S. Air Force work)
- **Attribution Requirement**: None required (Public Domain)
- **Capture Date**: 2011-06-22
- **Resolution**: 1800 x 1219 pixels
- **GPS Metadata**: No (EXIF header present, GPS tags absent)
- **Timestamp Metadata**: Yes (EXIF timestamp header present)
- **Visual Description**: Active construction site with concrete pump boom truck, concrete mixer, ground workers, formwork, and surrounding scaffolding.
- **Limitations**: Medium resolution photo taken at distance; workers appear as small bounding boxes.

### 2. `real_eval_02_construction_works_osaka.jpg`
- **Filename**: `real_eval_02_construction_works_osaka.jpg`
- **Source**: Wikimedia Commons
- **Canonical Page**: `https://commons.wikimedia.org/wiki/File:Construction_works_Japan,_Osaka.jpg`
- **Direct Image URL**: `https://upload.wikimedia.org/wikipedia/commons/a/a6/Construction_works_Japan%2C_Osaka.jpg`
- **Author / Artist**: Editorq35
- **License**: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution Requirement**: Attribute to "Editorq35" under CC BY-SA 4.0 license
- **Capture Date**: 2019-10-14
- **Resolution**: 4032 x 3024 pixels
- **GPS Metadata**: No (EXIF header present, GPS tags absent)
- **Timestamp Metadata**: Yes (EXIF timestamp header present)
- **Visual Description**: Heavy urban infrastructure construction site in Osaka, Japan showing dump trucks, high-visibility vest personnel, soil/ground excavation, and safety barriers.
- **Limitations**: Shot from elevated viewpoint, causing partial occlusion of ground objects.

### 3. `real_eval_03_construction_labour_workers.jpg`
- **Filename**: `real_eval_03_construction_labour_workers.jpg`
- **Source**: Wikimedia Commons
- **Canonical Page**: `https://commons.wikimedia.org/wiki/File:House_Construction_Labour_Workers_1_-_Invermere,_British_Columbia.jpg`
- **Direct Image URL**: `https://upload.wikimedia.org/wikipedia/commons/3/33/House_Construction_Labour_Workers_1_-_Invermere%2C_British_Columbia.jpg`
- **Author / Artist**: PatInver (Uploader: Sebastian Wallroth)
- **License**: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
- **Attribution Requirement**: Attribute to "PatInver" under CC BY-SA 4.0 license
- **Capture Date**: 2018-08-04
- **Resolution**: 1667 x 999 pixels
- **GPS Metadata**: No (EXIF header present, GPS tags absent)
- **Timestamp Metadata**: Yes (EXIF timestamp header present)
- **Visual Description**: Field labour workers on residential timber framing site in Invermere, BC with construction pickup truck/flatbed vehicle.
- **Limitations**: Frame focused primarily on upper framing structure, ground trench/drainage features not in field of view.

---

## Dataset Guidelines

1. **Do NOT add synthetic images** to `data/vision_eval_real/`. Synthetic test images must remain in `data/vision_eval/` for deterministic unit test fixtures.
2. **Do NOT invent metadata**. Metadata fields indicate true EXIF header contents.
3. **Verify licensing before adding samples**. Document individual author, exact license (e.g., CC BY-SA 4.0, Public Domain), attribution terms, and canonical Wikimedia Commons URLs.
