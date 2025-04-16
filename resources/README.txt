ICONS FOR SHIFTPLAN TO ICS CONVERTER
====================================

To customize the application icon for different platforms, place the following 
files in this directory:

1. For Windows: icon.ico
   - Recommended size: 256x256 pixels
   - Format: ICO file with multiple resolutions (16x16, 32x32, 48x48, 256x256)

2. For macOS: icon.icns
   - Use the macOS Icon Composer or iconutil to create
   - Should include multiple resolutions

3. For Linux: icon.png
   - Recommended size: 512x512 pixels
   - Format: PNG with transparency

CREATING ICONS
=============

Windows:
- You can use tools like GIMP, Photoshop, or online converters to create ICO files
- Make sure to include multiple resolutions in your ICO file

macOS:
- Create a set of PNG files with different resolutions
- Use iconutil to convert to ICNS format
- Example command:
  $ iconutil -c icns icon.iconset -o icon.icns

Linux:
- PNG format is standard
- Make sure it has transparency
- 512x512 pixel PNG works well

FREE ICON RESOURCES
==================
- https://icons8.com/
- https://www.flaticon.com/
- https://www.iconfinder.com/
- https://iconmonstr.com/ 