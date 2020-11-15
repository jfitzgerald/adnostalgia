package ADNUtil;

use strict;
use File::Glob qw(:glob);
use ADNImage;
use ADNConfig;


sub GetThumbs {
	my (%args) = @_;
	return undef unless($args{dir} && $args{file});

	my $fileSet = sprintf("%s/%s_?_thumb.jpg", $args{dir}, $args{file});
	my @thumbFiles = bsd_glob($fileSet);

	my @thumbs = ();
	foreach my $tmp (@thumbFiles) {
		$tmp =~ s|^(.+)/([^/]+\.jpg)$|$2|;
		my $detail = $tmp;
		$detail =~ s/_thumb//;
		push @thumbs, {detail => $detail, thumb => $tmp};
	}

	return \@thumbs;
}

sub CreateImageThumb {
	my (%args) = @_;
	return undef unless($args{dir} && $args{file});

	my $src  = sprintf("%s/%s.jpg", $args{dir}, $args{file});
	my $dest = sprintf("%s/%s_thumb.jpg", $args{dir}, $args{file});

	my $img = new ADNImage(file => $src);
	$img->scale($CONFIG{'Thumb'}, $CONFIG{'Quality'});
	$img->save($dest);
	undef $img;

	return $dest;
}

# dest : /Dir/Path
# file : /Src/Dir/file.jpg
sub CreateImagesFor {
	my (%args) = @_;
	return undef unless($args{dest} && $args{file});

    # SCN_0054
	my $image = $args{file};
	$image =~ s|^(.+)/([^/]+)\.jpg$|$2|;

    # SCN_0054.jpg
	my $srcImage = $args{file};
	$srcImage =~ s|^(.+)/([^/]+\.jpg)$|$2|;

    # /Path/to/image
	my $srcDir = $args{file};
	$srcDir =~ s|^(.+)/([^/]+)\.jpg$|$1|;

	my @thumbs = ();

	my $dest = join('/', $args{dest}, $srcImage);

	my $img = new ADNImage(file => $args{file});
	$img->scale($CONFIG{'MaxDimension'}, $CONFIG{'Quality'});
	$img->save($dest);
	push @thumbs, $dest;

	# let's get the detail images
	my @details = bsd_glob(sprintf("%s/%s_?.jpg", $srcDir, $image));
	foreach my $srcDetail (@details) {
		my $dstDetail = $srcDetail;
		$dstDetail =~ s/$srcDir/$args{dest}/;

		my $imgDetail = new ADNImage(file => $srcDetail);
		$imgDetail->scale($CONFIG{'MaxDimension'}, $CONFIG{'Quality'});
		$imgDetail->save($dstDetail);

		push @thumbs, $dstDetail;
	}

	# make thumb nails
	foreach my $thumb (@thumbs) {
		my $dest = $thumb;
		$dest =~ s/\.jpg$/_thumb\.jpg/;
		my $imgThumb = new ADNImage(file => $thumb);
		$imgThumb->crop($CONFIG{'ThumbX'}, $CONFIG{'ThumbY'}, $CONFIG{'Quality'});
		$imgThumb->save($dest);
	}
}

sub GetImage {
	my (%args) = @_;
	return undef unless($args{dir} && $args{file});

	return sprintf("%s/%s.jpg", $args{dir}, $args{file});
}

sub StringToPath {
	my $string = shift;

	$string =~ s/\s+/_/g;
	$string =~ s/\W//g;

	return lc $string;
}

1;
