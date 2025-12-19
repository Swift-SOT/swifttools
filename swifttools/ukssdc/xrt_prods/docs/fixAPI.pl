#!/usr/bin/env perl
use Getopt::Std;
use strict;

our %modFn;
our %classDef;
our %classFn;
our %classVar;
our $constructor = undef;
# our @writeFn     = qw(removeAstromPos getJSONDict setLightCurvePars addAstromPos setProductPars getAstromPosPars removeLightCurvePar
#   getLightCurvePars removeStandardPos getAllPars addLightCurve removeAstromPosPar setImagePars getJSON
#   checkProductStatus setEnhancedPosPars removeSpectrumPar addProduct setFromJSON isValid removeEnhancedPosPar
#   addSpectrum countActiveJobs getEnhancedPosPars removeProduct removeEnhancedPos addImage removeLightCurve
#   setStandardPosPars getProduct getStandardPosPars removeImagePar copyOldJob removeProductPar cancelProducts
#   setSpectrumPars removeStandardPosPar getImagePars setGlobalPars addStandardPos addEnhancedPos copyProd
#   getProductPars setAstromPosPars listOldJobs hasProd downloadProducts getGlobalPars removeImage submit
#   getSpectrumPars removeSpectrum);


sub usage()
{
  print STDERR <<EOF;

  Usage fixAPI.pl [OPTIONS] infile outfile

  OPTIONS
  =======

    -h            Show this help
    -c            Clobber - overwrite output file.
    -l            List classes to stout.

EOF
  exit(1);
}

sub saveSection($$)
{
  my ( $what, $op ) = @_;
  my $id = $what;
  $id =~ s/^#+ //;

  # Do some cleaning up.
  # Need to make lists render properly, i.e. no blank lines between list elements,
  #  otherwise PHP makes it stupid.
  # Ensure that my parameters etc appear as definition lists.
  # Do not want things appearing as preformat blocks, so lose all leading whitespace.

  my @op=split(/\n/, $op);
  # First lose the whitesapce, can do that in bulk
  @op = map {s/^\s+//g; s/</&lt;/g; $_} @op;
  push @op, "";
  # Now remove gaps in lists.
  my @newOp=();
  push @newOp, $op[0];
  my $inList=0;
  my $lastBlank=0;
  my $inPar=0;
  for ( my $ix = 1 ; $ix < scalar(@op)-1 ; $ix++ )
  {
    my $line=$op[$ix];

    # If the line starts with a single asterisc, then it is a list:
    if ($line=~/^\*[^*]/)
    {
      # If it is parameter/return/raise then we need to lose the leading *
      if ($line =~/Parameters/ or $line=~/Retur/ or $line=~/Raises/)
      {
        $line =~s/^\*\s*//g;
        if ($inList) # List has ended so needs a blank line.
        {
          $lastBlank=0; # Force a blank line before this.
        }
        $inList=0;
        $inPar=1;
      }
      elsif ($inPar)
      {
        $line =~s/^\*\s*//g;
        my @tmp=split(/\s*–\s*/, $line);
        push @newOp, $tmp[0];
        $line = ": $tmp[1]";

      }
      # OK, not in the paramter / return etc regime
      else
      {
        $inList=1;
      }
      if ($lastBlank==0) # Put a space before the list
      {
        push @newOp, "";
      }

      $lastBlank=0;

    }
    elsif ($line!~/./) # Blank line
    {
      $lastBlank=1;
      if ($inList or $op[$ix+1]=~/^:/)
      {
        # If we are in a list we don't write blank lines
        next;
      }
    }
    elsif ($inPar)
    {

      # Par may be a list, but I don't want it to be any more, so lose it:
      $line=~s/^\*\s+//;
      # May read "None"
      if ($line=~/\*None\*/)
      {
        $line = "No parameters";
      }
      else
      {
        # The line is of the form **parName** (*type*) - definition
        # I want to output:
        # **parName** (*type*)
        # : definition
        if ($line=~/^\*/)
        {
          my @tmp=split(/\s*–\s*/, $line);
          push @newOp, $tmp[0];
          $line = ": $tmp[1]";
        }
        elsif ($lastBlank==1)
        {
          $line=": $line";
        }
      }
      $lastBlank=0;
    }
    # Not a blank line AND doesn't start with an asterisc,
    elsif ($inList and $lastBlank) # End of the list
    {
      $lastBlank=0;
      $inList=0;
      # Put a blank line after the list
      push @newOp, "";
    }

    else
    {
      $lastBlank=0;
    }
    # Otherwise either we were not in a list, in which case save the line; or it's a continuation of the
    # list, in which case also keep it.
    push @newOp, $line;
  }
  push @newOp, $op[-1];
  $op = join ("\n", @newOp);







  # $/ = "";
  # $op =~ s/\n([^\n*\s])/ $1/g;
  # $op =~ s/\n\n(\s*)\*\s/$1* /g;
  # $op =~ s/ +/ /g;
  # $op =~ s/\* \*\*Parameters\*\*/\n**Parameters**/g;
  # $op =~ s/\* \*\*Returns\*\*\s*\n*/**Returns:** /g;
  # $op =~ s/\* \*\*Return type\*\*\s*\n*/**Return type:** /g;
  # $op =~ s/\* \*\*Raises\*\*/**Raises**/g;
  # $op =~ s/\*\*None\*\* – /None/g;

  # # $/ = "\n";

  # my @op = split( /\n/, $op );
  # my @newOp=();
  # push @newOp, $op[0];
  # for ( my $ix = 1 ; $ix < scalar(@op) ; $ix++ )
  # {
  #   $op[$ix] =~ s/^\s+//;
  #   unless ($op[$ix]=~/Parameters/ or $op[$ix]=~/Retur/ or $op[$ix]=~/Raises/)
  #   {
  #     $op[$ix] =~ s/^\*\*/* **/;
  #   }

  #   if ( $op[$ix] =~ /^\s*\* / and ( $op[ $ix - 1 ] !~ /^\n*\s*\* / ) and ( $op[ $ix - 1 ] =~/\w/ ))
  #   {
  #     $op[$ix] = "\n$op[$ix]";
  #   }
  #   if ( $op[$ix] =~ /^\*Para/ and $op[ $ix - 1 ] =~ /./ )
  #   {
  #     $op[$ix] = "\n$op[$ix]";
  #   }



  #   push @newOp, $op[$ix];
  # }
  # $op = join( "\n", @newOp );



  ## MODULE FUNCTION
  if ( $what =~ /^### xrt_/ )
  {
    $modFn{$id} = $op;
  }
  ## CLASS DEFINITION
  elsif ( $what =~ /^### class/ )
  {
    $classDef{$id} = $op;
  }
  ## CLASS VARIABLE
  elsif ( $what =~ /^#### property/ )
  {
    $id =~ s/property //;
    $id =~ s/[()]//g;
    $classVar{$id} = $op;
  }
  ## CONSTRUCTOR
  elsif ( $id =~ /__init__/ )
  {
    $constructor = $op;
  }
  ## CLASS FUNCTION
  else
  {
    my $def=$id;
    $def=~s/\\\*/*/g;
    $id =~ s/xrt_prods\.//;
    $id =~ s/\(.+//;

    $op="**Definition:** `$def`\n\n$op";

    $classFn{$id} = $op;
  }

}


##########
## MAIN ##
##########

my %opts;
getopts( 'chl', \%opts );

usage() if ( $opts{h} );

my ( $infile, $outfile ) = @ARGV;
usage() unless ($outfile);

unless ( -r $infile )
{
  die "Cannot find $infile\n";
}

if ( -r $outfile and not $opts{c} )
{
  die "$outfile exists and -c not set\n";
}


######## READ INFILE #########

open( my $IN, "<", $infile ) or die "Can't open $infile\n\n";
my $in   = 0;
my $op   = "";
my $what = undef;
while (<$IN>)
{
  if (/^####*\s*.+$/ and not /Brief/)
  {
    if ($in)
    {
      saveSection( $what, $op );
    }
    $op   = "";
    $what = $_;
    chomp($what);
    $in = 1;
  }
  else
  {
    next if (/^#/);
    next unless ($in);
    $op .= $_;
  }
}
saveSection( $what, $op );
close($IN);


# ####### PREPARE CONTENTS ########
# my @classFns = keys %classFn;

# my $cts = "";

# if ( $opts{l} )
# {
#   foreach my $cfn (@classFns)
#   {
#     #$cfn =~ s/xrt_prods\.//;
#     #$cfn =~ s/\(.+//;
#     print "$cfn ";
#   }
#   print "\n\n";
# }
# else
# {
#   foreach my $cfn (@writeFn)
#   {
#     $cfn =~ s/xrt_prods\.//;
#     $cfn =~ s/\(.+//;
#     next;
#     #next unless ( $writeFn{$cfn} );
#     $cts .= "    * [$cfn()](#$cfn)\n";
#   }
# }
# print "\n\n" if ( $opts{l} );





####### WRITE OUTPUT #########


# OK, here goes:
open( my $OUT, ">", $outfile ) or die "Can't open $outfile for writing\n\n";

print $OUT <<EOF;
# Full API description

Here we give the full description of the ``xrt_prods`` module, describing all public functions
and variables. Following Python convention, functions or variables intended only for internal
use within the class (i.e. those which we would declare as ``private`` in C++) have names which
begin with a single underscore character. These are not described below.

## Contents

* [Module-level functions](#module-level-functions)
  * [countActiveJobs()](#countactivejobs)
  * [listOldJobs()](#listoldjobs)
* [The XRTProductRequest class](#the-xrtproductrequest-class)
  * [Methods](#xrtproductrequest-methods)
  * [Variables](#xrtproductrequest-variables)

---

## Module level functions

EOF

my $done = 0;
foreach my $fn ( sort keys %modFn )
{
  print $OUT "<hr style='border: 1px solid #555; margin: 10px auto;' />\n\n" if ( $done > 0 );
  my $def = $fn;
  $fn =~ s/xrt_prods\.//;
  $fn =~ s/\(.+//;
  $fn = "`$fn()`";
  print $OUT <<EOF;

### $fn

**Definition:** `$def`

$modFn{$def}

EOF
  $done++;
}

print $OUT <<EOF;

---

## The XRTProductRequest class

EOF

my ($def) = keys %classDef;
my $classDef = $classDef{def};
$def =~ s/^\s*class\s*//;

print $OUT <<EOF;
**Definition:** `$def`

$classDef

---

### XRTProductRequest Methods

EOF

$done = 0;
foreach my $fn ( sort keys %classFn )
{
  my $def=$fn;
  print $OUT "<hr style='border: 1px solid #555; margin: 10px auto;' />\n\n" if ( $done > 0 );
  $fn = "`$fn()`";
  print $OUT <<EOF;

### $fn

$classFn{$def}

EOF
  $done++;
}

print $OUT <<EOF;

---

### XRTProductRequest Variables

EOF

$done = 0;
foreach my $fn ( sort keys %classVar )
{
  #print $OUT "<hr style='border: 1px solid #555; margin: 10px auto;' />\n\n" if ( $done > 0 );
  my $def = $fn;
  $fn =~ s/xrt_prods\.//;
  $fn = "`$fn`";
  print $OUT <<EOF;

### $fn

$classVar{$def}

EOF
  $done++;
}
close($OUT);

print "Written $outfile\n\n";
