#!/usr/bin/perl -w

use strict;
use ADNUtil;
use ADNConfig;

use Data::Dumper;

## example:
## perl resize_images.pl < imageList.txt > import_log
##

my $fileParam;

while($fileParam = <STDIN>) {
	chomp($fileParam);
	return undef if($fileParam !~ /\.jpg$/);

	ADNUtil::CreateImagesFor(dest => $CONFIG{'ImageDestDir'}, file => $fileParam);
}
