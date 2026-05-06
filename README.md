# Photo Manager for Blender (Asset Browser)

This addon turns the Blender Asset Browser into a powerful photography and texture manager. 

---

## Main Features

- **Batch Import:** Load entire folders of images and automatically turn them into ready-to-use Material Assets.
- **Advanced Viewer:** Select multiple assets and open them in a dedicated window. Navigate with arrows (← →) and use the built-in Slideshow.
- **Template Rename:** Build complex filenames using tags like `<NAME>`, `<DATE>`, `<TIME>`, and `#` for numbering. Includes text cleaning tools (Find/Replace, Snake_case, etc.).
- **Physical Editing:** Rotate, flip, or resize images directly on disk. Features a sync system to read original pixel dimensions.
- **Organization:** Batch add or remove tags to multiple assets at once.
- **Export & Convert:** Export selected assets and convert them to different formats (PNG, JPEG, etc.).

### Installation
1. Save the files into a folder named `photo_manager`.
2. Zip the folder or copy it into your Blender addons directory.
3. Enable "Photo Manager" in Blender Preferences.
4. Open the **Asset Browser** and press **N** to reveal the sidebar panel.

---

## Technical Notes
- **Version:** 1.15
- **Blender Compatibility:** 3.0 or higher.
- **Stability:** Includes "Nuclear Reset" logic to fix broken image datablocks and lazy cache issues.