#!/usr/bin/perl -w

use strict;
use ADNUtil;
use ADNConfig;

use Data::Dumper;

## Resizes scanned images to size suitable for web.
## Processes accompanying images (*_\d.jpg) and creates
## thumb nail images (*_thumb.jpg).

## example:
## perl import_ads.pl < imageList.txt > import_log
##
## For new images:
## perl import_ads.pl new/SCN_130.jpg
##

my $fileParam;

if($fileParam = $ARGV[0]) {
	importImage($fileParam);
}
else {
	while($fileParam = <STDIN>) {
		chomp($fileParam);
		importImage($fileParam);
	}
}


sub importImage {
	# pass in an HTML file, parse contents, import to DB
	my ($filePath) = @_;
	return undef if($filePath !~ /\.jpg$/);

	my $file = $filePath;
	$file =~ s|^(.+)/([^/]+\.jpg)$|$2|;

	my $imgNum = $filePath;
	$imgNum =~ s|^(.+)/([^/]+)\.jpg$|$2|;

	ADNUtil::CreateImagesFor(dest => $CONFIG{'ImageDestDir'}, file => $filePath);
}
