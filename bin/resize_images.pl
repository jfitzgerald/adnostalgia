#!/opt/local/bin/perl -w

use strict;
use lib '../lib';
use ADN::Item::Advert;
use ADN::Util;
use ADN::Config;

use Data::Dumper;

## example:
## perl import_tabs.pl < imageList.txt > import_log
## 

my $fileParam;

while($fileParam = <STDIN>)
{
	chomp($fileParam);
	return undef if($fileParam !~ /\.jpg$/);

	ADN::Util::CreateImagesFor(dest => $CONFIG{'ImageDestDir'}, file => $fileParam);
}
