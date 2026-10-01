# Build Site

Tell Hugo to build the site in docs/.

```bash
hugo -d docs/
```

Test the site in docs/

```
python -m SimpleHTTPServer
```

# Generate AI image notes

`generate_ad_notes.py` processes each primary ad image in a separate Codex CLI
run and stores the resulting text in the ad's `generated_note` field in
`data/ads.json`. The batch is resumable and writes the data file atomically
after every successful image.

Preview the batch without calling Codex:

```bash
python3 bin/generate_ad_notes.py --dry-run --limit 5
```

Once an analysis prompt has been added, generate notes with:

```bash
python3 bin/generate_ad_notes.py --prompt path/to/ad-note-prompt.md
```

Use `--include-details` to attach each ad's additional scans after the primary
image, `--only SCN_0152` to process one ad, or `--retry-failures` to retry only
failed records. Existing non-empty notes are skipped unless `--force` is used.

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
