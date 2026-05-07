# Photo Manager (Asset Browser) for Blender

**Photo Manager** is a powerful Blender add-on that transforms the built-in Asset Browser into an advanced photography, reference, and texture manager. 

Whether you are a 3D artist managing vast libraries of reference photos, or a texture artist organizing material assets, this tool provides a seamless workflow to batch import, rename, organize, edit, and export your images directly within Blender—without ever needing to open external image editing software.

## 🚀 Key Features

* **Batch Import:** Instantly load entire folders of images (`.png`, `.jpg`, `.jpeg`, `.tif`, `.bmp`) and automatically convert them into ready-to-use Material Assets with generated previews.
* **Advanced Viewer & Slideshow:** Select assets and open them in a dedicated, distraction-free Image Editor window. Features include a rock-solid "Shrink to Fit" auto-zoom, arrow-key navigation (← / →), and an automated slideshow with a customizable timer.
* **Smart Template Renaming:** Rename hundreds of assets at once using dynamic templates (e.g., `<NAME>_ref_<DATE>_#`). Features powerful cleanup tools: Find/Replace, character removal, and text-casing conversions (lowercase, UPPERCASE, Title Case, snake_case, camelCase, PascalCase).
* **Physical Image Editing:** Perform physical, non-destructive (until saved) edits directly to the image files on your disk using Blender's Python API and `numpy`. Flip horizontally/vertically, rotate CW/CCW, or batch resize images to specific dimensions.
* **Batch Organization:** Easily apply or clear tags across multiple selected assets simultaneously to keep your library neatly categorized.
* **Export & Convert:** Export selected assets to a specific folder and seamlessly convert them between formats (Original, PNG, JPEG).

## 📋 Requirements

* **Blender Version:** 3.0.0 or higher.
* **Dependencies:** Python's `numpy` module (comes pre-bundled with standard Blender installations).

## 🛠️ Installation

1. Click on `Code` > `Download ZIP` to download the repository.
2. Open Blender and navigate to **Edit** > **Preferences** > **Add-ons**.
3. Click the **Install...** button in the top right corner.
4. Locate and select the downloaded ZIP file, then click **Install Add-on**.
5. Enable the add-on by checking the box next to **System: Photo Manager (Asset Browser)**.
6. Open the **Asset Browser** in any Blender workspace and press the **N** key to reveal the Sidebar. You will find the **Photo Manager** tab there.

## 📖 How to Use

The add-on UI is divided into a logical step-by-step workflow:

### 1. Search and View
* Select one or more image assets.
* Click the **Full Screen (View)** icon to open the images in a dedicated viewer.
* Use the UI navigation arrows or run a **Slideshow** (adjust the delay in seconds using the provided slider).

### 2. Source Folder (Import)
* Pick a target folder from your hard drive.
* Click **Import** to automatically load all supported image files, wrap them in Material nodes, and mark them as assets with generated thumbnails.

### 3. Rename Assets
* **Template:** Use tags to construct new names:
  * `<NAME>`: The original file name.
  * `<DATA>`: Current Date (YYYYMMDD).
  * `<TIME>`: Current Time (HHMM).
  * `#`: Auto-incrementing numbers (e.g., `###` outputs `001, 002`).
* **Cleanup:** Find and replace text, or remove specific characters.
* **Format:** Change the text case (e.g., converting "my_image" to "MyImage" using PascalCase).
* Click the **Rename** button to apply changes to both the Material and the underlying Image data-block.

### 4. Organization
* Type comma-separated tags (e.g., `nature, reference, 4k`) in the text field.
* Click **+ (Apply Tags)** to add them to all selected assets, or the **Trash bin (Clear Tags)** to wipe existing tags.

### 5. Edit Image
* **Transform:** Flip Horizontally, Flip Vertically, Rotate Clockwise, or Rotate Counter-Clockwise. *(Note: This alters the pixel data directly).*
* **Resize:** Click the sync icon to fetch the original image dimensions. Enter new Width/Height values and click **Apply Resize** to permanently scale the images.

### 6. Export and Convert
* Select a destination directory.
* Choose your desired format (`ORIGINAL`, `PNG`, or `JPEG`).
* Click **Export Assets** to save copies of your assets out of Blender.

## 🧠 Technical Notes
* The add-on features a robust "Nuclear Reset" and lazy cache bypass logic to ensure that large images loaded into the viewer are displayed at the correct aspect ratio without stretching.
* Image transformations utilize `numpy` arrays for blazing-fast pixel manipulation directly in memory before writing back to disk.

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. 
See the [LICENSE](LICENSE) file for more details. 
You are free to use, modify, and distribute this software as long as you keep it open-source.

## ⚠️ Known Limitations

The following features are currently **not supported** due to technical constraints or Blender API limitations:

* **Advanced Color Correction:** No White Balance adjustment.
* **Cropping:** Manual image cropping is not available.
* **Overlays:** No support for adding watermarks or image overlays.
* **Retouching:** No Red Eye Removal or localized healing tools.
* **Geometric Correction:** No Perspective adjustment or fine Straightening/Tilt (only 90° rotations are supported).
* **Selection Persistence:** Due to current Blender Asset Browser API design, the selection is automatically cleared after performing operations on files.