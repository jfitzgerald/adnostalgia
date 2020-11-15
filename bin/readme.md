# Build Site

Tell Hugo to build the site in docs/.

```bash
hugo -d docs/
```

Test the site in docs/

```
python -m SimpleHTTPServer
```

# ImageMagick

For compilers to find imagemagick@6 you may need to set:

```bash
-I/usr/local/Cellar/imagemagick6/6.9.11-29/include/ImageMagick-6
-I"/usr/include/ImageMagick-6"
-L/usr/local/Cellar -L/usr/local/Cellar/imagemagick6/6.9.11-29/lib
```  

This might require symlinks because `brew` installs version 6 of ImageMagick
in a directory named `imagemagic@6`, which the `cpan` installer can't parse.

# Convert Images

To resize smaller side to 100 if it is larger than 100 and preserve aspect ratio, use

```bash
convert image.jpg -resize "100^>" newimage.jpg
```

To resize larger side to 100 if it is larger than 100 and preserve aspect ratio, use

```bash
convert image.jpg -resize "100>" newimage.jpg
```

# Resize Images

To resize images

```bash
find /Path/to/images/*.jpg -print | perl resize_images.pl > log
```
