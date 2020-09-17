package ADNImage;

use strict;
use Image::Magick;

sub new
{
	my ($class, %args) = @_;
	my $self = {};
	bless $self, $class;

	if($args{file})
	{
		#print STDERR "loading file: $args{file}\n";
		$self->load($args{file});
	}

	return $self;
}

sub load
{
	my ($self, $file) = @_;

	my $err;
	if(-e $file)
	{
		$self->{img} = Image::Magick->new();
		$err = $self->{img}->Read($file);
		die $err if $err;
	}
	else
	{
		die "File does not exist: $file";
	}
}

sub crop
{
	my ($self, $xSide, $ySide, $quality) = @_;

	die "no image available" if(!$self->{img});

	$self->{img}->Set(quality => $quality);

	my($x, $y) = $self->{img}->Get('width', 'height');

	if (($x > $xSide) || ($y > $ySide))
	{
		my ($scaleFactor, $displayX, $displayY);

		# calculate dimensions of display image
		if ($x > $y)
		{
			# landscape
			$scaleFactor = $ySide / $y;
			$displayX = int($x * $scaleFactor);
			$displayY = $ySide;
		}
		else
		{
			# portrait
			$scaleFactor = $xSide / $x;
			$displayY = int($y * $scaleFactor);
			$displayX = $xSide;
		}

		my $err = $self->{img}->Scale(width => $displayX, height => $displayY);
		die "$err" if "$err";

		# shave excess to fit xSide,ySide
		my ($shaveX, $shaveY);
		if($displayX > $xSide)
		{
			$shaveX = int(($displayX - $xSide) / 2);
			$shaveY = 0;
		}
		elsif($displayY > $ySide)
		{
			$shaveY = int(($displayY - $ySide) / 2);
			$shaveX = 0;
		}
		else
		{
			return;
		}

		$err = $self->{img}->Shave(width => $shaveX, height => $shaveY);
		die "$err" if "$err";

	}
}

sub scale
{
	my ($self, $maxSide, $quality) = @_;

	die "no image available" if(!$self->{img});

	$self->{img}->Set(quality => $quality);

	my($xSize, $ySize) = $self->{img}->Get('width', 'height');

	if (($xSize > $maxSide) || ($ySize > $maxSide))
	{
		my ($scaleFactor, $displayX, $displayY);

		# calculate dimensions of display image
		if ($xSize > $ySize)
		{
			$scaleFactor = $maxSide / $xSize;
			$displayX = $maxSide;
			$displayY = int($ySize * $scaleFactor);
		}
		else
		{
			$scaleFactor = $maxSide / $ySize;
			$displayY = $maxSide;
			$displayX = int($xSize * $scaleFactor);
		}

		my $err = $self->{img}->Scale(width => $displayX, height => $displayY);
		die "$err" if "$err";
	}
}


sub resize
{
	my ($self, $width, $height) = @_;

	die "no image available" if(!$self->{img});

	my $err;
	my $size = $width."x".$height;
	$err = $self->{img}->Resize(geometry => $size);

	return $err;
}

sub save
{
	my ($self, $dest) = @_;

	die "no image available" if(!$self->{img});

	my $err;
	$err = $self->{img}->Write($dest);
	return $err;
}

## other functions
##
## $x = $image->Crop(geometry => '690x354+54+130');

1;
