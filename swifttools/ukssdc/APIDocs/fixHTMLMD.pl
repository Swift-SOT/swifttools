#!/usr/bin/env perl
use strict;
use File::Basename;

my $infile = shift @ARGV;
my $outfile = shift @ARGV;

my $NB = basename($infile);
$NB=~s/md$/ipynb/;
print "$NB\n";

open (my $OUT, ">", $outfile);
open (my $IN, "<", $infile);
my $inDiv=0;
my $doneNB = 0;
while (<$IN>)
{
  chomp;
  s/ipynb/md/g;
  s/(\w+)_(\w+)\.md/$1\/$2.md/g;
  s/testtools/swifttools/g;
  if ($inDiv)
  {
    print $OUT "$_";
    if (m/\/div\>/)
    {
      $inDiv=0;
    }
  }
  else
  {
    if (/\<div[^>]*\>/)
    {
      $inDiv=1;
      print $OUT "<div style='width: 95%; max-height: 200px; overflow: scroll;'>";
    }
    else
    {
      print $OUT "$_\n";
    }
  }
  if (m/^# / and not $doneNB) # First line
  {
    print $OUT "\n[Jupyter notebook version of this page]($NB)\n";
    $doneNB=1;
  }
  
}




exit(0);
my $in=`cat $infile`;

$/="";
$in=~s/\>\s*\n\s*/>/g;
$/="\n";


print $OUT $in."\n";
close($OUT);
