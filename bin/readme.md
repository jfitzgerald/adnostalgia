# Build Site

Tell Hugo to build the site in docs/.

```bash
hugo -d docs/
```

# Convert Images

To resize smaller side to 100 if it is larger than 100 and preserve aspect ratio, use

```bash
convert image.jpg -resize "100^>" newimage.jpg
```

To resize larger side to 100 if it is larger than 100 and preserve aspect ratio, use

```bash
convert image.jpg -resize "100>" newimage.jpg
```
