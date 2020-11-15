package ADNConfig;

use Exporter;
@ISA = qw(Exporter);

@EXPORT = qw(%CONFIG);

## ----------------------------------------
## VARS list
## ----------------------------------------
use vars qw(%CONFIG);

%CONFIG =
(
    'Quality'           => 85,
    'ThumbY'            => 250,
    'ThumbX'            => 200,
    #'DetailMaxDimension'=> 820,
    'MaxDimension'      => 1200,
    'ImageDestDir'      => '/Users/justin/Code/adnostalgia/static/images/gallery'
);

1;
